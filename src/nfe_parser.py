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

    id_emitente = pegar_valor('//nfe_sped:emit/nfe_sped:CNPJ/text()')
    emitente = pegar_valor('//nfe_sped:emit/nfe_sped:xNome/text()')
    uf_emitente = pegar_valor('//nfe_sped:emit/nfe_sped:UF/text()')

    id_destinatario = pegar_valor('//nfe_sped:dest/nfe_sped:CNPJ/text()') or pegar_valor('//nfe_sped:dest/nfe_sped:CPF/text()')
    destinatario = pegar_valor('//nfe_sped:dest/nfe_sped:xNome/text()')
    uf_destinatario = pegar_valor('//nfe_sped:dest/nfe_sped:UF/text()')

    valor_total = buscar_int('//nfe_sped:total/nfe_sped:vNF/text()')
    total_produtos = buscar_int('//nfe_sped:total/nfe_sped:vProd/text()')
    frete = buscar_int('//nfe_sped:total/nfe_sped:vFrete/text()')
    ipi = buscar_int('//nfe_sped:total/nfe_sped:vIPI/text()')
    seguros = buscar_int('//nfe_sped:total/nfe_sped:vSeg/text()')
    descontos = buscar_int('//nfe_sped:total/nfe_sped:vDesc/text()')

    dados_nfe = {

        "Numero": numero_nfe,
        "Modelo NF": modelo_nf,
        "Data": data_emissao,
        "CNPJ do Emitente": id_emitente,
        "Razão-Emitente": emitente,
        "UF Emitente": uf_emitente,
        "CNPJ/CPF Destinário": id_destinatario,
        "Destinatário": destinatario,
        "UF Destinatario": uf_destinatario,
        "Produto": total_produtos,
        "Frete": frete,
        "IPI": ipi,
        "Seguros": seguros,
        "Descontos": descontos,
        "Valor Total": valor_total
    }

    return dados_nfe