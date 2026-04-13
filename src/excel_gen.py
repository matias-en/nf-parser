import pandas as pd

def salvar_excel(dicionario_aba, nome_arquivo):
    
    with pd.ExcelWriter(nome_arquivo) as writer:
        for nome_aba, dados in dicionario_aba.items():
            if dados:
                df = pd.DataFrame(dados)
                df.to_excel(writer, sheet_name=nome_aba, index=False)
                print(f"📊 Aba '{nome_aba}' gerada com {len(dados)} registros.")


    print(f"\n✅ Relatório completo gerado em: {nome_arquivo}")