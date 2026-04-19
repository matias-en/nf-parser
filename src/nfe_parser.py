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
    
    def buscar_data(xpath_str):
        return formatar_data(arvore.xpath(xpath_str, namespaces=nfe_nacional))
    
    numero_nfe = buscar_int('//nfe_sped:nNF/text()')
    modelo_nf = buscar_int('//nfe_sped:mod/text()')
    data_emissao = buscar_data('//nfe_sped:dhEmi/text()')

    cnpj_emit = pegar_valor('//nfe_sped:emit/nfe_sped:CNPJ/text()')


    dados_nfe = {

        "Numero": numero_nfe,
        "Modelo NF": modelo_nf,
        "Data": data_emissao,
        "CNPJ do Emitente": cnpj_emit,
        # "Razão-Emitente": 
    }

    return dados_nfe