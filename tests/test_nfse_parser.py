from src.nfse_parser import extrair_dados

XML_NFSE = """<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe Id="NFS35200714200166000187000000000000001000000001">
    <nNFSe>1</nNFSe>
    <DPS>
      <infDPS>
        <dCompet>2021-03-10</dCompet>
        <emit>
          <CNPJ>14200166000187</CNPJ>
          <xNome>Prestador de Servico Teste</xNome>
        </emit>
        <toma>
          <CNPJ>11222333000181</CNPJ>
          <xNome>Tomador Teste</xNome>
        </toma>
        <serv>
          <locPrest><cLocPrestacao>3550308</cLocPrestacao></locPrest>
          <cServ>
            <cTribNac>040301</cTribNac>
            <xDescServ>Servico de teste</xDescServ>
          </cServ>
        </serv>
        <valores>
          <vServPrest><vServ>1000,00</vServ></vServPrest>
          <pAliqAplic>5,00</pAliqAplic>
          <vISSQN>50,00</vISSQN>
          <vLiq>950,00</vLiq>
        </valores>
        <tribMun>
          <tpRetISSQN>2</tpRetISSQN>
        </tribMun>
        <tribFed>
          <vRetIRRF>10,00</vRetIRRF>
          <vRetCP>5,00</vRetCP>
          <vRetCSLL>3,00</vRetCSLL>
        </tribFed>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
"""


def test_extrai_dados_da_nfse(parse_xml):
    arvore = parse_xml(XML_NFSE)
    dados = extrair_dados(arvore)

    assert dados["Chave"] == "35200714200166000187000000000000001000000001"
    assert dados["Numero"] == 1
    assert str(dados["Data"]) == "2021-03-10"
    assert dados["CNPJ/CPF Prestador"] == "14.200.166/0001-87"
    assert dados["Razão Prestador"] == "Prestador de Servico Teste"
    assert dados["CNPJ/CPF Tomador"] == "11.222.333/0001-81"
    assert dados["Razão Tomador"] == "Tomador Teste"
    assert dados["Valor Total"] == 1000.00
    assert dados["Aliq ISSQN"] == 0.05
    assert dados["ISSQN"] == 50.00
    assert dados["ISSQN Retido"] == "Sim"
    assert dados["IRRF"] == 10.00
    assert dados["CPP"] == 5.00
    assert dados["CSRF"] == 3.00
    assert dados["Valor Líquido"] == 950.00
    assert dados["Cód. Serviço"] == "040301"


def test_codigo_tributacao_nacional_ausente_retorna_vazio(parse_xml):
    xml_sem_cservi = XML_NFSE.replace(
        "<cServ>\n            <cTribNac>040301</cTribNac>\n            <xDescServ>Servico de teste</xDescServ>\n          </cServ>",
        "",
    )
    dados = extrair_dados(parse_xml(xml_sem_cservi))
    assert dados["Cód. Serviço"] == ""


def test_issqn_nao_retido_quando_codigo_diferente_de_2(parse_xml):
    xml_sem_retencao = XML_NFSE.replace("<tpRetISSQN>2</tpRetISSQN>", "<tpRetISSQN>1</tpRetISSQN>")
    dados = extrair_dados(parse_xml(xml_sem_retencao))
    assert dados["ISSQN Retido"] == "Não"


def test_prestador_pessoa_fisica_usa_cpf(parse_xml):
    xml_cpf = XML_NFSE.replace(
        "<emit>\n          <CNPJ>14200166000187</CNPJ>",
        "<emit>\n          <CPF>12345678909</CPF>",
    )
    dados = extrair_dados(parse_xml(xml_cpf))
    assert dados["Tipo Doc Prestador"] == "CPF"
    assert dados["CNPJ/CPF Prestador"] == "123.456.789-09"
