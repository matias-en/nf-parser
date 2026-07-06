from src.processor import formatar_data, formatar_cnpj_cpf

nfe_nacional = {'nfe_sped': 'http://www.portalfiscal.inf.br/nfe'}


def extrair_cancelamento(arvore):

    def pegar_valor(xpath_str):
        res = arvore.xpath(xpath_str, namespaces=nfe_nacional)
        return res[0] if res else ""

    def buscar_data(xpath_str):
        return formatar_data(arvore.xpath(xpath_str, namespaces=nfe_nacional))

    tipo_evento = pegar_valor('//nfe_sped:tpEvento/text()')

    if tipo_evento == "110111":
        cnpj_emit_bruto = pegar_valor('//nfe_sped:infEvento/nfe_sped:CNPJ/text()')
        cpf_emit_bruto  = pegar_valor('//nfe_sped:infEvento/nfe_sped:CPF/text()')

        return {
            "Chave Vinculada":  pegar_valor('//nfe_sped:chNFe/text()'),
            "Data do Evento":   buscar_data('//nfe_sped:dhEvento/text()'),
            "Status":           "Cancelamento",
            "Protocolo Evento": pegar_valor('//nfe_sped:detEvento/nfe_sped:nProt/text()'),
            "CNPJ Emitente":    formatar_cnpj_cpf(cnpj_emit_bruto or cpf_emit_bruto),
            "Tipo Doc Emitente": "CNPJ" if cnpj_emit_bruto else ("CPF" if cpf_emit_bruto else ""),
            "Justificativa":    pegar_valor('//nfe_sped:detEvento/nfe_sped:xJust/text()'),
        }

    return None
