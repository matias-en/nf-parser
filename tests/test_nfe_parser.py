from src.nfe_parser import extrair_dados

XML_NFE = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe Id="NFe35200714200166000187550010000000046550010466" versao="4.00">
      <ide>
        <nNF>46</nNF>
        <mod>55</mod>
        <dhEmi>2020-07-15T10:00:00-03:00</dhEmi>
        <natOp>VENDA DE MERCADORIA</natOp>
      </ide>
      <emit>
        <CNPJ>14200166000187</CNPJ>
        <xNome>Empresa Emitente Teste LTDA</xNome>
        <enderEmit><UF>SP</UF></enderEmit>
      </emit>
      <dest>
        <CNPJ>11222333000181</CNPJ>
        <xNome>Cliente Destinatario Teste</xNome>
        <enderDest><UF>RJ</UF></enderDest>
      </dest>
      <det nItem="1">
        <prod>
          <xProd>Produto de Teste A</xProd>
          <NCM>12345678</NCM>
          <CFOP>5102</CFOP>
          <uCom>UN</uCom>
          <qCom>2,0000</qCom>
          <vUnCom>10,00</vUnCom>
          <vProd>20,00</vProd>
        </prod>
        <imposto>
          <vTotTrib>3,00</vTotTrib>
          <ICMS><ICMS00><CST>00</CST><vICMS>1,50</vICMS></ICMS00></ICMS>
          <PIS><PISAliq><CST>01</CST><vPIS>0,30</vPIS></PISAliq></PIS>
          <COFINS><COFINSAliq><CST>01</CST><vCOFINS>1,20</vCOFINS></COFINSAliq></COFINS>
          <IPI><IPITrib><vIPI>0,00</vIPI></IPITrib></IPI>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vBC>20,00</vBC>
          <vICMS>1,50</vICMS>
          <vIPI>0,00</vIPI>
          <vPIS>0,30</vPIS>
          <vCOFINS>1,20</vCOFINS>
          <vProd>20,00</vProd>
          <vNF>20,00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""


def test_extrai_cabecalho_da_nfe(parse_xml):
    arvore = parse_xml(XML_NFE)
    dados = extrair_dados(arvore)
    cab = dados["cabecalho"]

    assert cab["Chave"] == "35200714200166000187550010000000046550010466"
    assert cab["Numero"] == 46
    assert cab["Modelo NF"] == 55
    assert str(cab["Data"]) == "2020-07-15"
    assert cab["CNPJ Emitente"] == "14.200.166/0001-87"
    assert cab["Tipo Doc Emitente"] == "CNPJ"
    assert cab["Razão Emitente"] == "Empresa Emitente Teste LTDA"
    assert cab["UF Emitente"] == "SP"
    assert cab["CNPJ Destinatário"] == "11.222.333/0001-81"
    assert cab["UF Destinatário"] == "RJ"
    assert cab["Valor Total NF"] == 20.00
    assert cab["Valor Total Produtos"] == 20.00
    assert cab["ICMS"] == 1.50


def test_extrai_produtos_da_nfe(parse_xml):
    arvore = parse_xml(XML_NFE)
    dados = extrair_dados(arvore)
    produtos = dados["produtos"]

    assert len(produtos) == 1
    item = produtos[0]
    assert item["xProd"] == "Produto de Teste A"
    assert item["NCM"] == "12345678"
    assert item["CFOP"] == 5102
    assert item["qCom"] == 2.0
    assert item["vProd"] == 20.00
    assert item["CST ICMS"] == "00"
    assert item["vICMS"] == 1.50
    assert item["vPIS"] == 0.30
    assert item["vCOFINS"] == 1.20
    assert item["Chave"] == dados["cabecalho"]["Chave"]
    assert item["Numero"] == 46


def test_documento_sem_infnfe_retorna_estrutura_vazia(parse_xml):
    arvore = parse_xml('<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"></nfeProc>')
    dados = extrair_dados(arvore)
    assert dados == {"cabecalho": {}, "produtos": []}


def test_destinatario_pessoa_fisica_usa_cpf(parse_xml):
    xml_cpf = XML_NFE.replace(
        "<CNPJ>11222333000181</CNPJ>", "<CPF>12345678909</CPF>"
    )
    arvore = parse_xml(xml_cpf)
    dados = extrair_dados(arvore)
    cab = dados["cabecalho"]

    assert cab["Tipo Doc Destinatário"] == "CPF"
    assert cab["CNPJ Destinatário"] == "123.456.789-09"


def test_nfe_em_contingencia_sem_envelope_nfeproc_e_extraida(parse_xml):
    xml_contingencia = (
        XML_NFE
        .replace('<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">\n  <NFe>\n', '<NFe xmlns="http://www.portalfiscal.inf.br/nfe">\n')
        .replace('\n  </NFe>\n</nfeProc>\n', '\n</NFe>\n')
    )
    arvore = parse_xml(xml_contingencia)
    dados = extrair_dados(arvore)
    cab = dados["cabecalho"]

    assert cab["Chave"] == "35200714200166000187550010000000046550010466"
    assert cab["Razão Emitente"] == "Empresa Emitente Teste LTDA"
    assert len(dados["produtos"]) == 1


def test_produto_do_simples_nacional_usa_csosn(parse_xml):
    xml_csosn = XML_NFE.replace(
        "<ICMS><ICMS00><CST>00</CST><vICMS>1,50</vICMS></ICMS00></ICMS>",
        "<ICMS><ICMSSN102><CSOSN>102</CSOSN></ICMSSN102></ICMS>",
    )
    arvore = parse_xml(xml_csosn)
    dados = extrair_dados(arvore)
    item = dados["produtos"][0]

    assert item["CST ICMS"] == "102"
    assert item["vICMS"] == 0.0
