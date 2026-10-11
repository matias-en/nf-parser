import logging

from lxml import etree

import main
from src.db import BancoFiscal
from tests.test_nfe_parser import XML_NFE
from tests.test_cte_parser import XML_CTE
from tests.test_nfse_parser import XML_NFSE
from tests.test_nfse_abrasf_parser import XML_ABRASF
from tests.test_event_parser import XML_CANCELAMENTO


def _raiz(xml_str: str):
    return etree.fromstring(xml_str.encode("utf-8"))


def test_classificar_identifica_nfe():
    tipo, dados = main._classificar(_raiz(XML_NFE))
    assert tipo == "NFe"
    assert dados["cabecalho"]["Chave"]


def test_classificar_identifica_cte():
    tipo, dados = main._classificar(_raiz(XML_CTE))
    assert tipo == "CTe"
    assert dados["Chave CTe"]


def test_classificar_identifica_nfse_nacional():
    tipo, dados = main._classificar(_raiz(XML_NFSE))
    assert tipo == "NFSe"
    assert dados["Chave"]


def test_classificar_identifica_nfse_abrasf():
    tipo, dados = main._classificar(_raiz(XML_ABRASF))
    assert tipo == "NFSe_ABRASF"
    assert dados["Numero"] == 987


def test_classificar_identifica_cancelamento():
    tipo, dados = main._classificar(_raiz(XML_CANCELAMENTO))
    assert tipo == "CANCELAMENTO"
    assert dados["Status"] == "Cancelamento"


def test_classificar_documento_desconhecido():
    xml_desconhecido = '<algumOutroDocumento xmlns="http://exemplo.org/outro"></algumOutroDocumento>'
    tipo, dados = main._classificar(_raiz(xml_desconhecido))
    assert tipo == "DESCONHECIDO"
    assert dados is None


def test_empresa_do_documento_nfe_usa_razao_com_acento():
    dados = {"cabecalho": {"CNPJ Emitente": "14.200.166/0001-87", "Razão Emitente": "Empresa Teste"}}
    cnpj, razao = main._empresa_do_documento("NFe", dados)
    assert cnpj == "14.200.166/0001-87"
    assert razao == "Empresa Teste"


def test_empresa_do_documento_nfse_usa_razao_com_acento():
    dados = {"CNPJ/CPF Prestador": "14.200.166/0001-87", "Razão Prestador": "Prestador Teste"}
    cnpj, razao = main._empresa_do_documento("NFSe", dados)
    assert cnpj == "14.200.166/0001-87"
    assert razao == "Prestador Teste"


def test_empresa_do_documento_sem_dados_retorna_sem_empresa():
    cnpj, razao = main._empresa_do_documento("DESCONHECIDO", None)
    assert cnpj == ""
    assert razao == "_sem_empresa"


def test_empresa_do_documento_cte_usa_transportadora():
    dados = {"CNPJ Transportadora": "14.200.166/0001-87", "Transportadora": "Transportadora Teste"}
    cnpj, razao = main._empresa_do_documento("CTe", dados)
    assert cnpj == "14.200.166/0001-87"
    assert razao == "Transportadora Teste"


def test_processar_um_xml_nfe_valida_salva_na_pasta_da_empresa(tmp_path):
    conteudo = XML_NFE.encode("utf-8")
    tipo, dados, nome_xml = main._processar_um_xml(conteudo, "nfe_teste.xml", tmp_path)

    assert tipo == "NFe"
    assert nome_xml == "nfe_teste.xml"

    pasta_empresa = tmp_path / "14200166000187 - Empresa Emitente Teste LTDA"
    assert (pasta_empresa / "nfe_teste.xml").exists()
    assert (pasta_empresa / "nfe_teste.xml").read_bytes() == conteudo


def test_processar_um_xml_invalido_vai_para_nao_classificados(tmp_path):
    conteudo = b"isto nao e um xml valido <<<"
    tipo, dados, nome_xml = main._processar_um_xml(conteudo, "quebrado.xml", tmp_path)

    assert tipo == "ERRO"
    assert "quebrado.xml" in dados
    assert (tmp_path / "_nao_classificados" / "quebrado.xml").exists()


def test_processar_um_xml_desconhecido_vai_para_nao_classificados(tmp_path):
    conteudo = b'<algumOutroDocumento xmlns="http://exemplo.org/outro"></algumOutroDocumento>'
    tipo, dados, nome_xml = main._processar_um_xml(conteudo, "outro.xml", tmp_path)

    assert tipo == "DESCONHECIDO"
    assert (tmp_path / "_nao_classificados" / "outro.xml").exists()


def test_consolidar_resultado_nfe_com_cabecalho_vazio_vira_erro(tmp_path):
    with BancoFiscal() as banco:
        main._consolidar_resultado(
            "NFe", {"cabecalho": {}, "produtos": []}, "nfe_sem_dados.xml", tmp_path / "lote1.zip", banco
        )
        banco.commit()
        dfs = banco.gerar_dataframes()

    assert dfs["Mercadorias (NFe)"].empty
    assert len(dfs["Erros"]) == 1
    assert "nfe_sem_dados.xml" in dfs["Erros"].iloc[0]["Detalhe"]


def test_configurar_logging_sem_stderr_nao_adiciona_streamhandler(tmp_path, monkeypatch):
    monkeypatch.setattr(main.sys, "stderr", None)
    try:
        main.configurar_logging(tmp_path / "logs")
        tipos = [type(h) for h in logging.getLogger().handlers]
        assert logging.StreamHandler not in tipos
    finally:
        for h in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(h)
            h.close()
