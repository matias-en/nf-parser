import logging
import shutil
import zipfile
from lxml import etree  # type: ignore
from pathlib import Path

from src.processor import nome_pasta_empresa

logger = logging.getLogger(__name__)


def carregar_xml(caminho_arquivo: Path):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(caminho_arquivo), parser)


def listar_xmls(diretorio: Path) -> list:
    return [
        p for p in Path(diretorio).glob("*.xml")
        if "processados" not in p.parts
    ]


def listar_zips(diretorio: Path) -> list:
    return [
        p for p in Path(diretorio).rglob("*.zip")
        if "processados" not in p.parts
    ]


def mapear_conteudo_dos_zips(lista_de_zips: list) -> list:
    tarefas = []
    for caminho_zip in lista_de_zips:
        try:
            with zipfile.ZipFile(caminho_zip, 'r') as z:
                xmls_internos = [f for f in z.namelist() if f.lower().endswith('.xml')]
                for nome_xml in xmls_internos:
                    tarefas.append((caminho_zip, nome_xml))
        except zipfile.BadZipFile:
            logger.error(f"Arquivo corrompido ou inválido: {caminho_zip.name}")
    return tarefas


def salvar_xml_por_empresa(
    conteudo_xml: bytes,
    nome_xml: str,
    cnpj: str,
    razao_social: str,
    processados_dir: Path
) -> None:

    pasta_empresa = processados_dir / nome_pasta_empresa(cnpj, razao_social)
    pasta_empresa.mkdir(parents=True, exist_ok=True)

    destino = pasta_empresa / Path(nome_xml).name
    destino.write_bytes(conteudo_xml)


def salvar_xml_nao_classificado(
    conteudo_xml: bytes,
    nome_xml: str,
    processados_dir: Path
) -> None:

    pasta = processados_dir / "_nao_classificados"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / Path(nome_xml).name).write_bytes(conteudo_xml)


def arquivar_zip_original(caminho_zip: Path, processados_dir: Path) -> None:
    pasta_backup = processados_dir / "_zips_originais"
    pasta_backup.mkdir(parents=True, exist_ok=True)
    shutil.move(str(caminho_zip), str(pasta_backup / caminho_zip.name))
