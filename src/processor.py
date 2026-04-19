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
    
    if not lista_xpath:
        return None
    
    data_bruta = lista_xpath[0] 
    
    try:
        
        data_obj = datetime.fromisoformat(data_bruta)

        return data_obj.date()
    
    except Exception:
            
            return data_bruta[:10]