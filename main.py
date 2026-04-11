from pathlib import Path
from src.loader import listar_xmls, carregar_xml #, mover_arquivos
from src.nfse_parser import extrair_dados
from src.excel_gen import salvar_excel

# Configuração das pastas.
base_dir = Path(__file__).resolve().parent
input_dir = base_dir / "data" / "input"
output_dir = base_dir / "data" / "output"
processados_dir = base_dir / "data" / "processados"

# Criar a pasta de saida do Excel, caso não exista.
output_dir.mkdir(parents=True, exist_ok=True)
processados_dir.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    arquivos = listar_xmls(input_dir)

    if arquivos:
        print(f"✅ Encontrei {len(arquivos)} arquivos. \n🚀 Iniciando o processamento...")
        lista_final = []

        for nota_atual in arquivos:
            arvore = carregar_xml(nota_atual)
            dados_nota = extrair_dados(arvore)
            lista_final.append(dados_nota)
    
        print("\n🏁 Processamento concluído!")

        # mover_arquivos(nota_atual, processados_dir)

        caminho_excel = output_dir / "relatorio_notas.xlsx"
        salvar_excel(lista_final, nome_arquivo=caminho_excel)
        
    else:
        print("❌ Nenhum arquivo XML encontrado na pasta data/input.")
