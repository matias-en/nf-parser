from src.processor import limpar_num, limpar_int, formatar_data, formatar_cnpj_cpf

nfse_abraf = {'nfse_abraf': 'http://www.abrasf.org.br/nfse.xsd'}

def _tipo_documento(doc_cnpj: str, doc_cpf: str) -> str:
    if doc_cnpj:
        return "CNPJ"
    if doc_cpf:
        return "CPF"
    return ""

def extrair_dados(arvore):

    def pegar_valor(xpath_str):
        res = arvore.xpath(xpath_str, namespaces=nfse_abraf)
        return res[0] if res else ""

    def buscar_num(xpath_str):
        return limpar_num(arvore.xpath(xpath_str, namespaces=nfse_abraf))

    def buscar_int(xpath_str):
        return limpar_int(arvore.xpath(xpath_str, namespaces=nfse_abraf))

    def buscar_data(xpath_str):
        return formatar_data(arvore.xpath(xpath_str, namespaces=nfse_abraf))

    # PRESTADOR
    cnpj_prest = pegar_valor('//nfse_abraf:Prestador/nfse_abraf:CpfCnpj/nfse_abraf:Cnpj/text()')
    cpf_prest  = pegar_valor('//nfse_abraf:Prestador/nfse_abraf:CpfCnpj/nfse_abraf:CPF/text()')

    # TOMADOR
    cnpj_tom = pegar_valor('//nfse_abraf:TomadorServico//nfse_abraf:Cnpj/text()')
    cpf_tom  = pegar_valor('//nfse_abraf:TomadorServico//nfse_abraf:Cpf/text()')

    aliq    = buscar_num('//nfse_abraf:ValoresNfse/nfse_abraf:Aliquota/text()')
    ret_cod = pegar_valor('//nfse_abraf:Servico/nfse_abraf:IssRetido/text()')

    return {
        "Numero":              buscar_int('//nfse_abraf:InfNfse/nfse_abraf:Numero/text()'),
        "Data":                buscar_data('//nfse_abraf:InfDeclaracaoPrestacaoServico/nfse_abraf:Competencia/text()'),
        "CNPJ/CPF Prestador":  formatar_cnpj_cpf(cnpj_prest or cpf_prest),
        "Tipo Doc Prestador":  _tipo_documento(cnpj_prest, cpf_prest),
        "Razão Prestador":     pegar_valor('//nfse_abraf:PrestadorServico/nfse_abraf:RazaoSocial/text()'),
        "CNPJ/CPF Tomador":    formatar_cnpj_cpf(cnpj_tom or cpf_tom),
        "Tipo Doc Tomador":    _tipo_documento(cnpj_tom, cpf_tom),
        "Razão Tomador":       pegar_valor('//nfse_abraf:TomadorServico/nfse_abraf:RazaoSocial/text()'),
        "Valor Total":         buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorServicos/text()'),
        "Aliq ISSQN":          aliq / 100 if aliq else 0.0,
        "ISSQN":               buscar_num('//nfse_abraf:ValoresNfse/nfse_abraf:ValorIss/text()'),
        "ISSQN Retido":        "Sim" if ret_cod == "1" else "Não",
        "IRRF Retido":         buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorIr/text()'),
        "CPP Retido":          buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorCp/text()'),
        "CSLL Retido":         buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorCsll/text()'),
        "COFINS Retido":       buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorCofins/text()'),
        "PIS Retido":          buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorPis/text()'),
        "Valor Líquido":       buscar_num('//nfse_abraf:ValoresNfse/nfse_abraf:ValorLiquidoNfse/text()'),
    }
