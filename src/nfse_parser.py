from src.processor import limpar_num, limpar_int, formatar_data
from datetime import datetime

nfse_nacional = {'nfse_sped': 'http://www.sped.fazenda.gov.br/nfse'}

def extrair_dados(arvore):

    def pegar_valor(xpath_str):
        res = arvore.xpath(xpath_str, namespaces=nfse_nacional)
        return res[0] if res else ""
    
    def buscar_num(xpath_str):
        return limpar_num(arvore.xpath(xpath_str, namespaces=nfse_nacional))

    def buscar_int(xpath_str):
        return limpar_int(arvore.xpath(xpath_str, namespaces=nfse_nacional))

    def buscar_data(xpath_str):
        return formatar_data(arvore.xpath(xpath_str, namespaces=nfse_nacional))
    
    # Busca os dados do número e data de competência da NFSe.
    numero = buscar_int('//nfse_sped:nNFSe/text()')
    data_final = buscar_data('//nfse_sped:dCompet/text()')
        
    # Busca os dados de CNPJ ou CPF e nome do Prestador.
    doc_p = pegar_valor('//nfse_sped:emit/nfse_sped:CNPJ/text()') or pegar_valor('//nfse_sped:emit//nfse_sped:CPF/text()')
    nome_p = pegar_valor('//nfse_sped:emit/nfse_sped:xNome/text()')

    # Busca os dados de CNPJ ou CPF e nome do Tomador.
    doc_t = pegar_valor('//nfse_sped:toma/nfse_sped:CNPJ/text()') or pegar_valor('//nfse_sped:toma/nfse_sped:CPF/text()')
    nome_t = pegar_valor('//nfse_sped:toma/nfse_sped:xNome/text()')
        
    # Busca os valores de serviço e impostos.
    v_total = buscar_num('//nfse_sped:valores/nfse_sped:vServPrest/nfse_sped:vServ/text()')
    v_issqn = buscar_num('//nfse_sped:valores/nfse_sped:vISSQN/text()')
    aliq = buscar_num('//nfse_sped:valores/nfse_sped:pAliqAplic/text()') / 100
    v_liq = buscar_num('//nfse_sped:valores/nfse_sped:vLiq/text()')
    # v_irrf = buscar_num('//nfse_sped:valores/nfse_sped:vIRRF/text()') Preciso Ler a nota técnica para ver qual nome do campo.
    # v_cpp = buscar_num('//nfse_sped:valores/nfse_sped:vCP/text()') Preciso Ler a nota técnica para ver qual nome do campo.
    # v_csll = buscar_num('//nfse_sped:valores/nfse_sped:vCSLL/text()') Preciso Ler a nota técnica para ver qual nome do campo.

            
    # Busca a informação se o ISS é retido e retorna indicando Sim ou Não, conforme nota técnica da RFB.
    ret_cod = pegar_valor('//nfse_sped:tribMun/nfse_sped:tpRetISSQN/text()')
    ret_texto = "Sim" if ret_cod == "2" else "Não"

    dados_nota = {

        "Numero": numero,
        "Data": data_final,
        "CNPJ/CPF Prestador": doc_p,
        "Razão Prestador": nome_p,
        "CNPJ/CPF Tomador": doc_t,
        "Razão Tomador": nome_t,
        "Valor Total": v_total,
        "Aliq ISSQN": aliq,
        "ISSQN": v_issqn,
        "ISSQN Retido": ret_texto,
        #"IRRF": v_irrf
        #"CPP": v_cpp
        #"CSRF": v_csll
        "Valor Liquido": v_liq
    }
    
    return dados_nota