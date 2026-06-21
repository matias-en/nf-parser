from src.processor import limpar_num, limpar_int, formatar_data

# O namespace é o mesmo da NFe Nacional
nfe_nacional = {'nfe_sped': 'http://www.portalfiscal.inf.br/nfe'}


def extrair_cancelamento(arvore):
    def pegar_valor(xpath_str):
        res = arvore.xpath(xpath_str, namespaces=nfe_nacional)
        return res[0] if res else ""

    def buscar_data(xpath_str):
        return formatar_data(arvore.xpath(xpath_str, namespaces=nfe_nacional))

    # 1. Verificamos se o tipo do evento é Cancelamento (110111)
    tipo_evento = pegar_valor('//nfe_sped:tpEvento/text()')

    if tipo_evento == "110111":
        # 2. Extração dos dados baseada no seu XML de exemplo
        
        chave_vinculada = pegar_valor('//nfe_sped:chNFe/text()')
        data_evento = buscar_data('//nfe_sped:dhEvento/text()')
        justificativa = pegar_valor('//nfe_sped:detEvento/nfe_sped:xJust/text()')
        protocolo = pegar_valor('//nfe_sped:detEvento/nfe_sped:nProt/text()')
        cnpj_emitente = pegar_valor('//nfe_sped:infEvento/nfe_sped:CNPJ/text()')

        return {
            "Chave Vinculada": chave_vinculada,
            "Data do Evento": data_evento,
            "Status": "Cancelamento",
            "Protocolo Evento": protocolo,
            "CNPJ Emitente": cnpj_emitente,
            "Justificativa": justificativa
        }

    return None  # Ignora se for outro tipo de evento (ex: Carta de Correção)