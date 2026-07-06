from src.processor import limpar_num, limpar_int, formatar_data, formatar_cnpj_cpf

cte_ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}


def _tipo_documento(doc_cnpj: str, doc_cpf: str) -> str:
    if doc_cnpj:
        return "CNPJ"
    if doc_cpf:
        return "CPF"
    return ""


def extrair_dados(arvore):
    inf_cte_list = arvore.xpath('.//cte:infCte', namespaces=cte_ns)
    if not inf_cte_list:
        return None

    node = inf_cte_list[0]

    def p_val(xpath_str):
        res = node.xpath(xpath_str, namespaces=cte_ns)
        return res[0] if res else ""

    def b_num(xpath_str):
        return limpar_num(node.xpath(xpath_str, namespaces=cte_ns))

    def b_int(xpath_str):
        return limpar_int(node.xpath(xpath_str, namespaces=cte_ns))

    def b_data(xpath_str):
        return formatar_data(node.xpath(xpath_str, namespaces=cte_ns))

    chave_cte = "".join(filter(str.isdigit, p_val('./@Id')))

    # TRANSPORTADORA — sempre CNPJ
    cnpj_transp = p_val('./cte:emit/cte:CNPJ/text()')
    cpf_transp  = p_val('./cte:emit/cte:CPF/text()')

    # REMETENTE
    cnpj_rem = p_val('./cte:rem/cte:CNPJ/text()')
    cpf_rem  = p_val('./cte:rem/cte:CPF/text()')

    # DESTINATÁRIO (adquirente do frete)
    cnpj_dest = p_val('./cte:dest/cte:CNPJ/text()')
    cpf_dest  = p_val('./cte:dest/cte:CPF/text()')

    return {
        "Chave CTe":              chave_cte,
        "Numero":                 b_int('./cte:ide/cte:nCT/text()'),
        "CFOP":                   b_int('./cte:ide/cte:CFOP/text()'),
        "Data":                   b_data('./cte:ide/cte:dhEmi/text()'),
        "Operação":               p_val('./cte:ide/cte:natOp/text()'),
        "CNPJ Transportadora":    formatar_cnpj_cpf(cnpj_transp or cpf_transp),
        "Tipo Doc Transportadora": _tipo_documento(cnpj_transp, cpf_transp),
        "Transportadora":         p_val('./cte:emit/cte:xNome/text()'),
        "Doc Remetente":          formatar_cnpj_cpf(cnpj_rem or cpf_rem),
        "Tipo Doc Remetente":     _tipo_documento(cnpj_rem, cpf_rem),
        "Remetente":              p_val('./cte:rem/cte:xNome/text()'),
        "Doc Destinatário":       formatar_cnpj_cpf(cnpj_dest or cpf_dest),
        "Tipo Doc Destinatário":  _tipo_documento(cnpj_dest, cpf_dest),
        "Destinatário":           p_val('./cte:dest/cte:xNome/text()'),
        "Valor Frete":            b_num('./cte:vPrest/cte:vTPrest/text()'),
        "ICMS CTe":               b_num('./cte:imp/cte:ICMS/*/cte:vICMS/text()'),
        "NFe Referenciada":       p_val('./cte:infCTeNorm/cte:infDoc/cte:infNFe/cte:chave/text()'),
    }