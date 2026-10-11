from src.cte_parser import extrair_dados

XML_CTE = """<?xml version="1.0" encoding="UTF-8"?>
<cteProc xmlns="http://www.portalfiscal.inf.br/cte">
  <CTe>
    <infCte Id="CTe35200714200166000187570010000000015550010465">
      <ide>
        <nCT>15</nCT>
        <CFOP>6353</CFOP>
        <dhEmi>2020-08-01T09:00:00-03:00</dhEmi>
        <natOp>PRESTACAO DE SERVICO DE TRANSPORTE</natOp>
      </ide>
      <emit>
        <CNPJ>14200166000187</CNPJ>
        <xNome>Transportadora Teste LTDA</xNome>
      </emit>
      <rem>
        <CNPJ>22333444000155</CNPJ>
        <xNome>Remetente Teste</xNome>
      </rem>
      <dest>
        <CNPJ>11222333000181</CNPJ>
        <xNome>Destinatario Teste</xNome>
      </dest>
      <vPrest>
        <vTPrest>150,00</vTPrest>
      </vPrest>
      <imp>
        <ICMS>
          <ICMS00><vICMS>18,00</vICMS></ICMS00>
        </ICMS>
      </imp>
      <infCTeNorm>
        <infDoc>
          <infNFe><chave>35200714200166000187550010000000046550010466</chave></infNFe>
        </infDoc>
      </infCTeNorm>
    </infCte>
  </CTe>
</cteProc>
"""


def test_extrai_dados_do_cte(parse_xml):
    dados = extrair_dados(parse_xml(XML_CTE))

    assert dados["Chave CTe"] == "35200714200166000187570010000000015550010465"
    assert dados["Numero"] == 15
    assert dados["CFOP"] == 6353
    assert str(dados["Data"]) == "2020-08-01"
    assert dados["CNPJ Transportadora"] == "14.200.166/0001-87"
    assert dados["Transportadora"] == "Transportadora Teste LTDA"
    assert dados["Doc Remetente"] == "22.333.444/0001-55"
    assert dados["Remetente"] == "Remetente Teste"
    assert dados["Doc Destinatário"] == "11.222.333/0001-81"
    assert dados["Destinatário"] == "Destinatario Teste"
    assert dados["Valor Frete"] == 150.00
    assert dados["ICMS CTe"] == 18.00
    assert dados["NFe Referenciada"] == "35200714200166000187550010000000046550010466"


def test_documento_sem_infcte_retorna_none(parse_xml):
    arvore = parse_xml('<cteProc xmlns="http://www.portalfiscal.inf.br/cte"></cteProc>')
    assert extrair_dados(arvore) is None
