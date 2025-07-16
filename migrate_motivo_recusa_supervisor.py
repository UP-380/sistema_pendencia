#!/usr/bin/env python3
"""
Script de migração para adicionar a coluna motivo_recusa_supervisor na tabela Pendencia
"""

import sqlite3
import os
from datetime import datetime

def migrar_motivo_recusa_supervisor():
    """Adiciona a coluna motivo_recusa_supervisor na tabela Pendencia"""
    
    # Caminho do banco de dados
    db_path = 'instance/pendencias.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(pendencia)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'motivo_recusa_supervisor' in colunas:
            print("✅ Coluna 'motivo_recusa_supervisor' já existe na tabela Pendencia")
            return True
        
        # Adicionar a nova coluna
        print("🔄 Adicionando coluna 'motivo_recusa_supervisor'...")
        cursor.execute("""
            ALTER TABLE pendencia 
            ADD COLUMN motivo_recusa_supervisor TEXT
        """)
        
        # Commit das alterações
        conn.commit()
        
        # Verificar se a coluna foi criada
        cursor.execute("PRAGMA table_info(pendencia)")
        colunas_apos = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'motivo_recusa_supervisor' in colunas_apos:
            print("✅ Coluna 'motivo_recusa_supervisor' adicionada com sucesso!")
            
            # Mostrar estrutura atualizada da tabela
            print("\n📋 Estrutura atualizada da tabela Pendencia:")
            cursor.execute("PRAGMA table_info(pendencia)")
            for coluna in cursor.fetchall():
                print(f"  - {coluna[1]} ({coluna[2]})")
            
            return True
        else:
            print("❌ Erro: Coluna não foi criada")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Erro SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migração: motivo_recusa_supervisor")
    print("=" * 50)
    
    sucesso = migrar_motivo_recusa_supervisor()
    
    print("=" * 50)
    if sucesso:
        print("🎉 Migração concluída com sucesso!")
        print("📝 A funcionalidade de recusa do Supervisor está pronta para uso.")
    else:
        print("💥 Migração falhou!")
        print("🔧 Verifique os erros acima e tente novamente.") 