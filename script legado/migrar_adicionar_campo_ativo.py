#!/usr/bin/env python3
"""
Script de migração para adicionar o campo 'ativo' à tabela 'usuario'
"""

from app import app, db
import sqlite3
import os

def migrar_banco(db_path):
    """Migra um banco de dados específico"""
    if not os.path.exists(db_path):
        print(f"⚠️  Banco não encontrado: {db_path} (pulando...)")
        return True  # Não é erro se não existir
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(usuario)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ativo' in columns:
            print(f"✅ {db_path}: Coluna 'ativo' já existe")
            conn.close()
            return True
        
        # Adicionar coluna 'ativo' com valor padrão True
        print(f"🔄 {db_path}: Adicionando coluna 'ativo'...")
        cursor.execute("ALTER TABLE usuario ADD COLUMN ativo BOOLEAN DEFAULT 1 NOT NULL")
        
        # Atualizar todos os registros existentes para ativo=True
        cursor.execute("UPDATE usuario SET ativo = 1 WHERE ativo IS NULL")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {db_path}: Coluna 'ativo' adicionada com sucesso!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao migrar {db_path}: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Erro inesperado em {db_path}: {e}")
        return False

def migrar_campo_ativo():
    """Adiciona a coluna 'ativo' à tabela usuario em todos os bancos"""
    with app.app_context():
        # Lista de possíveis caminhos do banco
        db_paths = [
            app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''),
            'instance/pendencias.db',
            'pendencias.db'
        ]
        
        # Remover duplicatas mantendo ordem
        db_paths = list(dict.fromkeys(db_paths))
        
        sucesso = True
        for db_path in db_paths:
            if not migrar_banco(db_path):
                sucesso = False
        
        if sucesso:
            print("\n✅ Todos os bancos foram migrados com sucesso!")
            print("   Todos os usuários existentes foram marcados como ativos.")
        
        return sucesso

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar campo 'ativo' à tabela 'usuario'")
    print("=" * 60)
    
    if migrar_campo_ativo():
        print("\n✅ Migração concluída com sucesso!")
    else:
        print("\n❌ Falha na migração!")
    
    print("=" * 60)

