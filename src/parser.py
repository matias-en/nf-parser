from lxml import etree
from pathlib import Path
from excel_gen import salvar_excel
from datetime import datetime

# Diretórios
base_dir = Path(__file__).resolve().parent.parent
input_dir = base_dir / "data" / "input"
output_dir = base_dir / "data" / "output"

# Cria a pasta output em caso de não existência.
output_dir.mkdir(parents=True, exist_ok=True)

arquivos = list(input_dir.glob("*.xml"))

# Dicionário de apelidos
nfse_nacional = {'nfse_sped': 'http://www.sped.fazenda.gov.br/nfse'}

# Aqui cria uma "receita de bolo" de como ler o xml e transformar ele em um formato melhor para navegar "arvore".
def carregar_xml(caminho_arquivo):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(caminho_arquivo), parser)

# Aqui onde iremos ler os arquivos e buscar as informações que desejamos, usando __name__ == "__main__" para executar esse arquivo por enquanto
if __name__ == "__main__":
    if arquivos:
        print(f"Encontrei {len(arquivos)} arquivos. \nIniciando o processamento.")

        lista_final = []

        for nota_atual in arquivos:
            arvore = carregar_xml(nota_atual)

            numero = arvore.xpath('//nfse_sped:nNFSe/text()', namespaces=nfse_nacional)
            data_competencia = arvore.xpath('//nfse_sped:dCompet/text()', namespaces=nfse_nacional)
            id_prestador = arvore.xpath('//nfse_sped:emit/nfse_sped:CNPJ/text()', namespaces=nfse_nacional)
            prestador_nfse = arvore.xpath('//nfse_sped:emit/nfse_sped:xNome/text()', namespaces=nfse_nacional)
            id_tomador = arvore.xpath('//nfse_sped:toma/nfse_sped:CPF/text()', namespaces=nfse_nacional)
            tomador_nfse = arvore.xpath('//nfse_sped:toma/nfse_sped:xNome/text()', namespaces=nfse_nacional)
            vr_total = arvore.xpath('//nfse_sped:valores/nfse_sped:vServPrest/nfse_sped:vServ/text()', namespaces=nfse_nacional)
            vr_liquido = arvore.xpath('//nfse_sped:valores/nfse_sped:vLiq/text()', namespaces=nfse_nacional)

            if numero and data_competencia and prestador_nfse and vr_total and vr_liquido and id_prestador and id_tomador:
               
                vr_total_num = float(vr_total[0]) #Ele vai ler somente quando houver . no lugar da virgula, proxima aula resolveremos esse problema.
                vr_liquido_num = float(vr_liquido[0])
                
                try:
                    data = datetime.strptime(data_competencia[0], "%Y-%m-%d").date()
                except ValueError:
                    data = data_competencia[0]       

                dados_nota = {

                    "Numero": numero[0],
                    "Data": data,
                    "CNPJ/CPF Prestador": id_prestador[0],
                    "Razão Prestador": prestador_nfse[0],
                    "CNPJ/CPF Tomador": id_tomador[0],
                    "Razão Tomador": tomador_nfse[0],
                    "Valor Total": vr_total_num,
                    "Valor Liquido": vr_liquido_num
                }
                
                lista_final.append(dados_nota)
        
        print("\nProcessamento concluído")
        excel_dir = output_dir / "relatorio_notas.xlsx"
        salvar_excel(lista_final, nome_arquivo=excel_dir)
    else:
        print("Nenhum arquivo XML encontrado na pasta data/input.")

