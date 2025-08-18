#!/usr/bin/env python3
"""
Script de migração - adicionar campos para novos tipos de pendência
Execute este script para adicionar os campos especializados
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_novos_tipos():
    """Migração para adicionar campos dos novos tipos de pendência"""
    
    with app.app_context():
        try:
            print("🚀 Iniciando migração para novos tipos de pendência...")
            
            # 1. Verificar colunas existentes
            print("🔍 Verificando colunas existentes...")
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns = [row[1] for row in result.fetchall()]
            
            # 2. Adicionar novas colunas
            novos_campos = [
                ("codigo_lancamento", "TEXT"),
                ("data_competencia", "DATE"),
                ("data_baixa", "DATE"),
                ("natureza_sistema", "TEXT")
            ]
            
            for campo, tipo in novos_campos:
                if campo not in columns:
                    print(f"📝 Adicionando coluna {campo}...")
                    db.session.execute(text(f"""
                        ALTER TABLE pendencia 
                        ADD COLUMN {campo} {tipo} NULL
                    """))
                    db.session.commit()
                    print(f"✅ Coluna {campo} adicionada com sucesso!")
                else:
                    print(f"ℹ️ Coluna {campo} já existe, pulando...")
            
            # 3. Verificar resultado final
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns_final = [row[1] for row in result.fetchall()]
            
            print(f"✅ Migração concluída!")
            print(f"📊 Colunas na tabela pendencia: {', '.join(columns_final)}")
            
            # 4. Verificar se todos os campos foram adicionados
            campos_esperados = ["codigo_lancamento", "data_competencia", "data_baixa", "natureza_sistema"]
            campos_faltando = [campo for campo in campos_esperados if campo not in columns_final]
            
            if not campos_faltando:
                print("🎉 Todos os campos foram adicionados com sucesso!")
            else:
                print(f"⚠️ Campos faltando: {campos_faltando}")
                
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    migrate_novos_tipos()
