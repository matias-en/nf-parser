from pathlib import Path
from src.loader import listar_xmls, carregar_xml #, mover_arquivos
from src.nfse_parser import extrair_dados as extrair_nfse
from src.nfe_parser import extrair_dados as extrair_nfe
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
        lista_nfse = [] 
        lista_nfe = []

        for nota_atual in arquivos:
            arvore = carregar_xml(nota_atual)

            if arvore.xpath('//*[local-name()="infNFSe"]'):
                dados_nfse = extrair_nfse(arvore)
                lista_nfse.append(dados_nfse)
                print(f"🏢 {nota_atual.name} -> Processada como SERVIÇO")

            else:
                dados_nfe = extrair_nfe(arvore)
                lista_nfe.append(dados_nfe)
                print(f"📦 {nota_atual.name} -> Processada como MERCADORIA")
    
        print("\n🏁 Processamento concluído!")

        dados_para_excel = {
            "Serviços (NFSe)": lista_nfse,
            "Mercadorias (NFe)": lista_nfe
        }

        # mover_arquivos(nota_atual, processados_dir)

        caminho_excel = output_dir / "relatorio_notas.xlsx"
        salvar_excel(dados_para_excel, nome_arquivo=caminho_excel)
        
    else:
        print("❌ Nenhum arquivo XML encontrado na pasta data/input.")
