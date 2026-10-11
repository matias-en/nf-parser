import pandas as pd


def conciliar_valores(df_nfe: pd.DataFrame, df_produtos: pd.DataFrame, tolerancia: float = 0.01) -> pd.DataFrame:
    colunas = [
        "Chave", "Numero", "Razão Emitente",
        "Valor Total Produtos", "Soma dos Itens", "Diferença",
    ]

    if df_nfe.empty:
        return pd.DataFrame(columns=colunas)

    soma_itens = (
        df_produtos.groupby("Chave", as_index=False)["vProd"]
        .sum()
        .rename(columns={"vProd": "Soma dos Itens"})
    )

    comparacao = df_nfe[["Chave", "Numero", "Razão Emitente", "Valor Total Produtos"]].merge(
        soma_itens, on="Chave", how="left"
    )
    comparacao["Soma dos Itens"] = comparacao["Soma dos Itens"].fillna(0.0)
    comparacao["Diferença"] = (comparacao["Valor Total Produtos"] - comparacao["Soma dos Itens"]).round(2)

    divergentes = comparacao[comparacao["Diferença"].abs() > tolerancia]
    return divergentes[colunas].reset_index(drop=True)
