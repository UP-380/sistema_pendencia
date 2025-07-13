#!/usr/bin/env python3
"""
Script de migração para adicionar o campo motivo_recusa à tabela Pendencia
"""

import sqlite3
import os

def migrate_motivo_recusa():
    """Adiciona o campo motivo_recusa à tabela Pendencia"""
    
    # Caminho do banco de dados
    db_path = 'instance/pendencias.db'
    
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em: {db_path}")
        return False
    
    try:
        # Conecta ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se o campo já existe
        cursor.execute("PRAGMA table_info(pendencia)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'motivo_recusa' in columns:
            print("Campo 'motivo_recusa' já existe na tabela Pendencia.")
            return True
        
        # Adiciona o campo motivo_recusa
        print("Adicionando campo 'motivo_recusa' à tabela Pendencia...")
        cursor.execute("ALTER TABLE pendencia ADD COLUMN motivo_recusa TEXT")
        
        # Commit das alterações
        conn.commit()
        print("Campo 'motivo_recusa' adicionado com sucesso!")
        
        # Verifica se foi adicionado
        cursor.execute("PRAGMA table_info(pendencia)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'motivo_recusa' in columns:
            print("✓ Migração concluída com sucesso!")
            return True
        else:
            print("✗ Erro: Campo não foi adicionado.")
            return False
            
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== Migração: Adicionar campo motivo_recusa ===")
    success = migrate_motivo_recusa()
    if success:
        print("Migração executada com sucesso!")
    else:
        print("Falha na migração!") 