from src.nfse_abrasf_parser import extrair_dados

XML_ABRASF = """<?xml version="1.0" encoding="UTF-8"?>
<CompNfse xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Nfse>
    <InfNfse>
      <Numero>987</Numero>
      <DeclaracaoPrestacaoServico>
        <InfDeclaracaoPrestacaoServico>
          <Competencia>2019-11-05</Competencia>
          <Servico>
            <Valores>
              <ValorServicos>2000,00</ValorServicos>
              <ValorIr>20,00</ValorIr>
              <ValorCp>10,00</ValorCp>
              <ValorCsll>6,00</ValorCsll>
              <ValorCofins>6,00</ValorCofins>
              <ValorPis>1,30</ValorPis>
            </Valores>
            <IssRetido>1</IssRetido>
          </Servico>
          <PrestadorServico>
            <RazaoSocial>Prestador ABRASF Teste</RazaoSocial>
          </PrestadorServico>
          <Prestador>
            <CpfCnpj><Cnpj>14200166000187</Cnpj></CpfCnpj>
          </Prestador>
          <TomadorServico>
            <RazaoSocial>Tomador ABRASF Teste</RazaoSocial>
            <IdentificacaoTomador>
              <CpfCnpj><Cnpj>11222333000181</Cnpj></CpfCnpj>
            </IdentificacaoTomador>
          </TomadorServico>
        </InfDeclaracaoPrestacaoServico>
      </DeclaracaoPrestacaoServico>
      <ValoresNfse>
        <Aliquota>3,00</Aliquota>
        <ValorIss>60,00</ValorIss>
        <ValorLiquidoNfse>1940,00</ValorLiquidoNfse>
      </ValoresNfse>
    </InfNfse>
  </Nfse>
</CompNfse>
"""


def test_extrai_dados_abrasf(parse_xml):
    dados = extrair_dados(parse_xml(XML_ABRASF))

    assert dados["Numero"] == 987
    assert str(dados["Data"]) == "2019-11-05"
    assert dados["CNPJ/CPF Prestador"] == "14.200.166/0001-87"
    assert dados["Tipo Doc Prestador"] == "CNPJ"
    assert dados["Razão Prestador"] == "Prestador ABRASF Teste"
    assert dados["CNPJ/CPF Tomador"] == "11.222.333/0001-81"
    assert dados["Razão Tomador"] == "Tomador ABRASF Teste"
    assert dados["Valor Total"] == 2000.00
    assert dados["Aliq ISSQN"] == 0.03
    assert dados["ISSQN"] == 60.00
    assert dados["ISSQN Retido"] == "Sim"
    assert dados["IRRF Retido"] == 20.00
    assert dados["CPP Retido"] == 10.00
    assert dados["CSLL Retido"] == 6.00
    assert dados["COFINS Retido"] == 6.00
    assert dados["PIS Retido"] == 1.30
    assert dados["Valor Líquido"] == 1940.00


def test_iss_nao_retido(parse_xml):
    xml_sem_retencao = XML_ABRASF.replace("<IssRetido>1</IssRetido>", "<IssRetido>2</IssRetido>")
    dados = extrair_dados(parse_xml(xml_sem_retencao))
    assert dados["ISSQN Retido"] == "Não"
