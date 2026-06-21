import pandas as pd


def salvar_excel(dicionario_dados, nome_arquivo):
    
    escreveu_pelo_menos_uma_aba = False

    with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
        for aba, dados in dicionario_dados.items():

            
            tem_conteudo = False
            if isinstance(dados, pd.DataFrame):
                tem_conteudo = not dados.empty
            elif isinstance(dados, list):
                tem_conteudo = len(dados) > 0

            if tem_conteudo:
                
                df = dados if isinstance(dados, pd.DataFrame) else pd.DataFrame(dados)
                df.to_excel(writer, sheet_name=aba, index=False)
                escreveu_pelo_menos_uma_aba = True

        if not escreveu_pelo_menos_uma_aba:
            pd.DataFrame([{"Status": "Nenhum dado válido encontrado neste lote"}]).to_excel(writer, sheet_name="Aviso",
                                                                                            index=False)