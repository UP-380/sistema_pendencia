#!/usr/bin/env python3
"""
Script Simplificado de Análise do Banco de Dados
"""

import sqlite3

def main():
    conn = sqlite3.connect('pendencias.db')
    cursor = conn.cursor()
    
    print("="*80)
    print("ANÁLISE DO BANCO DE DADOS - Sistema UP380")
    print("="*80)
    
    # 1. Listar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = [row[0] for row in cursor.fetchall()]
    print(f"\nTabelas: {', '.join(tabelas)}")
    
    # 2. Analisar tabela pendencia
    print("\n" + "="*80)
    print("TABELA: pendencia")
    print("="*80)
    
    cursor.execute("PRAGMA table_info(pendencia)")
    colunas = cursor.fetchall()
    print(f"\nColunas ({len(colunas)}):")
    for col in colunas:
        print(f"  - {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
    
    # Verificar índices
    cursor.execute("PRAGMA index_list(pendencia)")
    indices = cursor.fetchall()
    print(f"\nÍndices ({len(indices)}):")
    for idx in indices:
        print(f"  - {idx[1]}")
    
    # Contar registros
    cursor.execute("SELECT COUNT(*) FROM pendencia")
    total = cursor.fetchone()[0]
    print(f"\nTotal de registros: {total}")
    
    # Estatísticas
    if total > 0:
        cursor.execute("SELECT status, COUNT(*) FROM pendencia GROUP BY status")
        print("\nPor Status:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        cursor.execute("SELECT tipo_pendencia, COUNT(*) FROM pendencia GROUP BY tipo_pendencia")
        print("\nPor Tipo:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
    
    # 3. Verificar problemas
    print("\n" + "="*80)
    print("VERIFICAÇÃO DE PROBLEMAS")
    print("="*80)
    
    # Valores inválidos
    cursor.execute("SELECT COUNT(*) FROM pendencia WHERE valor <= 0")
    invalidos = cursor.fetchone()[0]
    if invalidos > 0:
        print(f"\n❌ {invalidos} pendências com valor <= 0")
    
    # Sem email
    cursor.execute("SELECT COUNT(*) FROM pendencia WHERE email_cliente IS NULL OR email_cliente = ''")
    sem_email = cursor.fetchone()[0]
    if sem_email > 0:
        print(f"⚠️  {sem_email} pendências sem email_cliente")
    
    # Tokens duplicados
    cursor.execute("""
        SELECT token_acesso, COUNT(*) 
        FROM pendencia 
        WHERE token_acesso IS NOT NULL
        GROUP BY token_acesso 
        HAVING COUNT(*) > 1
    """)
    dup_tokens = cursor.fetchall()
    if dup_tokens:
        print(f"❌ {len(dup_tokens)} tokens DUPLICADOS!")
    
    # 4. Gerar script de correção
    print("\n" + "="*80)
    print("GERANDO SCRIPT DE CORREÇÃO")
    print("="*80)
    
    script = """-- Script de Correção do Banco de Dados
-- Sistema de Pendências UP380

-- Habilitar foreign keys
PRAGMA foreign_keys = ON;

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_pendencia_empresa ON pendencia(empresa);
CREATE INDEX IF NOT EXISTS idx_pendencia_status ON pendencia(status);
CREATE INDEX IF NOT EXISTS idx_pendencia_tipo ON pendencia(tipo_pendencia);
CREATE INDEX IF NOT EXISTS idx_pendencia_data_abertura ON pendencia(data_abertura);
CREATE INDEX IF NOT EXISTS idx_pendencia_token ON pendencia(token_acesso);

-- Adicionar campo tipo_credito_debito
ALTER TABLE pendencia ADD COLUMN tipo_credito_debito VARCHAR(10);

-- Verificar integridade
PRAGMA integrity_check;
"""
    
    with open('correcao_banco.sql', 'w', encoding='utf-8') as f:
        f.write(script)
    
    print("\n✅ Script salvo em: correcao_banco.sql")
    
    conn.close()
    print("\n" + "="*80)
    print("ANÁLISE CONCLUÍDA")
    print("="*80)

if __name__ == '__main__':
    main()
