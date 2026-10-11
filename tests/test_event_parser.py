from src.event_parser import extrair_cancelamento

XML_CANCELAMENTO = """<?xml version="1.0" encoding="UTF-8"?>
<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <evento>
    <infEvento>
      <CNPJ>14200166000187</CNPJ>
      <chNFe>35200714200166000187550010000000046550010466</chNFe>
      <dhEvento>2020-07-16T14:00:00-03:00</dhEvento>
      <tpEvento>110111</tpEvento>
      <detEvento>
        <nProt>135200000000001</nProt>
        <xJust>Erro na emissao do documento fiscal original</xJust>
      </detEvento>
    </infEvento>
  </evento>
</procEventoNFe>
"""


def test_extrai_cancelamento(parse_xml):
    dados = extrair_cancelamento(parse_xml(XML_CANCELAMENTO))

    assert dados is not None
    assert dados["Chave Vinculada"] == "35200714200166000187550010000000046550010466"
    assert str(dados["Data do Evento"]) == "2020-07-16"
    assert dados["Status"] == "Cancelamento"
    assert dados["Protocolo Evento"] == "135200000000001"
    assert dados["CNPJ Emitente"] == "14.200.166/0001-87"
    assert dados["Tipo Doc Emitente"] == "CNPJ"
    assert dados["Justificativa"] == "Erro na emissao do documento fiscal original"


def test_evento_diferente_de_cancelamento_retorna_none(parse_xml):
    xml_outro_evento = XML_CANCELAMENTO.replace("<tpEvento>110111</tpEvento>", "<tpEvento>110110</tpEvento>")
    assert extrair_cancelamento(parse_xml(xml_outro_evento)) is None
