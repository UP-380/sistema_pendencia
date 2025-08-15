#!/usr/bin/env python3
"""
Script de migração para adicionar o campo data_abertura na tabela pendencia
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_add_data_abertura():
    """Adiciona o campo data_abertura na tabela pendencia"""
    
    with app.app_context():
        try:
            print("🔄 Iniciando migração: adicionando campo data_abertura...")
            
            # 1. Verificar se a coluna já existe
            print("🔍 Verificando se a coluna data_abertura já existe...")
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'data_abertura' not in columns:
                print("📝 Adicionando coluna data_abertura...")
                db.session.execute(text("""
                    ALTER TABLE pendencia 
                    ADD COLUMN data_abertura DATETIME NULL
                """))
                db.session.commit()
                print("✅ Coluna data_abertura adicionada com sucesso!")
            else:
                print("ℹ️ Coluna data_abertura já existe, pulando criação...")
            
            # 2. Backfill inteligente: usar o 1º log da pendência, se existir; senão, usar agora()
            print("🔄 Preenchendo dados de data_abertura...")
            db.session.execute(text("""
                UPDATE pendencia 
                SET data_abertura = COALESCE(
                    (SELECT MIN(l.data_hora) FROM log_alteracao l WHERE l.pendencia_id = pendencia.id),
                    CURRENT_TIMESTAMP
                )
                WHERE data_abertura IS NULL
            """))
            db.session.commit()
            print("✅ Dados de data_abertura preenchidos!")
            
            # 3. Verificar se há registros sem data_abertura
            print("🔍 Verificando registros sem data_abertura...")
            result = db.session.execute(text("SELECT COUNT(*) as total FROM pendencia WHERE data_abertura IS NULL"))
            total_null = result.fetchone().total
            if total_null == 0:
                print("✅ Todos os registros têm data_abertura preenchida!")
            else:
                print(f"⚠️ Ainda há {total_null} registros sem data_abertura")
            
            # 4. Verificar resultado
            result = db.session.execute(text("SELECT COUNT(*) as total FROM pendencia WHERE data_abertura IS NOT NULL"))
            total = result.fetchone().total
            print(f"✅ Migração concluída! {total} pendências com data_abertura preenchida.")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    migrate_add_data_abertura()
