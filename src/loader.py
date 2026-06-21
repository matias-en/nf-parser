from lxml import etree
from pathlib import Path
import shutil
import zipfile

def carregar_xml(caminho_arquivo):
    """MANTIDO: Carrega XML a partir de um arquivo no disco."""
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(caminho_arquivo), parser)

def listar_xmls(diretorio):
    """MANTIDO: Busca todos os arquivos .xml soltos na pasta."""
    return list(Path(diretorio).glob("*.xml"))

def listar_zips(diretorio):
    """NOVO: Busca todos os arquivos .zip na pasta input."""
    return list(Path(diretorio).rglob("*.zip"))

def mapear_conteudo_dos_zips(lista_de_zips):
    """NOVO: Mapeia quais XMLs existem dentro de cada ZIP."""
    tarefas = []
    for caminho_zip in lista_de_zips:
        try:
            with zipfile.ZipFile(caminho_zip, 'r') as z:
                # Filtra apenas arquivos XML dentro do ZIP
                xmls_internos = [f for f in z.namelist() if f.lower().endswith('.xml')]
                for nome_xml in xmls_internos:
                    tarefas.append((caminho_zip, nome_xml))
        except zipfile.BadZipFile:
            print(f"❌ Arquivo corrompido ou inválido: {caminho_zip.name}")
    return tarefas

def mover_arquivos(caminho_origem, pasta_destino):
    """MANTIDO: Move o arquivo (XML ou ZIP) para a pasta de destino."""
    caminho_destino = Path(pasta_destino)
    caminho_destino.mkdir(parents=True, exist_ok=True)
    shutil.move(str(caminho_origem), str(caminho_destino / caminho_origem.name))