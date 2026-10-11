import argparse
import logging
import os
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed, BrokenExecutor

import pandas as pd
from lxml import etree  # type: ignore
from tqdm import tqdm

from src.loader import (
    listar_zips,
    listar_xmls,
    salvar_xml_por_empresa,
    salvar_xml_nao_classificado,
    arquivar_zip_original,
    parser_xml_seguro,
)
from src.nfse_abrasf_parser import extrair_dados as extrair_nfse_abrasf
from src.nfse_parser import extrair_dados as extrair_nfse
from src.nfe_parser import extrair_dados as extrair_nfe
from src.cte_parser import extrair_dados as extrair_cte
from src.event_parser import extrair_cancelamento
from src.excel_gen import salvar_excel
from src.db import BancoFiscal
from src.processor import chave_valida
from src.conciliacao import conciliar_valores
from src.config import carregar_config

# ============================================================
# LOGGING
# ============================================================

def configurar_logging(pasta_log: Path, handlers_extra: list = None):
    pasta_log.mkdir(parents=True, exist_ok=True)
    nome_log = f"execucao_{datetime.now():%Y%m%d_%H%M%S}.log"
    handlers = [logging.FileHandler(pasta_log / nome_log, encoding="utf-8")]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    if handlers_extra:
        handlers.extend(handlers_extra)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )

logger = logging.getLogger(__name__)

# ============================================================
# CLASSIFICACAO DE DOCUMENTOS (por namespace)
# ============================================================

def _classificar(arvore):
    tag_raiz = arvore.tag.lower()
    if tag_raiz.startswith("{"):
        namespace, _, nome_local = tag_raiz[1:].partition("}")
    else:
        namespace, nome_local = "", tag_raiz

    if "procevento" in nome_local:
        return "CANCELAMENTO", extrair_cancelamento(arvore)
    if "portalfiscal.inf.br/cte" in namespace:
        return "CTe", extrair_cte(arvore)
    if "portalfiscal.inf.br/nfe" in namespace:
        return "NFe", extrair_nfe(arvore)
    if "abrasf.org.br" in namespace:
        return "NFSe_ABRASF", extrair_nfse_abrasf(arvore)
    if "sped.fazenda.gov.br/nfse" in namespace:
        return "NFSe", extrair_nfse(arvore)
    return "DESCONHECIDO", None

# ============================================================
# HELPERS
# ============================================================

def _empresa_do_documento(tipo: str, dados: dict) -> tuple:
    if not dados or not isinstance(dados, dict):
        return "", "_sem_empresa"
    if tipo == "NFe":
        cab = dados.get("cabecalho", dados)
        return cab.get("CNPJ Emitente", ""), cab.get("Razão Emitente", "_sem_razao")
    if tipo == "CTe":
        return dados.get("CNPJ Transportadora", ""), dados.get("Transportadora", "_sem_razao")
    if tipo in ("NFSe", "NFSe_ABRASF"):
        return dados.get("CNPJ/CPF Prestador", ""), dados.get("Razão Prestador", "_sem_razao")
    if tipo == "CANCELAMENTO":
        return dados.get("CNPJ Emitente", ""), "_cancelamentos"
    return "", "_sem_empresa"


def _processar_um_xml(conteudo: bytes, nome_xml: str, processados_dir: Path) -> tuple:
    try:
        arvore = etree.fromstring(conteudo, parser=parser_xml_seguro())
        tipo, dados = _classificar(arvore)
    except Exception as e:
        logger.exception(f"Falha ao parsear XML: {nome_xml}")
        salvar_xml_nao_classificado(conteudo, nome_xml, processados_dir)
        return "ERRO", f"{nome_xml}: {e}", nome_xml

    cnpj, razao = _empresa_do_documento(tipo, dados)
    if tipo in ("DESCONHECIDO", "ERRO") or dados is None or not cnpj:
        salvar_xml_nao_classificado(conteudo, nome_xml, processados_dir)
    else:
        salvar_xml_por_empresa(conteudo, nome_xml, cnpj, razao, processados_dir)

    return tipo, dados, nome_xml

# ============================================================
# WORKER — salva XMLs no disco e retorna APENAS dados parseados
# (sem bytes crus no retorno, evita estouro de memória no IPC)
# ============================================================

def trabalhador_zip(args):
    """
    Recebe (caminho_zip, processados_dir) como tupla.
    Parseia cada XML, salva o arquivo na pasta correta e
    retorna apenas os dicionários de dados (sem bytes).
    """
    caminho_zip, processados_dir = args
    processados_dir = Path(processados_dir)
    resultados = []

    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            nomes_xml = [n for n in z.namelist() if n.lower().endswith('.xml')]
            for nome_xml in nomes_xml:
                try:
                    conteudo = z.read(nome_xml)
                    resultados.append(_processar_um_xml(conteudo, nome_xml, processados_dir))
                except Exception as e:
                    logger.exception(f"Erro ao processar {nome_xml} em {caminho_zip.name}")
                    resultados.append(("ERRO", f"{nome_xml} em {caminho_zip.name}: {e}", nome_xml))

    except Exception as e:
        logger.exception(f"ZIP corrompido: {caminho_zip.name}")
        resultados.append(("ERRO", f"ZIP corrompido {caminho_zip.name}: {e}", ""))

    return resultados

# ============================================================
# CONSOLIDACAO NO BANCO
# ============================================================

def _consolidar_resultado(tipo, dados, nome_xml, origem: Path, banco):
    """Insere um resultado no banco. Não lida mais com bytes/arquivos."""

    if tipo == "ERRO":
        logger.error(dados)
        banco.inserir_erro(str(dados), origem.name)
        return

    if tipo == "DESCONHECIDO" or dados is None:
        logger.warning(f"XML nao classificado: {nome_xml}")
        banco.inserir_erro(f"Tipo desconhecido: {nome_xml}", origem.name)
        return

    if tipo == "NFe":
        cab = dados.get("cabecalho", {})
        chave = cab.get("Chave", "")
        if not chave:
            logger.error(f"NFe sem dados extraidos (estrutura de XML inesperada): {nome_xml}")
            banco.inserir_erro(f"NFe sem dados extraidos (estrutura de XML inesperada): {nome_xml}", origem.name)
            return
        if not chave_valida(chave):
            logger.warning(f"Chave NFe invalida: '{chave}' em {nome_xml}")
        banco.inserir_nfe(cab, dados.get("produtos", []))
    elif tipo == "CTe":
        banco.inserir_cte(dados)
    elif tipo == "CANCELAMENTO":
        banco.inserir_cancelamento(dados)
    elif tipo == "NFSe":
        banco.inserir_nfse(dados)
    elif tipo == "NFSe_ABRASF":
        banco.inserir_nfse_abrasf(dados)

# ============================================================
# PROCESSAMENTO EM LOTES (recria executor a cada lote)
# ============================================================

def processar_lote_zips(
    lote: list,
    num_cores: int,
    banco: BancoFiscal,
    processados_dir: Path,
    pbar,
):
    """
    Processa um lote de ZIPs criando um executor novo a cada chamada.
    Isso garante que um BrokenExecutor num lote não afete os próximos.
    """
    # Passa processados_dir junto com o caminho do ZIP (worker precisa)
    args_lote = [(z, str(processados_dir)) for z in lote]

    try:
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            futuros = {executor.submit(trabalhador_zip, args): args[0] for args in args_lote}

            for futuro in as_completed(futuros):
                caminho_zip = futuros[futuro]
                try:
                    for tipo, dados, nome_xml in futuro.result():
                        _consolidar_resultado(tipo, dados, nome_xml, caminho_zip, banco)

                    banco.commit()
                    arquivar_zip_original(caminho_zip, processados_dir)

                except BrokenExecutor:
                    raise

                except Exception as e:
                    logger.exception(f"Erro ao processar ZIP {caminho_zip.name}")
                    banco.inserir_erro(str(e), caminho_zip.name)
                    banco.commit()

                pbar.update(1)

    except BrokenExecutor as e:
        logger.error(
            f"Worker encerrado abruptamente: {e}\n"
            f"Dados processados ate aqui serao incluidos no relatorio."
        )
        banco.commit()

# ============================================================
# PIPELINE (reutilizado pela CLI e pela GUI)
# ============================================================

class NenhumArquivoEncontrado(Exception):
    pass


@dataclass
class ResultadoExecucao:
    caminho_excel: Path
    duplicadas: dict
    divergencias: pd.DataFrame
    total_zips: int
    total_xmls: int


class _BarraSilenciosa:
    def __init__(self, total, callback):
        self.total = total
        self.n = 0
        self._callback = callback

    def update(self, quantidade=1):
        self.n += quantidade
        self._callback(self.n, self.total)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _criar_barra(total, desc, unit, callback):
    if callback is None:
        return tqdm(total=total, desc=desc, unit=unit)
    return _BarraSilenciosa(total, callback)


def executar_pipeline(
    input_dir: Path,
    num_cores: int,
    tamanho_lote: int,
    tolerancia_conciliacao: float = 0.01,
    progresso_zip=None,
    progresso_xml=None,
    handlers_log_extra: list = None,
) -> ResultadoExecucao:
    output_dir = input_dir
    processados_dir = input_dir / "processados"
    logs_dir = input_dir / "logs"

    processados_dir.mkdir(exist_ok=True)
    configurar_logging(logs_dir, handlers_extra=handlers_log_extra)

    logger.info(f"Pasta de trabalho: {input_dir}")
    logger.info(f"Nucleos em uso: {num_cores}")

    lista_zips = listar_zips(input_dir)
    lista_xmls_soltos = listar_xmls(input_dir)

    logger.info(f"{len(lista_zips)} ZIP(s) encontrado(s).")
    logger.info(f"{len(lista_xmls_soltos)} XML(s) solto(s) encontrado(s).")

    if not lista_zips and not lista_xmls_soltos:
        raise NenhumArquivoEncontrado(str(input_dir))

    with BancoFiscal() as banco:

        if lista_zips:
            total_lotes = -(-len(lista_zips) // tamanho_lote)
            logger.info(
                f"Processando {len(lista_zips)} ZIP(s) em {total_lotes} lote(s) "
                f"de ate {tamanho_lote} ZIP(s) cada."
            )

            with _criar_barra(len(lista_zips), "Processando ZIPs", "zip", progresso_zip) as pbar:
                for i in range(0, len(lista_zips), tamanho_lote):
                    lote = lista_zips[i:i + tamanho_lote]
                    lote_num = (i // tamanho_lote) + 1
                    logger.info(
                        f"Lote {lote_num}/{total_lotes}: {len(lote)} ZIP(s) | "
                        f"ZIPs {i + 1}-{min(i + tamanho_lote, len(lista_zips))} de {len(lista_zips)}"
                    )
                    processar_lote_zips(lote, num_cores, banco, processados_dir, pbar)

        if lista_xmls_soltos:
            with _criar_barra(len(lista_xmls_soltos), "Processando XMLs", "xml", progresso_xml) as pbar:
                for caminho_xml in lista_xmls_soltos:
                    try:
                        conteudo = caminho_xml.read_bytes()
                        tipo, dados, nome_xml = _processar_um_xml(
                            conteudo, caminho_xml.name, processados_dir
                        )
                        _consolidar_resultado(tipo, dados, nome_xml, caminho_xml, banco)

                    except Exception as e:
                        logger.exception(f"Erro ao processar XML solto {caminho_xml.name}")
                        banco.inserir_erro(str(e), caminho_xml.name)

                    pbar.update(1)
                banco.commit()

        logger.info("Extracao concluida. Gerando relatorio Excel...")
        dados_para_excel = banco.gerar_dataframes()
        duplicadas = banco.resumo_duplicadas()

    divergencias = conciliar_valores(
        dados_para_excel["Mercadorias (NFe)"], dados_para_excel["Produtos"], tolerancia_conciliacao
    )
    dados_para_excel["Divergências"] = divergencias

    nome_excel = f"relatorio_notas_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    caminho_excel = output_dir / nome_excel
    salvar_excel(dados_para_excel, nome_arquivo=caminho_excel)

    return ResultadoExecucao(
        caminho_excel=caminho_excel,
        duplicadas=duplicadas,
        divergencias=divergencias,
        total_zips=len(lista_zips),
        total_xmls=len(lista_xmls_soltos),
    )

# ============================================================
# ENTRADA DO USUARIO
# ============================================================

def perguntar_pasta_xml() -> Path:
    while True:
        caminho = input("\nQual pasta contem os arquivos XML/ZIP? ").strip().strip('"')
        pasta = Path(caminho).expanduser().resolve()
        if pasta.is_dir():
            return pasta
        print(f"Pasta nao encontrada: {pasta}\nTente novamente.")


def limite_seguro_cores() -> int:
    total = os.cpu_count() or 4
    return max(1, total // 2)


def perguntar_num_cores() -> int:
    total = os.cpu_count() or 4
    max_seguro = limite_seguro_cores()
    print(f"\nHardware detectado: {total} nucleos.")
    print(f"Limite de seguranca sugerido: {max_seguro} nucleos.")
    print(f"(Metade dos nucleos fisicos para workload de I/O + parse)")
    try:
        escolha = int(input(f"Quantos nucleos deseja usar? (1 a {max_seguro}): "))
        return max(1, min(escolha, max_seguro))
    except ValueError:
        print(f"Entrada invalida - usando {max_seguro} nucleos.")
        return max_seguro


def perguntar_tamanho_lote(total_zips: int) -> int:
    print(f"\nTotal de ZIPs: {total_zips}")
    print("Lotes menores = menos RAM consumida simultaneamente.")
    try:
        entrada = input("Quantos ZIPs por lote? (recomendado: 5, Enter para usar 5): ").strip()
        lote = int(entrada) if entrada else 5
        return max(1, lote)
    except ValueError:
        return 5


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extrai dados de NFe/NFSe/CTe (XML) para uma planilha Excel. "
            "Sem argumentos, roda no modo interativo de sempre; passe "
            "--input para rodar via linha de comando/agendador (cron, "
            "Agendador de Tarefas etc.), sem prompts. Um config.yaml na "
            "pasta do projeto/executavel tambem pode fornecer os padroes."
        )
    )
    parser.add_argument(
        "--input", "-i", type=Path, default=None,
        help="Pasta com os arquivos XML/ZIP de entrada. Se informado, "
             "pula o prompt interativo de pasta.",
    )
    parser.add_argument(
        "--cores", "-c", type=int, default=None,
        help=f"Nucleos de CPU a usar (padrao: metade dos nucleos disponiveis, "
             f"ate {limite_seguro_cores()} nesta maquina).",
    )
    parser.add_argument(
        "--batch-size", "-b", type=int, default=None,
        help="Quantidade de ZIPs por lote (padrao: 5).",
    )
    parser.add_argument(
        "--tolerancia", "-t", type=float, default=None,
        help="Tolerancia em R$ para a conciliacao entre o total da NFe e a "
             "soma dos itens (padrao: 0.01).",
    )
    return parser.parse_args(argv)


def _validar_num_cores(valor: int) -> int:
    max_seguro = limite_seguro_cores()
    return max(1, min(valor, max_seguro))

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()

    config = carregar_config()
    args = parse_args()

    pasta_config = config.get("pasta_entrada")
    modo_nao_interativo = args.input is not None or bool(pasta_config)

    if args.input is not None:
        input_dir = args.input.expanduser().resolve()
        if not input_dir.is_dir():
            print(f"Pasta nao encontrada: {input_dir}")
            sys.exit(1)
    elif pasta_config:
        input_dir = Path(pasta_config).expanduser().resolve()
        if not input_dir.is_dir():
            print(f"Pasta nao encontrada (config.yaml): {input_dir}")
            sys.exit(1)
    else:
        input_dir = perguntar_pasta_xml()

    if args.cores:
        num_cores = _validar_num_cores(args.cores)
    elif config.get("nucleos"):
        num_cores = _validar_num_cores(config["nucleos"])
    elif modo_nao_interativo:
        num_cores = limite_seguro_cores()
    else:
        num_cores = perguntar_num_cores()

    lista_zips = listar_zips(input_dir)
    lista_xmls_soltos = listar_xmls(input_dir)

    if not lista_zips and not lista_xmls_soltos:
        print("\nNenhum arquivo encontrado na pasta indicada.")
        if not modo_nao_interativo:
            input("Pressione Enter para sair...")
        sys.exit(0)

    if args.batch_size:
        tamanho_lote = max(1, args.batch_size)
    elif config.get("tamanho_lote"):
        tamanho_lote = max(1, config["tamanho_lote"])
    elif lista_zips and not modo_nao_interativo:
        tamanho_lote = perguntar_tamanho_lote(len(lista_zips))
    else:
        tamanho_lote = 5

    if args.tolerancia is not None:
        tolerancia = args.tolerancia
    else:
        tolerancia = config.get("tolerancia_conciliacao", 0.01)

    resultado = executar_pipeline(input_dir, num_cores, tamanho_lote, tolerancia_conciliacao=tolerancia)

    print(f"\nRelatorio gerado: {resultado.caminho_excel}")

    total_duplicadas = sum(resultado.duplicadas.values())
    if total_duplicadas:
        print(f"{total_duplicadas} nota(s) duplicada(s) ignorada(s).")

    if not resultado.divergencias.empty:
        print(f"{len(resultado.divergencias)} NFe(s) com divergencia entre total e soma dos itens.")

    if not modo_nao_interativo:
        input("\nPressione Enter para sair...")
