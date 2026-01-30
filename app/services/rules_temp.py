
def obter_colunas_importacao_por_tipo(tipo_pendencia):
    """Retorna as colunas necessárias para importação de um tipo específico de pendência"""
    rule = TIPO_RULES.get(tipo_pendencia)
    if rule and "import_columns" in rule:
        return rule["import_columns"]
    # Fallback para tipos não configurados
    return ["empresa", "banco", "data", "fornecedor", "valor", "observacao", "email_cliente"]
