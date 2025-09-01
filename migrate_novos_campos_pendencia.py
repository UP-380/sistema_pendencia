#!/usr/bin/env python3
"""
Script de migração para adicionar os novos campos especializados na tabela pendencia
"""

import sqlite3
import os

def migrate_novos_campos_pendencia():
    """Adiciona os novos campos especializados na tabela pendencia"""
    
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
        
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(pendencia)")
        columns = [column[1] for column in cursor.fetchall()]
        
        novos_campos = [
            'codigo_lancamento',
            'data_competencia', 
            'data_baixa',
            'natureza_sistema'
        ]
        
        campos_para_adicionar = []
        for campo in novos_campos:
            if campo not in columns:
                campos_para_adicionar.append(campo)
            else:
                print(f"✅ Coluna '{campo}' já existe na tabela pendencia")
        
        if not campos_para_adicionar:
            print("✅ Todos os campos já existem na tabela pendencia")
            return True
        
        # Adicionar os novos campos
        for campo in campos_para_adicionar:
            print(f"�� Adicionando coluna '{campo}' na tabela pendencia...")
            
            if campo == 'codigo_lancamento':
                cursor.execute("ALTER TABLE pendencia ADD COLUMN codigo_lancamento TEXT")
            elif campo == 'data_competencia':
                cursor.execute("ALTER TABLE pendencia ADD COLUMN data_competencia DATE")
            elif campo == 'data_baixa':
                cursor.execute("ALTER TABLE pendencia ADD COLUMN data_baixa DATE")
            elif campo == 'natureza_sistema':
                cursor.execute("ALTER TABLE pendencia ADD COLUMN natureza_sistema TEXT")
        
        # Commit das alterações
        conn.commit()
        
        print("✅ Migração de novos campos concluída com sucesso!")
        print(f"�� Campos adicionados: {', '.join(campos_para_adicionar)}")
        
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
    print("�� Iniciando migração: novos campos especializados")
    success = migrate_novos_campos_pendencia()
    
    if success:
        print("�� Migração concluída com sucesso!")
    else:
        print("💥 Falha na migração!")
        exit(1)