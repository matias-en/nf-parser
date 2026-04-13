from src.processor import limpar_num, limpar_int, formatar_data

nfe_nacional = {'nfe_sped': 'http://www.portalfiscal.inf.br/nfe'}

def extrair_dados(arvore):

    def pegar_valor(xpath_str):
        res = arvore.xpath(xpath_str, namespaces=nfe_nacional)
        return res[0] if res else ""
    
    def buscar_num(xpath_str):
        return limpar_num(arvore.xpath(xpath_str, namespaces=nfe_nacional))

    def buscar_int(xpath_str):
        return limpar_int(arvore.xpath(xpath_str, namespaces=nfe_nacional))
    
    numero_nfe = buscar_int('//nfe_sped:nNF/text()')


    dados_nfe = {

        "Numero": numero_nfe,

    }

    return dados_nfe