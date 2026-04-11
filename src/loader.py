from lxml import etree
from pathlib import Path
import shutil

def carregar_xml(caminho_arquivo):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(caminho_arquivo), parser)

def listar_xmls(diretorio):
    """Busca todos os arquivos .xml dentro de uma pasta."""
    return list(Path(diretorio).glob("*.xml"))

def mover_arquivos(caminho_origem, pasta_destino):
    caminho_destino = Path(pasta_destino)
    caminho_destino.mkdir(parents=True, exist_ok=True)
    shutil.move(str(caminho_origem), str(caminho_destino / caminho_origem.name))