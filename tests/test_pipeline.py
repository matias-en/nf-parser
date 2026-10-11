import zipfile

import pytest

import main
from tests.test_nfe_parser import XML_NFE


def _criar_zip(pasta, nome_zip, xmls: dict):
    caminho = pasta / nome_zip
    with zipfile.ZipFile(caminho, "w") as z:
        for nome_xml, conteudo in xmls.items():
            z.writestr(nome_xml, conteudo)
    return caminho


def _xml_nfe_com_chave(chave):
    return XML_NFE.replace(
        'Id="NFe35200714200166000187550010000000046550010466"',
        f'Id="NFe{chave}"',
    )


def test_executar_pipeline_sem_arquivos_levanta_excecao(tmp_path):
    with pytest.raises(main.NenhumArquivoEncontrado):
        main.executar_pipeline(tmp_path, num_cores=1, tamanho_lote=5)


def test_executar_pipeline_gera_excel_sem_divergencia(tmp_path):
    _criar_zip(tmp_path, "lote1.zip", {"nfe.xml": XML_NFE})

    resultado = main.executar_pipeline(tmp_path, num_cores=1, tamanho_lote=5)

    assert resultado.caminho_excel.exists()
    assert resultado.total_zips == 1
    assert resultado.total_xmls == 0
    assert resultado.duplicadas["nfe"] == 0
    assert resultado.divergencias.empty


def test_executar_pipeline_conta_duplicadas_entre_zips(tmp_path):
    _criar_zip(tmp_path, "lote1.zip", {"nfe.xml": XML_NFE})
    _criar_zip(tmp_path, "lote2.zip", {"nfe_copia.xml": XML_NFE})

    resultado = main.executar_pipeline(tmp_path, num_cores=1, tamanho_lote=5)

    assert resultado.duplicadas["nfe"] == 1


def test_executar_pipeline_sinaliza_divergencia(tmp_path):
    xml_divergente = XML_NFE.replace("<vProd>20,00</vProd>\n        </prod>", "<vProd>15,00</vProd>\n        </prod>")
    _criar_zip(tmp_path, "lote1.zip", {"nfe.xml": xml_divergente})

    resultado = main.executar_pipeline(tmp_path, num_cores=1, tamanho_lote=5)

    assert len(resultado.divergencias) == 1
    assert resultado.divergencias.iloc[0]["Diferença"] == 5.00


def test_executar_pipeline_chama_callback_de_progresso(tmp_path):
    _criar_zip(tmp_path, "lote1.zip", {"a.xml": _xml_nfe_com_chave("1" * 44)})
    _criar_zip(tmp_path, "lote2.zip", {"b.xml": _xml_nfe_com_chave("2" * 44)})

    chamadas = []
    main.executar_pipeline(
        tmp_path, num_cores=1, tamanho_lote=5,
        progresso_zip=lambda atual, total: chamadas.append((atual, total)),
    )

    assert chamadas == [(1, 2), (2, 2)]
