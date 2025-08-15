#!/usr/bin/env python3
"""
Script de migração para adicionar a coluna data_abertura na tabela pendencia
"""

import sqlite3
import os

def migrate_data_abertura():
    """Adiciona a coluna data_abertura na tabela pendencia"""
    
    # Caminho para o banco de dados
    db_path = 'instance/pendencias.db'
    
    # Verificar se o banco existe
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(pendencia)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'data_abertura' in columns:
            print("✅ Coluna 'data_abertura' já existe na tabela pendencia")
            return True
        
        # Adicionar a coluna data_abertura
        print("📊 Adicionando coluna 'data_abertura' na tabela pendencia...")
        cursor.execute("ALTER TABLE pendencia ADD COLUMN data_abertura TEXT")
        
        # Atualizar registros existentes com a data atual (ou data se já existir)
        print("🔄 Atualizando registros existentes...")
        cursor.execute("""
            UPDATE pendencia 
            SET data_abertura = COALESCE(data, datetime('now'))
            WHERE data_abertura IS NULL
        """)
        
        # Commit das alterações
        conn.commit()
        
        print("✅ Migração 'data_abertura' concluída com sucesso!")
        print(f"📊 Registros atualizados: {cursor.rowcount}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro na migração: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migração: data_abertura")
    success = migrate_data_abertura()
    
    if success:
        print("🎉 Migração concluída com sucesso!")
    else:
        print("💥 Falha na migração!")
        exit(1)
