import os
import zipfile
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from lxml import etree
from tqdm import tqdm
from collections import defaultdict

from src.loader import listar_zips, mapear_conteudo_dos_zips, mover_arquivos
from src.nfse_abrasf_parser import extrair_dados as extrair_nfse_abrasf
from src.nfse_parser import extrair_dados as extrair_nfse
from src.nfe_parser import extrair_dados as extrair_nfe
from src.cte_parser import extrair_dados as extrair_cte
from src.event_parser import extrair_cancelamento
from src.excel_gen import salvar_excel

base_dir = Path(__file__).resolve().parent
input_dir = base_dir / "data" / "input"
output_dir = base_dir / "data" / "output"
processados_dir = base_dir / "data" / "processados"

NS = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
    'cte': 'http://www.portalfiscal.inf.br/cte',
}

def trabalhador_zip(caminho_zip: Path):
    resultados = []
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            nomes_xml = [n for n in z.namelist() if n.lower().endswith('.xml')]
            for nome_xml in nomes_xml:
                try:
                    conteudo = z.read(nome_xml)
                    arvore = etree.fromstring(conteudo)
                    tipo, dados = _classificar(arvore)
                    if dados:
                        resultados.append((tipo, dados))
                except Exception as e:
                    resultados.append(("ERRO", f"{nome_xml} em {caminho_zip.name}: {e}"))
    except Exception as e:
        resultados.append(("ERRO", f"ZIP corrompido {caminho_zip.name}: {e}"))
    return resultados

def _classificar(arvore):
    tag_raiz = arvore.tag.lower()

    # Separa namespace e nome local da tag raiz, ex:
    # "{http://www.abrasf.org.br/nfse.xsd}compnfse" -> namespace="http://www.abrasf.org.br/nfse.xsd", local="compnfse"
    if tag_raiz.startswith("{"):
        namespace, _, nome_local = tag_raiz[1:].partition("}")
    else:
        namespace, nome_local = "", tag_raiz

    # 1. CANCELAMENTOS (eventos da NFe nacional)
    if "procevento" in nome_local:
        return "CANCELAMENTO", extrair_cancelamento(arvore)

    # 2. CTE (namespace próprio do CTe)
    if "portalfiscal.inf.br/cte" in namespace:
        return "CTe", extrair_cte(arvore)

    # 3. NFe (namespace próprio da NFe nacional)
    if "portalfiscal.inf.br/nfe" in namespace:
        return "NFe", extrair_nfe(arvore)

    # 4. NFSe ABRASF (namespace abrasf.org.br)
    if "abrasf.org.br" in namespace:
        return "NFSe_ABRASF", extrair_nfse_abrasf(arvore)

    # 5. NFSe NACIONAL (namespace sped.fazenda.gov.br/nfse)
    if "sped.fazenda.gov.br/nfse" in namespace:
        return "NFSe", extrair_nfse(arvore)

    return "DESCONHECIDO", None

if __name__ == "__main__":
    output_dir.mkdir(parents=True, exist_ok=True)
    processados_dir.mkdir(parents=True, exist_ok=True)

    total_cores = os.cpu_count()
    max_seguro = max(1, (os.cpu_count() or 4) - 2)
    print(f"🖥️ Hardware detectado: {total_cores} núcleos.")
    print(f"🛡️ Limite de segurança sugerido: {max_seguro} núcleos.")

    try:
        escolha = int(input(f"Quantos núcleos deseja usar? (1 a {max_seguro}): "))
        num_cores = max(1, min(escolha, max_seguro))
    except ValueError:
        num_cores = max_seguro

    lista_zips = listar_zips(input_dir)
    print(f"✅ {len(lista_zips)} ZIPs encontrados.")

    acumulador = defaultdict(list)
    chaves_nfe_vistas = set()

    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futuros = {executor.submit(trabalhador_zip, z): z for z in lista_zips}

        with tqdm(total=len(lista_zips), desc="📦 Processando ZIPs", unit="zip") as pbar:
            for futuro in as_completed(futuros):

                for tipo, dados in futuro.result():
                    if tipo == "NFe":
                        chave_atual = dados["cabecalho"].get("Chave", "")
                        if chave_atual and chave_atual not in chaves_nfe_vistas:
                            chaves_nfe_vistas.add(chave_atual)
                            acumulador["NFe"].append(dados["cabecalho"])
                            acumulador["Produtos"].extend(dados["produtos"])
                    # chave repetida ou vazia → ignora silenciosamente
                        else:
                            acumulador[tipo].append(dados)

            pbar.update(1)

    print("\n🏁 Extração concluída. Consolidando relatório no Excel...")

    df_nfe = pd.DataFrame(acumulador["NFe"])
    if not df_nfe.empty:
        df_nfe = df_nfe.dropna(subset=['Chave'])
        df_nfe = df_nfe[df_nfe['Chave'].astype(str).str.strip() != ""]
        df_nfe = df_nfe.drop_duplicates(subset=['Chave']) # deixar aqui por enquanto

    df_produtos = pd.DataFrame(acumulador["Produtos"])

    dados_para_excel = {
        "Mercadorias (NFe)": df_nfe,
        "Produtos": df_produtos,
        "Transporte (CTe)": acumulador["CTe"],
        "Cancelamentos": acumulador["CANCELAMENTO"],
        "Serviços (Nacional)": acumulador["NFSe"],
        "Serviços (ABRASF)": acumulador["NFSe_ABRASF"],
    }

    caminho_excel = output_dir / "relatorio_notas_completo.xlsx"
    salvar_excel(dados_para_excel, nome_arquivo=caminho_excel)
    print(f"📊 Relatório gerado com sucesso em: {caminho_excel}")