import pandas as pd

def salvar_excel(lista_dados, nome_arquivo="relatorio_notas.xlsx", nome_aba="Serviços"):
    
    if lista_dados:
        df = pd.DataFrame(lista_dados)
        df.to_excel(nome_arquivo, index=False, sheet_name=nome_aba)

        print(f"\n✅ SUCESSO: Arquivo '{nome_arquivo}' gerado com {len(df)} notas.")
    else:
        print("\n ⚠️ AVISO: Nenhuma nota foi processada, então não criei o Excel.")