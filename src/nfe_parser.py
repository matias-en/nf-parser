from src.processor import limpar_num, limpar_int, formatar_data

nfe_nacional = {'nfe_sped': 'http://www.portalfiscal.inf.br/nfe'}


def extrair_dados(arvore):
    inf_nfe_list = arvore.xpath('./nfe_sped:NFe/nfe_sped:infNFe', namespaces=nfe_nacional)
    if not inf_nfe_list:
        return {"cabecalho": {}, "produtos": []}

    node = inf_nfe_list[0]

    # FUNÇÕES PADRÃO (Restauradas e mantidas conforme seu código original)
    def pegar_valor(xpath_str):
        res = node.xpath(xpath_str, namespaces=nfe_nacional)
        return res[0] if res else ""

    def buscar_num(xpath_str):
        return limpar_num(node.xpath(xpath_str, namespaces=nfe_nacional))

    def buscar_int(xpath_str):
        return limpar_int(node.xpath(xpath_str, namespaces=nfe_nacional))

    def buscar_data(xpath_str):
        return formatar_data(node.xpath(xpath_str, namespaces=nfe_nacional))

    chave_nfebruta = pegar_valor('./@Id')
    chave_nfe = "".join(filter(str.isdigit, chave_nfebruta))
    numero_nfe = buscar_int('./nfe_sped:ide/nfe_sped:nNF/text()')
    data_emissao = buscar_data('./nfe_sped:ide/nfe_sped:dhEmi/text()')

    cabecalho = {
        "Numero": numero_nfe,
        "Modelo NF": buscar_int('./nfe_sped:ide/nfe_sped:mod/text()'),
        "Data": data_emissao,
        "CNPJ Emitente": pegar_valor('./nfe_sped:emit/nfe_sped:CNPJ/text()') or pegar_valor(
            './nfe_sped:emit/nfe_sped:CPF/text()'),
        "Razão Emitente": pegar_valor('./nfe_sped:emit/nfe_sped:xNome/text()'),
        "Operação": pegar_valor('./nfe_sped:ide/nfe_sped:natOp/text()'),
        "CNPJ Destinatário": pegar_valor('./nfe_sped:dest/nfe_sped:CNPJ/text()') or pegar_valor(
            './nfe_sped:dest/nfe_sped:CPF/text()'),
        "Razão Destinatário": pegar_valor('./nfe_sped:dest/nfe_sped:xNome/text()'),
        "Valor Total NF": buscar_num('./nfe_sped:total/nfe_sped:ICMSTot/nfe_sped:vNF/text()'),
        "BC ICMS": buscar_num('./nfe_sped:total/nfe_sped:ICMSTot/nfe_sped:vBC/text()'),
        "ICMS": buscar_num('./nfe_sped:total/nfe_sped:ICMSTot/nfe_sped:vICMS/text()'),
        "IPI": buscar_num('./nfe_sped:total/nfe_sped:ICMSTot/nfe_sped:vIPI/text()'),
        "PIS": buscar_num('./nfe_sped:total/nfe_sped:ICMSTot/nfe_sped:vPIS/text()'),
        "COFINS": buscar_num('./nfe_sped:total/nfe_sped:ICMSTot/nfe_sped:vCOFINS/text()'),
        "Chave": chave_nfe
    }

    # 3. EXTRAÇÃO DE PRODUTOS (COM CFOP NUMÉRICO E SEM CPROD)
    itens_xml = node.xpath('./nfe_sped:det', namespaces=nfe_nacional)
    lista_produtos = []

    for item in itens_xml:
        def p_val_item(xpath_rel):
            res = item.xpath(xpath_rel, namespaces=nfe_nacional)
            return res[0] if res else ""

        def b_num_item(xpath_rel):
            return limpar_num(item.xpath(xpath_rel, namespaces=nfe_nacional))

        def b_int_item(xpath_rel):
            return limpar_int(item.xpath(xpath_rel, namespaces=nfe_nacional))

        lista_produtos.append({
            "Chave": chave_nfe,
            "Numero": numero_nfe,
            "Data": data_emissao,
            "nItem": p_val_item('./@nItem'),
            # cProd removido
            "xProd": p_val_item('./nfe_sped:prod/nfe_sped:xProd/text()'),
            "NCM": p_val_item('./nfe_sped:prod/nfe_sped:NCM/text()'),
            "CFOP": b_int_item('./nfe_sped:prod/nfe_sped:CFOP/text()'),
            "uCom": p_val_item('./nfe_sped:prod/nfe_sped:uCom/text()'),
            "qCom": b_num_item('./nfe_sped:prod/nfe_sped:qCom/text()'),
            "vUnCom": b_num_item('./nfe_sped:prod/nfe_sped:vUnCom/text()'),
            "vProd": b_num_item('./nfe_sped:prod/nfe_sped:vProd/text()'),
            "vTotTrib": b_num_item('./nfe_sped:imposto/nfe_sped:vTotTrib/text()'),
            "vICMS": b_num_item('.//nfe_sped:ICMS//nfe_sped:vICMS/text()'),
            "vPIS": b_num_item('.//nfe_sped:PIS//nfe_sped:vPIS/text()'),
            "vCOFINS": b_num_item('.//nfe_sped:COFINS//nfe_sped:vCOFINS/text()'),
            "vIPI": b_num_item('.//nfe_sped:IPI//nfe_sped:vIPI/text()')
        })

    return {
        "cabecalho": cabecalho,
        "produtos": lista_produtos
    }