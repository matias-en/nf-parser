from datetime import datetime

def limpar_num(lista_xpath):

    # Trata vírgulas, converte para float e garante 0.0 se estiver vazio.
    if lista_xpath:
        try:
            return float(lista_xpath[0].replace(',', '.'))
        except (ValueError, TypeError):
            return 0.0
    return 0.0

def limpar_int(lista_xpath):

    # Garante que o valor seja um número inteiro.
    if lista_xpath:
        try:
            texto = lista_xpath[0].strip()
            return int(texto) if texto.isdigit() else 0
        except (ValueError, TypeError):
            return 0
    return 0

def formatar_data(lista_xpath):
    # Converte o texto da competência em um objeto de data do Python.
    
    if lista_xpath:
        try:
            return datetime.strptime(lista_xpath[0], "%Y-%m-%d").date()
        except:
            return lista_xpath[0]
    return None