# Regras de validação por tipo de pendência
TIPO_RULES = {
    "Natureza Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data"],
        "forbidden": ["banco", "data_competencia", "data_baixa"],
        "labels": {"data": "Data do Lançamento ou Baixa"},
        "observacao_hint": "Natureza atual no ERP (obrigatório registrar)",
        "columns": ["tipo", "fornecedor_cliente", "valor", "codigo_lancamento", "data", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "codigo_lancamento", "data", "natureza_sistema", "observacao", "email_cliente"]
    },
    "Competência Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data_competencia"],
        "forbidden": ["banco", "data_baixa"],
        "labels": {"data_competencia": "Data Competência"},
        "observacao_hint": "Informe: Data da competência errada",
        "columns": ["tipo", "fornecedor_cliente", "valor", "codigo_lancamento", "data_competencia", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "codigo_lancamento", "data_competencia", "observacao", "email_cliente"]
    },
    "Data da Baixa Errada": {
        "required": ["banco", "data_baixa", "fornecedor_cliente", "valor", "codigo_lancamento"],
        "forbidden": [],
        "labels": {"data_baixa": "Data da Baixa"},
        "observacao_hint": "Campo livre para contexto",
        "columns": ["tipo", "banco", "data_baixa", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data_baixa", "fornecedor", "valor", "codigo_lancamento", "observacao", "email_cliente"]
    },
    "Cartão de Crédito Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "valor", "observacao", "email_cliente"]
    },
    "Pagamento Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "fornecedor", "valor", "observacao", "email_cliente"]
    },
    "Recebimento Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "valor", "observacao", "email_cliente"]
    },
    "Documento Não Anexado": {
        "required": ["fornecedor_cliente", "valor", "data"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "data", "observacao", "email_cliente"]
    },
    "Lançamento Não Encontrado em Extrato": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "fornecedor", "valor", "codigo_lancamento", "observacao", "email_cliente"]
    },
    "Lançamento Não Encontrado em Sistema": {
        "required": ["fornecedor_cliente", "valor", "data", "tipo_credito_debito"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "codigo_lancamento", "tipo_credito_debito", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "data", "codigo_lancamento", "tipo_credito_debito", "observacao", "email_cliente"],
        "labels": {"tipo_credito_debito": "Tipo de Lançamento"},
        "observacao_hint": "Informe detalhes do lançamento não encontrado"
    }
}

# Mapeamento de tipos para importação
TIPO_IMPORT_MAP = {
    "NATUREZA_ERRADA": "Natureza Errada",
    "COMPETENCIA_ERRADA": "Competência Errada", 
    "DATA_BAIXA_ERRADA": "Data da Baixa Errada",
    "CARTAO_NAO_IDENTIFICADO": "Cartão de Crédito Não Identificado",
    "PAGAMENTO_NAO_IDENTIFICADO": "Pagamento Não Identificado",
    "RECEBIMENTO_NAO_IDENTIFICADO": "Recebimento Não Identificado",
    "DOCUMENTO_NAO_ANEXADO": "Documento Não Anexado",
    "LANCAMENTO_NAO_ENCONTRADO_EXTRATO": "Lançamento Não Encontrado em Extrato",
    "LANCAMENTO_NAO_ENCONTRADO_SISTEMA": "Lançamento Não Encontrado em Sistema",
    # Mapeamentos legados (para compatibilidade com planilhas antigas)
    "NOTA_FISCAL_NAO_ANEXADA": "Documento Não Anexado",
    "NOTA_FISCAL_NAO_IDENTIFICADA": "Documento Não Anexado"
}

from app.utils.helpers import parse_currency_to_float, parse_date_or_none

def validar_por_tipo(payload):
    """Valida campos obrigatórios e proibidos por tipo de pendência"""
    tipo = payload.get("tipo_pendencia")
    rule = TIPO_RULES.get(tipo)
    if not rule:
        return False, f"Tipo de pendência inválido: {tipo}"

    # Verificar campos obrigatórios (apenas se existir a chave "required")
    if "required" in rule:
        for field in rule["required"]:
            if not payload.get(field):
                return False, f"Campo obrigatório ausente: {field} (tipo {tipo})"

    # Verificar campos proibidos
    for field in rule.get("forbidden", []):
        if payload.get(field):
            return False, f"Campo não deve ser preenchido para {tipo}: {field}"

    # Coerência de valor (converte formato brasileiro)
    if payload.get("valor"):
        try:
            valor_convertido = parse_currency_to_float(payload["valor"])
            if valor_convertido <= 0:
                return False, "Valor deve ser maior que zero."
        except (ValueError, TypeError):
            return False, "Valor inválido. Use formato: R$ 0,00"

    return True, None

def obter_colunas_por_tipo(tipo_pendencia):
    """Retorna as colunas que devem ser exibidas para um tipo específico de pendência"""
    rule = TIPO_RULES.get(tipo_pendencia)
    if rule and "columns" in rule:
        return rule["columns"]
    # Fallback para tipos não configurados
    return ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]

def obter_todas_colunas():
    """Retorna todas as colunas disponíveis para o painel"""
    return {
        "tipo": "Tipo",
        "banco": "Banco", 
        "data": "Data da Pendência",
        "data_abertura": "Data de Abertura",
        "fornecedor_cliente": "Fornecedor/Cliente",
        "valor": "Valor",
        "codigo_lancamento": "Código",
        "data_competencia": "Data Comp.",
        "data_baixa": "Data Baixa",
        "observacao": "Observação",
        "status": "Status",
        "modificado_por": "Modificado por"
    }

def validar_row_por_tipo(tipo, row):
    """Valida uma linha da planilha conforme o tipo de pendência"""
    rule = TIPO_RULES.get(tipo)
    if not rule:
        return f"Tipo de pendência inválido: {tipo}"
    
    def has(field):
        """Verifica se o campo tem valor válido"""
        val = row.get(field, "")
        return val not in [None, "", "NaN", "nan", "None", "null", "NULL", "undefined", "N/A", "n/a"]
    
    def get_field_value(field):
        """Obtém valor do campo com fallbacks"""
        # Tentar campo original
        val = row.get(field, "")
        if val not in [None, "", "NaN", "nan", "None", "null", "NULL", "undefined", "N/A", "n/a"]:
            return val
        
        # Tentar variações do nome
        field_variations = [
            field.replace("_cliente", ""),
            field.replace("_or_id", ""),
            field + "_id"
        ]
        
        for variation in field_variations:
            val = row.get(variation, "")
            if val not in [None, "", "NaN", "nan", "None", "null", "NULL", "undefined", "N/A", "n/a"]:
                return val
        
        return ""
    
    # Verificar campos obrigatórios
    for field in rule.get("required", []):
        field_value = get_field_value(field)
        if not field_value:
            return f"Campo obrigatório ausente ou vazio: {field}"
    
    # Verificar campos proibidos
    for field in rule.get("forbidden", []):
        if has(field):
            return f"Campo proibido para {tipo}: {field}"
    
    # Validar valor
    if has("valor"):
        try:
            valor = float(row["valor"])
            if valor <= 0:
                return "Valor deve ser maior que zero."
        except (ValueError, TypeError):
            return "Valor deve ser um número válido."
    
    # Validar datas específicas
    if tipo == "Competência Errada" and has("data_competencia"):
        if not parse_date_or_none(row.get("data_competencia")):
            return "Data Competência inválida. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Data da Baixa Errada" and has("data_baixa"):
        if not parse_date_or_none(row.get("data_baixa")):
            return "Data da Baixa inválida. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Natureza Errada" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data do Lançamento ou Baixa inválida. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    # Validar campos de data obrigatórios para outros tipos
    if tipo == "Recebimento Não Identificado" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Recebimento Não Identificado. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Pagamento Não Identificado" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Pagamento Não Identificado. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Cartão de Crédito Não Identificado" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Cartão de Crédito Não Identificado. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Nota Fiscal Não Anexada" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Nota Fiscal Não Anexada. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    return None

def label_tipo_planilha(tipo_import):
    """Converte tipo de importação para rótulo humano"""
    return TIPO_IMPORT_MAP.get(tipo_import, tipo_import)
