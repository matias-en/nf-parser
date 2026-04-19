from src.processor import limpar_num, limpar_int, formatar_data

cte_mod57 = {'cte_mod57': 'http://www.portalfiscal.inf.br/cte'}

def extrair_dados(arvore):
    
    def buscar_int(xpath_str):
        return limpar_int(arvore.xpath(xpath_str, namespaces=cte_mod57))
    
    numero_cte = buscar_int('//cte_mod57:nCT/text()')


    dados_cte = {

        'Numero': numero_cte

    }

       


    return dados_cte