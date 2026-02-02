import re
import pytz
from datetime import datetime, timedelta

BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')

def now_brazil():
    return datetime.now(BRAZIL_TZ)

def pick(val_a, val_b):
    """Usa id se vier, senão usa nome"""
    return val_a or val_b

def parse_currency_to_float(valor_str):
    """
    Converte string de moeda para float.
    Suporta formatos:
    - Brasileiro: R$ 1.234,56 ou 1.234,56
    - Americano/Excel: 1234.56
    - Apenas números: 1234
    """
    if not valor_str:
        return 0.0
    
    # Converte para string se não for
    v = str(valor_str).strip()
    
    # Remove símbolo R$
    v = re.sub(r'R\$', '', v)
    
    # Remove todos os tipos de espaços (incluindo \xa0, \u00a0, etc.)
    v = re.sub(r'[\s\xa0\u00a0\u2000-\u200f\u2028-\u202f\u205f-\u206f]', '', v)
    
    # Detectar formato:
    # Se tem vírgula E ponto: formato brasileiro (1.234,56)
    # Se tem apenas vírgula: formato brasileiro (1234,56)
    # Se tem apenas ponto: formato americano/Excel (1234.56)
    # Se não tem nenhum: número inteiro (1234)
    
    if ',' in v and '.' in v:
        # Formato brasileiro: 1.234,56 -> remove pontos e troca vírgula por ponto
        v = v.replace('.', '').replace(',', '.')
    elif ',' in v:
        # Formato brasileiro sem milhar: 1234,56 -> troca vírgula por ponto
        v = v.replace(',', '.')
    elif '.' in v:
        # Pode ser formato americano (1234.56) OU brasileiro com milhar (1.234)
        # Se tem mais de um ponto, é brasileiro com milhar
        if v.count('.') > 1:
            # Formato brasileiro: 1.234.567 -> remove pontos
            v = v.replace('.', '')
        else:
            # Verificar se é milhar ou decimal
            # Se o ponto está nos últimos 3 caracteres, é decimal (1234.56)
            # Se não, é milhar (1.234)
            parts = v.split('.')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # É decimal: 1234.56 -> manter
                pass
            else:
                # É milhar: 1.234 -> remover ponto
                v = v.replace('.', '')
    
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0

def parse_date_or_none(s):
    """Converte string para data ou retorna None - aceita múltiplos formatos"""
    if not s or str(s).strip() == "" or str(s).strip().lower() in ["nan", "none", "null"]:
        return None
    
    # Se já for um objeto date ou datetime
    if isinstance(s, datetime):
        return s.date()
    
    s = str(s).strip()
    
    # Se contiver espaço (provavelmente tem hora), pega apenas a primeira parte
    if " " in s:
        s = s.split(" ")[0]
    
    # Lista de formatos de data aceitos
    date_formats = [
        "%Y-%m-%d",      # 2025-08-18
        "%d/%m/%Y",      # 18/08/2025
        "%d-%m-%Y",      # 18-08-2025
        "%Y/%m/%d",      # 2025/08/18
        "%d/%m/%y",      # 18/08/25
        "%d-%m-%y",      # 18-08-25
        "%d.%m.%Y",      # 18.08.2025
        "%d.%m.%y",      # 18.08.25
        "%Y-%m-%dT%H:%M:%S", # ISO format common in some exports
    ]
    
    for fmt in date_formats:
        try:
            # Tenta converter usando o formato completo ou apenas a parte da data
            if 'T' in s and fmt == "%Y-%m-%dT%H:%M:%S":
                return datetime.strptime(s, fmt).date()
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    
    # Tentar converter se for um número (Excel às vezes retorna números de série)
    try:
        # Remove caracteres que podem vir em números formatados
        clean_s = s.replace(',', '.').split('.')[0] # Pega apenas a parte inteira para dias
        if clean_s.isdigit() and len(clean_s) <= 6: # Serial do Excel é um número curto
            serial = int(clean_s)
            # Excel base date is 1899-12-30 for serial 1 (due to 1900 leap year bug)
            base_date = datetime(1899, 12, 30)
            return (base_date + timedelta(days=serial)).date()
    except (ValueError, TypeError, OverflowError):
        pass
    
    return None
