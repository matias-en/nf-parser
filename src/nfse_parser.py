from src.processor import limpar_num, limpar_int, formatar_data, formatar_cnpj_cpf

nfse_nacional = {'nfse_sped': 'http://www.sped.fazenda.gov.br/nfse'}

def _tipo_documento(doc_cnpj: str, doc_cpf: str) -> str:
    if doc_cnpj:
        return "CNPJ"
    if doc_cpf:
        return "CPF"
    return ""

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

    chave_nfse = "".join(filter(str.isdigit, pegar_valor('//nfse_sped:infNFSe/@Id')))

    # PRESTADOR
    cnpj_prest = pegar_valor('//nfse_sped:emit/nfse_sped:CNPJ/text()')
    cpf_prest  = pegar_valor('//nfse_sped:emit//nfse_sped:CPF/text()')

    # TOMADOR
    cnpj_tom = pegar_valor('//nfse_sped:toma/nfse_sped:CNPJ/text()')
    cpf_tom  = pegar_valor('//nfse_sped:toma/nfse_sped:CPF/text()')

    aliq = buscar_num('//nfse_sped:valores/nfse_sped:pAliqAplic/text()')
    ret_cod = pegar_valor('//nfse_sped:tribMun/nfse_sped:tpRetISSQN/text()')

    return {
        "Numero":              buscar_int('//nfse_sped:nNFSe/text()'),
        "Data":                buscar_data('//nfse_sped:dCompet/text()'),
        "CNPJ/CPF Prestador":  formatar_cnpj_cpf(cnpj_prest or cpf_prest),
        "Tipo Doc Prestador":  _tipo_documento(cnpj_prest, cpf_prest),
        "Razão Prestador":     pegar_valor('//nfse_sped:emit/nfse_sped:xNome/text()'),
        "CNPJ/CPF Tomador":    formatar_cnpj_cpf(cnpj_tom or cpf_tom),
        "Tipo Doc Tomador":    _tipo_documento(cnpj_tom, cpf_tom),
        "Razão Tomador":       pegar_valor('//nfse_sped:toma/nfse_sped:xNome/text()'),
        "Valor Total":         buscar_num('//nfse_sped:valores/nfse_sped:vServPrest/nfse_sped:vServ/text()'),
        "Aliq ISSQN":          aliq / 100 if aliq else 0.0,
        "ISSQN":               buscar_num('//nfse_sped:valores/nfse_sped:vISSQN/text()'),
        "ISSQN Retido":        "Sim" if ret_cod == "2" else "Não",
        "IRRF":                buscar_num('//nfse_sped:tribFed/nfse_sped:vRetIRRF/text()'),
        "CPP":                 buscar_num('//nfse_sped:tribFed/nfse_sped:vRetCP/text()'),
        "CSRF":                buscar_num('//nfse_sped:tribFed/nfse_sped:vRetCSLL/text()'),
        "Valor Líquido":       buscar_num('//nfse_sped:valores/nfse_sped:vLiq/text()'),
        "Chave":               chave_nfse,
    }
