#!/usr/bin/env python3
"""
Script de migração para adicionar as colunas natureza_operacao e motivo_recusa
à tabela pendencia no banco de dados SQLite.
"""

import sqlite3
import os

def migrate_database():
    """Adiciona as colunas natureza_operacao e motivo_recusa à tabela pendencia"""
    
    # Caminho do banco de dados
    db_path = 'instance/pendencias.db'
    
    # Verifica se o banco existe
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em: {db_path}")
        return False
    
    try:
        # Conecta ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se as colunas já existem
        cursor.execute("PRAGMA table_info(pendencia)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("Colunas existentes na tabela pendencia:")
        for col in columns:
            print(f"  - {col}")
        
        # Adiciona a coluna natureza_operacao se não existir
        if 'natureza_operacao' not in columns:
            print("Adicionando coluna 'natureza_operacao'...")
            cursor.execute("ALTER TABLE pendencia ADD COLUMN natureza_operacao TEXT")
            print("✓ Coluna 'natureza_operacao' adicionada com sucesso!")
        else:
            print("✓ Coluna 'natureza_operacao' já existe")
        
        # Adiciona a coluna motivo_recusa se não existir
        if 'motivo_recusa' not in columns:
            print("Adicionando coluna 'motivo_recusa'...")
            cursor.execute("ALTER TABLE pendencia ADD COLUMN motivo_recusa TEXT")
            print("✓ Coluna 'motivo_recusa' adicionada com sucesso!")
        else:
            print("✓ Coluna 'motivo_recusa' já existe")
        
        # Confirma as alterações
        conn.commit()
        
        # Verifica novamente as colunas
        cursor.execute("PRAGMA table_info(pendencia)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        print("\nColunas após a migração:")
        for col in columns_after:
            print(f"  - {col}")
        
        conn.close()
        print("\n✅ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migração do banco de dados...")
    success = migrate_database()
    
    if success:
        print("\n🎉 Migração realizada com sucesso!")
        print("Agora você pode reiniciar o sistema.")
    else:
        print("\n💥 Falha na migração. Verifique os erros acima.") 