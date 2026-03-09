#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para adicionar função ao rules.py"""

nova_funcao = '''

def obter_colunas_importacao_por_tipo(tipo_pendencia):
    """Retorna as colunas necessárias para importação de um tipo específico de pendência"""
    rule = TIPO_RULES.get(tipo_pendencia)
    if rule and "import_columns" in rule:
        return rule["import_columns"]
    return ["empresa", "banco", "data", "fornecedor", "valor", "observacao", "email_cliente"]
'''

with open('app/services/rules.py', 'a', encoding='utf-8') as f:
    f.write(nova_funcao)

print("Função adicionada com sucesso!")
