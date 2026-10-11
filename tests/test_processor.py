from src.processor import (
    limpar_num,
    limpar_int,
    formatar_data,
    chave_valida,
    formatar_cnpj_cpf,
    sanitizar_nome_pasta,
    nome_pasta_empresa,
)


def test_limpar_num_converte_virgula_para_ponto():
    assert limpar_num(["1234,56"]) == 1234.56


def test_limpar_num_aceita_valor_com_ponto():
    assert limpar_num(["10.50"]) == 10.50


def test_limpar_num_lista_vazia_retorna_zero():
    assert limpar_num([]) == 0.0


def test_limpar_num_valor_invalido_retorna_zero():
    assert limpar_num(["abc"]) == 0.0


def test_limpar_int_converte_string_numerica():
    assert limpar_int(["42"]) == 42


def test_limpar_int_lista_vazia_retorna_zero():
    assert limpar_int([]) == 0


def test_limpar_int_valor_nao_numerico_retorna_zero():
    assert limpar_int(["N/A"]) == 0


def test_limpar_int_com_espacos_em_volta():
    assert limpar_int([" 7 "]) == 7


def test_formatar_data_iso_completa_com_timezone():
    resultado = formatar_data(["2020-07-15T10:00:00-03:00"])
    assert str(resultado) == "2020-07-15"


def test_formatar_data_lista_vazia_retorna_none():
    assert formatar_data([]) is None


def test_formatar_data_texto_invalido_usa_fallback_dos_10_primeiros_chars():
    resultado = formatar_data(["2020-07-15-formato-estranho"])
    assert resultado == "2020-07-15"


def test_chave_valida_aceita_44_digitos():
    assert chave_valida("1" * 44) is True


def test_chave_valida_rejeita_tamanho_errado():
    assert chave_valida("123") is False


def test_chave_valida_rejeita_caracteres_nao_numericos():
    assert chave_valida("a" * 44) is False


def test_formatar_cnpj_cpf_cnpj_14_digitos():
    assert formatar_cnpj_cpf("14200166000187") == "14.200.166/0001-87"


def test_formatar_cnpj_cpf_cpf_11_digitos():
    assert formatar_cnpj_cpf("12345678909") == "123.456.789-09"


def test_formatar_cnpj_cpf_ja_formatado_extrai_digitos():
    assert formatar_cnpj_cpf("14.200.166/0001-87") == "14.200.166/0001-87"


def test_formatar_cnpj_cpf_tamanho_invalido_retorna_original():
    assert formatar_cnpj_cpf("123") == "123"


def test_formatar_cnpj_cpf_vazio_retorna_vazio():
    assert formatar_cnpj_cpf("") == ""


def test_formatar_cnpj_cpf_none_retorna_none():
    assert formatar_cnpj_cpf(None) is None


def test_sanitizar_nome_pasta_remove_caracteres_invalidos():
    assert sanitizar_nome_pasta('Loja "Top" / Ltda: *?<>|') == "Loja Top  Ltda"


def test_sanitizar_nome_pasta_none_retorna_vazio():
    assert sanitizar_nome_pasta(None) == ""


def test_nome_pasta_empresa_formata_cnpj_e_razao():
    resultado = nome_pasta_empresa("14.200.166/0001-87", "Empresa Teste LTDA")
    assert resultado == "14200166000187 - Empresa Teste LTDA"


def test_nome_pasta_empresa_sem_cnpj():
    resultado = nome_pasta_empresa("", "Empresa Sem CNPJ")
    assert resultado == " - Empresa Sem CNPJ"
