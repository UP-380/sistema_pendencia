#!/usr/bin/env python3
"""
Script de migração para PRODUÇÃO - adicionar campo data_abertura na tabela pendencia
Execute este script na VPS após o deploy
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_producao():
    """Migração para produção - adiciona campo data_abertura"""
    
    with app.app_context():
        try:
            print("🚀 Iniciando migração de PRODUÇÃO...")
            print("📝 Adicionando campo data_abertura na tabela pendencia")
            
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
            
            # Primeiro, verificar se há registros sem data_abertura
            result = db.session.execute(text("SELECT COUNT(*) as total FROM pendencia WHERE data_abertura IS NULL"))
            total_null = result.fetchone().total
            
            if total_null > 0:
                print(f"📊 Encontrados {total_null} registros sem data_abertura")
                
                # Backfill usando logs ou timestamp atual
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
            else:
                print("ℹ️ Todos os registros já têm data_abertura preenchida!")
            
            # 3. Verificar resultado final
            result = db.session.execute(text("SELECT COUNT(*) as total FROM pendencia WHERE data_abertura IS NOT NULL"))
            total = result.fetchone().total
            
            result = db.session.execute(text("SELECT COUNT(*) as total FROM pendencia"))
            total_geral = result.fetchone().total
            
            print(f"✅ Migração concluída!")
            print(f"📊 Total de pendências: {total_geral}")
            print(f"📊 Pendências com data_abertura: {total}")
            
            if total == total_geral:
                print("🎉 Migração 100% bem-sucedida!")
            else:
                print(f"⚠️ Ainda há {total_geral - total} registros sem data_abertura")
                
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    migrate_producao()
