import pandas as pd

from src.conciliacao import conciliar_valores


def _df_nfe(linhas):
    return pd.DataFrame(linhas, columns=["Chave", "Numero", "Razão Emitente", "Valor Total Produtos"])


def _df_produtos(linhas):
    return pd.DataFrame(linhas, columns=["Chave", "vProd"])


def test_sem_divergencia_quando_totais_batem():
    df_nfe = _df_nfe([["CHAVE1", 1, "Empresa A", 100.00]])
    df_produtos = _df_produtos([["CHAVE1", 60.00], ["CHAVE1", 40.00]])

    resultado = conciliar_valores(df_nfe, df_produtos)
    assert resultado.empty


def test_divergencia_quando_soma_dos_itens_diverge_do_total():
    df_nfe = _df_nfe([["CHAVE1", 1, "Empresa A", 100.00]])
    df_produtos = _df_produtos([["CHAVE1", 60.00], ["CHAVE1", 30.00]])

    resultado = conciliar_valores(df_nfe, df_produtos)
    assert len(resultado) == 1
    linha = resultado.iloc[0]
    assert linha["Chave"] == "CHAVE1"
    assert linha["Valor Total Produtos"] == 100.00
    assert linha["Soma dos Itens"] == 90.00
    assert linha["Diferença"] == 10.00


def test_nfe_sem_produtos_e_tratada_como_soma_zero():
    df_nfe = _df_nfe([["CHAVE1", 1, "Empresa A", 50.00]])
    df_produtos = _df_produtos([])

    resultado = conciliar_valores(df_nfe, df_produtos)
    assert len(resultado) == 1
    assert resultado.iloc[0]["Soma dos Itens"] == 0.0
    assert resultado.iloc[0]["Diferença"] == 50.00


def test_diferenca_dentro_da_tolerancia_nao_e_sinalizada():
    df_nfe = _df_nfe([["CHAVE1", 1, "Empresa A", 100.00]])
    df_produtos = _df_produtos([["CHAVE1", 99.995]])

    resultado = conciliar_valores(df_nfe, df_produtos, tolerancia=0.01)
    assert resultado.empty


def test_diferenca_acima_da_tolerancia_e_sinalizada():
    df_nfe = _df_nfe([["CHAVE1", 1, "Empresa A", 100.00]])
    df_produtos = _df_produtos([["CHAVE1", 99.90]])

    resultado = conciliar_valores(df_nfe, df_produtos, tolerancia=0.01)
    assert len(resultado) == 1


def test_dataframes_vazios_retornam_estrutura_vazia():
    resultado = conciliar_valores(pd.DataFrame(), pd.DataFrame())
    assert resultado.empty
    assert list(resultado.columns) == [
        "Chave", "Numero", "Razão Emitente",
        "Valor Total Produtos", "Soma dos Itens", "Diferença",
    ]


def test_multiplas_nfe_apenas_a_divergente_e_retornada():
    df_nfe = _df_nfe([
        ["CHAVE1", 1, "Empresa A", 100.00],
        ["CHAVE2", 2, "Empresa B", 200.00],
    ])
    df_produtos = _df_produtos([
        ["CHAVE1", 100.00],
        ["CHAVE2", 150.00],
    ])

    resultado = conciliar_valores(df_nfe, df_produtos)
    assert len(resultado) == 1
    assert resultado.iloc[0]["Chave"] == "CHAVE2"
