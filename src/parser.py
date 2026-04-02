#Aqui estou falando para o código trazer a ferramenta da caixa de ferramentas (import - tras a caixa, from especifica o item)
from lxml import etree
from pathlib import Path

# Aqui estou descrevendo o caminho base para o projeto. __file__ é o arquivo atual
# .parent.parente volta duas pastas.
# .resolve pega o endereço absoluto do C://
base_dir = Path(__file__).resolve().parent.parent
input_dir = base_dir / "data" / "input"
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
        nota_atual = arquivos[0]
        print(f"Lendo arquivos: {nota_atual.name}")

        # Abrir a nota fiscal
        arvore = carregar_xml(nota_atual)
        # Buscar o número da NFSe
        buscar_numero = arvore.xpath('//nfse_sped:nNFSe/text()', namespaces=nfse_nacional)
        # Buscar o nome do Prestador
        buscar_prestador = arvore.xpath('//nfse_sped:emit/nfse_sped:xNome/text()', namespaces=nfse_nacional)
        # Buscar o valor líquido
        buscar_valorliq = arvore.xpath('//nfse_sped:valores/nfse_sped:vLiq/text()', namespaces=nfse_nacional)
        # Buscar tomador, desafio do curso.
        buscar_tomador = arvore.xpath('//nfse_sped:toma/nfse_sped:xNome/text()', namespaces=nfse_nacional)

        # Mostrar os resultados
        if buscar_numero:
            print(f"Número da NFSe é {buscar_numero[0]}")

        if buscar_prestador:
            print(f"Nome do Prestador é {buscar_prestador[0]}")

        if buscar_valorliq:
            print(f"Valor líquido da operação é {buscar_valorliq[0]}")
        # Aqui está irá retornar como texto, deixarei essa notação para resolver posteriormente conforme aprendizado.

        if buscar_tomador:
            print(f"Nome do tomador é {buscar_tomador[0]}")

    else:
        print("Não encontrei nenhum item na pasta.")

