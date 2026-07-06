import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def limpar_num(lista_xpath) -> float:
    if lista_xpath:
        try:
            return float(lista_xpath[0].replace(',', '.'))
        except (ValueError, TypeError):
            return 0.0
    return 0.0

def limpar_int(lista_xpath) -> int:
    if lista_xpath:
        try:
            texto = lista_xpath[0].strip()
            if texto.isdigit():
                return int(texto)
            logger.warning(f"Valor inteiro inválido encontrado: '{texto}'")
            return 0
        except (ValueError, TypeError):
            return 0
    return 0

def formatar_data(lista_xpath):
    if not lista_xpath:
        return None
    data_bruta = lista_xpath[0]
    try:
        return datetime.fromisoformat(data_bruta).date()
    except Exception:
        return data_bruta[:10]

def chave_valida(chave: str) -> bool:
    """Valida se a chave fiscal tem exatamente 44 dígitos numéricos."""
    return len(chave) == 44 and chave.isdigit()

def formatar_cnpj_cpf(documento: str) -> str:
    """Formata CNPJ (00.000.000/0000-00) ou CPF (000.000.000-00)."""
    doc = "".join(filter(str.isdigit, documento or ""))
    if len(doc) == 14:
        return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
    if len(doc) == 11:
        return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
    return documento

def sanitizar_nome_pasta(nome: str) -> str:
    """Remove caracteres inválidos para nomes de pasta em qualquer SO."""
    nome = re.sub(r'[\\/:*?"<>|]', '', nome or "")
    return nome.strip()

def nome_pasta_empresa(cnpj: str, razao_social: str) -> str:
    """Gera nome de pasta no formato: '00000000000000 - Razão Social'."""
    cnpj_limpo = "".join(filter(str.isdigit, cnpj or ""))
    razao_limpa = sanitizar_nome_pasta(razao_social)
    return f"{cnpj_limpo} - {razao_limpa}"
