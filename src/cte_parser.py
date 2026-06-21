from src.processor import limpar_num, limpar_int, formatar_data

# Namespace padrão para CTe 4.00
cte_ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}


def extrair_dados(arvore):
    # ✅ MUDANÇA: Usamos './/' para encontrar o infCte mesmo dentro do envelope cteProc
    inf_cte_list = arvore.xpath('.//cte:infCte', namespaces=cte_ns)

    # ✅ Retornamos None para o main ignorar e não gerar linha em branco
    if not inf_cte_list:
        return None

    node = inf_cte_list[0]

    # Funções auxiliares originais mantidas (relativas ao node)
    def p_val(xpath_str):
        res = node.xpath(xpath_str, namespaces=cte_ns)
        return res[0] if res else ""

    def b_num(xpath_str):
        return limpar_num(node.xpath(xpath_str, namespaces=cte_ns))

    def b_int(xpath_str):
        return limpar_int(node.xpath(xpath_str, namespaces=cte_ns))

    def b_data(xpath_str):
        return formatar_data(node.xpath(xpath_str, namespaces=cte_ns))

    # IDENTIFICAÇÃO
    chave_bruta = p_val('./@Id')
    chave_cte = "".join(filter(str.isdigit, chave_bruta))

    # ✅ CORREÇÃO: Chamada da função corrigida de p_valor para p_val e CFOP como int
    cfop_cte = b_int('./cte:ide/cte:CFOP/text()')

    numero_cte = b_int('./cte:ide/cte:nCT/text()')
    data_emissao = b_data('./cte:ide/cte:dhEmi/text()')
    natureza_op = p_val('./cte:ide/cte:natOp/text()')

    # TRANSPORTADORA (Emitente)
    cnpj_transp = p_val('./cte:emit/cte:CNPJ/text()')
    nome_transp = p_val('./cte:emit/cte:xNome/text()')

    # REMETENTE
    doc_rem = p_val('./cte:rem/cte:CNPJ/text()') or p_val('./cte:rem/cte:CPF/text()')
    nome_rem = p_val('./cte:rem/cte:xNome/text()')

    # DESTINATÁRIO
    doc_dest = p_val('./cte:dest/cte:CNPJ/text()') or p_val('./cte:dest/cte:CPF/text()')
    nome_dest = p_val('./cte:dest/cte:xNome/text()')

    # VALORES
    valor_frete = b_num('./cte:vPrest/cte:vTPrest/text()')
    valor_icms = b_num('./cte:imp/cte:ICMS/*/cte:vICMS/text()')

    # DOCUMENTO ORIGINÁRIO
    chave_nfe_ref = p_val('./cte:infCTeNorm/cte:infDoc/cte:infNFe/cte:chave/text()')

    return {
        "Chave CTe": chave_cte,
        "Numero": numero_cte,
        "CFOP": cfop_cte,
        "Data": data_emissao,
        "Operação": natureza_op,
        "CNPJ Transportadora": cnpj_transp,
        "Transportadora": nome_transp,
        "Doc Remetente": doc_rem,
        "Remetente": nome_rem,
        "Doc Destinatário": doc_dest,
        "Destinatário": nome_dest,
        "Valor Frete": valor_frete,
        "ICMS CTe": valor_icms,
        "NFe Referenciada": chave_nfe_ref
    }