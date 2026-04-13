from datetime import datetime

def limpar_num(lista_xpath):

    if lista_xpath:
        try:
            return float(lista_xpath[0].replace(',', '.'))
        except (ValueError, TypeError):
            return 0.0
    return 0.0

def limpar_int(lista_xpath):

    if lista_xpath:
        try:
            texto = lista_xpath[0].strip()
            return int(texto) if texto.isdigit() else 0
        except (ValueError, TypeError):
            return 0
    return 0

def formatar_data(lista_xpath):
    
    if lista_xpath:
        try:
            return datetime.strptime(lista_xpath[0], "%Y-%m-%d").date()
        except:
            return lista_xpath[0]
    return None