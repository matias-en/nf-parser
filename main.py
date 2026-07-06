import logging
import os
import zipfile
import pandas as pd
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed, BrokenExecutor

from lxml import etree # type: ignore
from tqdm import tqdm


from src.loader import (
    listar_zips,
    listar_xmls,
    salvar_xml_por_empresa,
    salvar_xml_nao_classificado,
    arquivar_zip_original,
)

from src.nfse_abrasf_parser import extrair_dados as extrair_nfse_abrasf
from src.nfse_parser import extrair_dados as extrair_nfse
from src.nfe_parser import extrair_dados as extrair_nfe
from src.cte_parser import extrair_dados as extrair_cte
from src.event_parser import extrair_cancelamento
from src.excel_gen import salvar_excel
from src.db import BancoFiscal
from src.processor import chave_valida, nome_pasta_empresa, sanitizar_nome_pasta

# LOGGIN

def configurar_logging(pasta_log: Path):
    pasta_log.mkdir(parents=True, exist_ok=True)
    nome_log = f"execucao_{datetime.now():%Y%m%D_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(pasta_log / nome_log, encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )

logger = logging.getLogger(__name__)

# CLASSIFICAÇÃO DE DOCUMENTOS

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

def _empresa_do_documento(tipo: str, dados: dict) -> tuple:
    if not dados or not isinstance(dados, dict):
        return "", "_sem_empresa"
    if tipo == "NFe":
        cab = dados.get("cabecalho", dados)
        return cab.get("CNPJ Emitente", ""), cab.get("Razao Emitente", "_sem_razao")
    if tipo == "CTe":
        return dados.get("CNPJ Transportadora", ""), dados.get("Transportadora", "_sem_razao")
    if tipo in ("NFSe", "NFSe_ABRASF"):
        return dados.get("CNPJ/CPF Prestador", ""), dados.get("Razao Prestador", "_sem_razao")
    if tipo == "CANCELAMENTO":
        return dados.get("CNPJ Emitente", ""), "_cancelamentos"
    return "", "_sem_empresa"

# PEÃO DA OBRA

def trabalhador_zip(args):
    caminho_zip, processados_dir = args
    processados_dir = Path(processados_dir)
    resultados = []

    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            nomes_xml = [n for n in z.namelist() if n.lower().endswith('.xml')]
            for nome_xml in nomes_xml:
                try:
                    conteudo = z.read(nome_xml)
                    arvore = etree.fromstring(conteudo)
                    tipo, dados = _classificar(arvore)

                    # Salva XML organizado por empresa direto no peão
                    if tipo not in ("DESCONHECIDO", "ERRO") and dados is not None:
                        if tipo == "NFe":
                            cab = dados.get("cabecalho", {})
                            cnpj = cab.get("CNPJ Emitente", "")
                            razao = cab.get("Razao Emitente", "_sem_razao")
                        elif tipo == "CTe":
                            cnpj = dados.get("CNPJ Transportadora", "")
                            razao = dados.get("Transportadora", "_sem_razao")
                        elif tipo in ("NFSe", "NFSe_ABRASF"):
                            cnpj = dados.get("CNPJ/CPF Prestador", "")
                            razao = dados.get("Razao Prestador", "_sem_razao")
                        elif tipo == "CANCELAMENTO":
                            cnpj = dados.get("CNPJ Emitente", "")
                            razao = "_cancelamentos"
                        else:
                            cnpj, razao = "", ""

                        if cnpj:
                            pasta = processados_dir / nome_pasta_empresa(cnpj, razao)
                            pasta.mkdir(parents=True, exist_ok=True)
                            (pasta / Path(nome_xml).name).write_bytes(conteudo)
                        else:
                            pasta = processados_dir / "_nao_classificados"
                            pasta.mkdir(parents=True, exist_ok=True)
                            (pasta / Path(nome_xml).name).write_bytes(conteudo)
                    else:
                        pasta = processados_dir / "_nao_classificados"
                        pasta.mkdir(parents=True, exist_ok=True)
                        (pasta / Path(nome_xml).name).write_bytes(conteudo)

                    # Retorna apenas os dados (sem bytes)
                    resultados.append((tipo, dados, nome_xml))

                except Exception as e:
                    resultados.append(("ERRO", f"{nome_xml} em {caminho_zip.name}: {e}", nome_xml))

    except Exception as e:
        resultados.append(("ERRO", f"ZIP corrompido {caminho_zip.name}: {e}", ""))

    return resultados

# CONSOLIDACAO DOS DADOS

def _consolidar_resultado(tipo, dados, nome_xml, caminho_zip, banco):

    if tipo == "ERRO":
        logger.error(dados)
        banco.inserir_erro(str(dados), caminho_zip.name)
        return

    if tipo == "DESCONHECIDO" or dados is None:
        logger.warning(f"XML nao classificado: {nome_xml}")
        banco.inserir_erro(f"Tipo desconhecido: {nome_xml}", caminho_zip.name)
        return

    if tipo == "NFe":
        cab = dados.get("cabecalho", {})
        chave = cab.get("Chave", "")
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

# PROCESSAMENTO EM LOTE (MELHRADO)
# SCRIPT CONTINUAVA FECHANDO SOZINHO

def processar_lote_zips(
    lote: list,
    num_cores: int,
    banco: BancoFiscal,
    processados_dir: Path,
    pbar: tqdm,
):
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
                    logger.error(f"Erro ao processar ZIP {caminho_zip.name}: {e}")
                    banco.inserir_erro(str(e), caminho_zip.name)
                    banco.commit()

                pbar.update(1)

    except BrokenExecutor as e:
        logger.error(
            f"Peão encerrado abruptamente: {e}\n"
            f"Dados processados ate aqui serao incluidos no relatorio."
        )
        banco.commit()

# ENTRADA DOS XML

def perguntar_pasta_xml() -> Path:
    while True:
        caminho = input("\nQual pasta contem os arquivos XML/ZIP? ").strip().strip('"')
        pasta = Path(caminho).expanduser().resolve()
        if pasta.is_dir():
            return pasta
        print(f"Pasta nao encontrada: {pasta}\nTente novamente.")

def perguntar_num_cores() -> int:
    total = os.cpu_count() or 4
    max_seguro = max(1, total // 2)
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
    
# MAIN

if __name__ == "__main__":

    input_dir = perguntar_pasta_xml()
    output_dir = input_dir
    processados_dir = input_dir / "processados"
    logs_dir = input_dir / "logs"

    processados_dir.mkdir(exist_ok=True)
    configurar_logging(logs_dir)

    logger.info(f"Pasta de trabalho: {input_dir}")

    num_cores = perguntar_num_cores()
    logger.info(f"Nucleos em uso: {num_cores}")

    lista_zips = listar_zips(input_dir)
    lista_xmls_soltos = listar_xmls(input_dir)

    logger.info(f"{len(lista_zips)} ZIP(s) encontrado(s).")
    logger.info(f"{len(lista_xmls_soltos)} XML(s) solto(s) encontrado(s).")

    if not lista_zips and not lista_xmls_soltos:
        print("\nNenhum arquivo encontrado na pasta indicada.")
        input("Pressione Enter para sair...")
        exit(0)

    tamanho_lote = perguntar_tamanho_lote(len(lista_zips)) if lista_zips else 5

    with BancoFiscal() as banco:

        # ── ZIPs em paralelo, lote por lote ──────────────────
        if lista_zips:
            total_lotes = -(-len(lista_zips) // tamanho_lote)
            logger.info(
                f"Processando {len(lista_zips)} ZIP(s) em {total_lotes} lote(s) "
                f"de ate {tamanho_lote} ZIP(s) cada."
            )

            with tqdm(total=len(lista_zips), desc="Processando ZIPs", unit="zip") as pbar:
                for i in range(0, len(lista_zips), tamanho_lote):
                    lote = lista_zips[i:i + tamanho_lote]
                    lote_num = (i // tamanho_lote) + 1
                    logger.info(
                        f"Lote {lote_num}/{total_lotes}: {len(lote)} ZIP(s) | "
                        f"ZIPs {i + 1}-{min(i + tamanho_lote, len(lista_zips))} de {len(lista_zips)}"
                    )
                    # Executor recriado a cada lote — evita BrokenProcessPool em cascata
                    processar_lote_zips(lote, num_cores, banco, processados_dir, pbar)

        # ── XMLs soltos ───────────────────────────────────────
        if lista_xmls_soltos:
            with tqdm(total=len(lista_xmls_soltos), desc="Processando XMLs", unit="xml") as pbar:
                for caminho_xml in lista_xmls_soltos:
                    try:
                        conteudo = caminho_xml.read_bytes()
                        arvore = etree.fromstring(conteudo)
                        tipo, dados = _classificar(arvore)

                        if dados is None:
                            salvar_xml_nao_classificado(conteudo, caminho_xml.name, processados_dir)
                            pbar.update(1)
                            continue

                        if tipo == "NFe":
                            banco.inserir_nfe(dados.get("cabecalho", {}), dados.get("produtos", []))
                        elif tipo == "CTe":
                            banco.inserir_cte(dados)
                        elif tipo == "CANCELAMENTO":
                            banco.inserir_cancelamento(dados)
                        elif tipo == "NFSe":
                            banco.inserir_nfse(dados)
                        elif tipo == "NFSe_ABRASF":
                            banco.inserir_nfse_abrasf(dados)
                        else:
                            salvar_xml_nao_classificado(conteudo, caminho_xml.name, processados_dir)
                            pbar.update(1)
                            continue

                        cnpj, razao = _empresa_do_documento(tipo, dados)
                        salvar_xml_por_empresa(conteudo, caminho_xml.name, cnpj, razao, processados_dir)

                    except Exception as e:
                        logger.error(f"Erro ao processar XML solto {caminho_xml.name}: {e}")
                        banco.inserir_erro(str(e), caminho_xml.name)

                    pbar.update(1)
                banco.commit()

        logger.info("Extracao concluida. Gerando relatorio Excel...")
        dados_para_excel = banco.gerar_dataframes()

    nome_excel = f"relatorio_notas_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    caminho_excel = output_dir / nome_excel
    salvar_excel(dados_para_excel, nome_arquivo=caminho_excel)

    print(f"\nRelatorio gerado: {caminho_excel}")
    input("\nPressione Enter para sair...")