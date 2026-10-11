import pytest

from src.db import BancoFiscal


@pytest.fixture
def banco():
    with BancoFiscal() as b:
        yield b


def _cabecalho_nfe(chave="35200714200166000187550010000000046550010466"):
    return {
        "Chave": chave,
        "Numero": 46,
        "Modelo NF": 55,
        "Data": "2020-07-15",
        "CNPJ Emitente": "14.200.166/0001-87",
        "Tipo Doc Emitente": "CNPJ",
        "Razão Emitente": "Empresa Emitente Teste LTDA",
        "UF Emitente": "SP",
        "Operação": "VENDA",
        "CNPJ Destinatário": "11.222.333/0001-81",
        "Tipo Doc Destinatário": "CNPJ",
        "Razão Destinatário": "Cliente Teste",
        "UF Destinatário": "RJ",
        "Valor Total NF": 20.0,
        "Valor Total Produtos": 20.0,
        "BC ICMS": 20.0,
        "ICMS": 1.5,
        "IPI": 0.0,
        "PIS": 0.3,
        "COFINS": 1.2,
    }


def _produto(chave, n_item="1"):
    return {
        "Chave": chave,
        "Numero": 46,
        "Data": "2020-07-15",
        "nItem": n_item,
        "xProd": "Produto de Teste A",
        "NCM": "12345678",
        "CFOP": 5102,
        "uCom": "UN",
        "qCom": 2.0,
        "vUnCom": 10.0,
        "vProd": 20.0,
        "vTotTrib": 3.0,
        "CST ICMS": "00",
        "vICMS": 1.5,
        "CST PIS": "01",
        "vPIS": 0.3,
        "CST COFINS": "01",
        "vCOFINS": 1.2,
        "vIPI": 0.0,
    }


def test_inserir_nfe_nova_retorna_true(banco):
    cab = _cabecalho_nfe()
    assert banco.inserir_nfe(cab, [_produto(cab["Chave"])]) is True


def test_inserir_nfe_duplicada_retorna_false_e_nao_duplica_produtos(banco):
    cab = _cabecalho_nfe()
    produtos = [_produto(cab["Chave"])]

    assert banco.inserir_nfe(cab, produtos) is True
    assert banco.inserir_nfe(cab, produtos) is False

    banco.commit()
    dfs = banco.gerar_dataframes()
    assert len(dfs["Mercadorias (NFe)"]) == 1
    assert len(dfs["Produtos"]) == 1


def test_gerar_dataframes_nfe_contem_colunas_esperadas(banco):
    cab = _cabecalho_nfe()
    banco.inserir_nfe(cab, [_produto(cab["Chave"])])
    banco.commit()

    df = banco.gerar_dataframes()["Mercadorias (NFe)"]
    linha = df.iloc[0]

    assert linha["Chave"] == cab["Chave"]
    assert linha["CNPJ Emitente"] == cab["CNPJ Emitente"]
    assert linha["Valor Total NF"] == 20.0
    assert linha["Valor Total Produtos"] == 20.0
    assert linha["Status"] == "Normal"


def test_cancelamento_marca_status_da_nfe(banco):
    cab = _cabecalho_nfe()
    banco.inserir_nfe(cab, [])
    banco.inserir_cancelamento({
        "Chave Vinculada": cab["Chave"],
        "Data do Evento": "2020-07-16",
        "Status": "Cancelamento",
        "Protocolo Evento": "135200000000001",
        "CNPJ Emitente": cab["CNPJ Emitente"],
        "Tipo Doc Emitente": "CNPJ",
        "Justificativa": "Erro na emissao",
    })
    banco.commit()

    df = banco.gerar_dataframes()["Mercadorias (NFe)"]
    assert df.iloc[0]["Status"] == "Cancelada"


def test_inserir_erro_aparece_na_aba_de_erros(banco):
    banco.inserir_erro("XML corrompido: teste.xml", "lote1.zip")
    banco.commit()

    df = banco.gerar_dataframes()["Erros"]
    assert len(df) == 1
    assert df.iloc[0]["Detalhe"] == "XML corrompido: teste.xml"
    assert df.iloc[0]["Origem"] == "lote1.zip"


def test_nfse_grava_codigo_tributacao_nacional_com_zero_a_esquerda(banco):
    banco.inserir_nfse({
        "Chave": "35200714200166000187000000000000001000000001",
        "Numero": 1,
        "Data": "2021-03-10",
        "CNPJ/CPF Prestador": "14.200.166/0001-87",
        "Razão Prestador": "Prestador Teste",
        "Valor Total": 1000.0,
        "Cód. Serviço": "040301",
    })
    banco.commit()

    df = banco.gerar_dataframes()["Serviços (Nacional)"]
    assert df.iloc[0]["Cód. Serviço"] == "040301"


def test_resumo_cfop_agrupa_por_cfop(banco):
    cab = _cabecalho_nfe()
    banco.inserir_nfe(cab, [_produto(cab["Chave"], n_item="1"), _produto(cab["Chave"], n_item="2")])
    banco.commit()

    df = banco.gerar_dataframes()["Resumo CFOP"]
    linha = df[df["CFOP"] == 5102].iloc[0]
    assert linha["Qtd Itens"] == 2
    assert linha["Total vProd"] == 40.0


def test_resumo_duplicadas_zerado_por_padrao(banco):
    assert banco.resumo_duplicadas() == {
        "nfe": 0, "cte": 0, "cancelamento": 0, "nfse": 0, "nfse_abrasf": 0,
    }


def test_resumo_duplicadas_conta_nfe_repetida(banco):
    cab = _cabecalho_nfe()
    banco.inserir_nfe(cab, [])
    banco.inserir_nfe(cab, [])
    banco.inserir_nfe(cab, [])

    assert banco.resumo_duplicadas()["nfe"] == 2


def test_resumo_duplicadas_conta_cte_nfse_e_cancelamento_repetidos(banco):
    cte = {"Chave CTe": "35200714200166000187570010000000015550010465"}
    nfse = {"Chave": "35200714200166000187000000000000001000000001"}
    nfse_abrasf = {"Numero": 1, "Data": "2020-01-01", "CNPJ/CPF Prestador": "14.200.166/0001-87"}
    cancelamento = {"Chave Vinculada": "35200714200166000187550010000000046550010466", "Protocolo Evento": "1"}

    assert banco.inserir_cte(cte) is True
    assert banco.inserir_cte(cte) is False
    assert banco.inserir_nfse(nfse) is True
    assert banco.inserir_nfse(nfse) is False
    assert banco.inserir_nfse_abrasf(nfse_abrasf) is True
    assert banco.inserir_nfse_abrasf(nfse_abrasf) is False
    assert banco.inserir_cancelamento(cancelamento) is True
    assert banco.inserir_cancelamento(cancelamento) is False

    resumo = banco.resumo_duplicadas()
    assert resumo["cte"] == 1
    assert resumo["nfse"] == 1
    assert resumo["nfse_abrasf"] == 1
    assert resumo["cancelamento"] == 1


def test_resumo_execucao_reflete_notas_unicas_e_duplicadas(banco):
    cab = _cabecalho_nfe()
    banco.inserir_nfe(cab, [])
    banco.inserir_nfe(cab, [])
    banco.commit()

    df = banco.gerar_dataframes()["Resumo Execução"]
    linha_nfe = df[df["Tipo de Documento"] == "NFe"].iloc[0]
    assert linha_nfe["Notas Únicas"] == 1
    assert linha_nfe["Duplicadas Ignoradas"] == 1


def test_banco_e_arquivo_temporario_removido_ao_sair_do_context_manager():
    with BancoFiscal() as b:
        caminho = b._caminho
        import os
        assert os.path.exists(caminho)
    assert not os.path.exists(caminho)
