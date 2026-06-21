from src.processor import limpar_num, limpar_int, formatar_data

nfse_abraf = {'nfse_abraf': 'http://www.abrasf.org.br/nfse.xsd'}


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

    #chave_bruta = pegar_valor('//nfse_abraf:infNFSe/@Id')
    #chave_nfse = "".join(filter(str.isdigit, chave_bruta))

    numero_nfse = buscar_int('//nfse_abraf:InfNfse/nfse_abraf:Numero/text()')
    data_final = buscar_data('//nfse_abraf:InfDeclaracaoPrestacaoServico/nfse_abraf:Competencia/text()')

    doc_p = pegar_valor('//nfse_abraf:Prestador/nfse_abraf:CpfCnpj/nfse_abraf:Cnpj/text()') or pegar_valor(
        '//nfse_abraf:Prestador/nfse_abraf:CpfCnpj/nfse_abraf:CPF/text()')
    nome_p = pegar_valor('//nfse_abraf:PrestadorServico/nfse_abraf:RazaoSocial/text()')

    doc_t = pegar_valor('//nfse_abraf:TomadorServico//nfse_abraf:Cnpj/text()') or pegar_valor('//nfse_abraf:TomadorServico//nfse_abraf:Cpf/text()')
    nome_t = pegar_valor('//nfse_abraf:TomadorServico/nfse_abraf:RazaoSocial/text()')

    v_total = buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorServicos/text()')
    v_issqn = buscar_num('//nfse_abraf:ValoresNfse/nfse_abraf:ValorIss/text()')
    aliq = buscar_num('//nfse_abraf:ValoresNfse/nfse_abraf:Aliquota/text()') / 100
    v_liq = buscar_num('//nfse_abraf:ValoresNfse/nfse_abraf:ValorLiquidoNfse/text()')
    r_irrf = buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorIr/text()')
    r_cpp = buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorCp/text()')
    r_csll = buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorCsll/text()')
    r_pis = buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorPis/text()')
    r_cofins = buscar_num('//nfse_abraf:Servico/nfse_abraf:Valores/nfse_abraf:ValorCofins/text()')

    ret_cod = pegar_valor('//nfse_abraf:Servico/nfse_abraf:IssRetido/text()')
    ret_texto = "Sim" if ret_cod == "1" else "Não"

    dados_nfseabraf = {

        "Numero": numero_nfse,
        "Data": data_final,
        "CNPJ/CPF Prestador": doc_p,
        "Razão Prestador": nome_p,
        "CNPJ/CPF Tomador": doc_t,
        "Razão Tomador": nome_t,
        "Valor Total": v_total,
        "Aliq ISSQN": aliq,
        "ISSQN": v_issqn,
        "ISSQN Retido": ret_texto,
        "IRRF Retido": r_irrf,
        "CPP Retido": r_cpp,
        "CSLL Retido": r_csll,
        "COFINS Retido": r_cofins,
        "PIS Retido": r_pis,
        "Valor Líquido": v_liq,

    }

    return dados_nfseabraf