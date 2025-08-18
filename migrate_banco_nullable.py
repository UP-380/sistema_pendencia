#!/usr/bin/env python3
"""
Script de migração - alterar campo banco para nullable
Execute este script para permitir valores NULL no campo banco
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_banco_nullable():
    """Migração para permitir NULL no campo banco"""
    
    with app.app_context():
        try:
            print("🚀 Iniciando migração para permitir NULL no campo banco...")
            
            # 1. Verificar se a coluna já permite NULL
            print("🔍 Verificando configuração atual do campo banco...")
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns = {row[1]: row[3] for row in result.fetchall()}
            
            if 'banco' in columns:
                print(f"📊 Campo banco atual: nullable={columns['banco']}")
                
                # 2. Alterar para permitir NULL (SQLite não suporta ALTER COLUMN para nullable)
                # Vamos criar uma nova tabela temporária
                print("📝 Criando tabela temporária...")
                db.session.execute(text("""
                    CREATE TABLE pendencia_temp (
                        id INTEGER PRIMARY KEY,
                        empresa VARCHAR(50) NOT NULL,
                        tipo_pendencia VARCHAR(30) NOT NULL,
                        banco VARCHAR(50),
                        data DATE,
                        data_abertura DATETIME NOT NULL,
                        fornecedor_cliente VARCHAR(200) NOT NULL,
                        valor FLOAT NOT NULL,
                        observacao VARCHAR(300),
                        resposta_cliente VARCHAR(300),
                        email_cliente VARCHAR(120),
                        status VARCHAR(50),
                        token_acesso VARCHAR(100),
                        data_resposta DATETIME,
                        modificado_por VARCHAR(50),
                        nota_fiscal_arquivo VARCHAR(300),
                        natureza_operacao VARCHAR(500),
                        motivo_recusa VARCHAR(500),
                        motivo_recusa_supervisor VARCHAR(500),
                        codigo_lancamento VARCHAR(64),
                        data_competencia DATE,
                        data_baixa DATE,
                        natureza_sistema VARCHAR(120)
                    )
                """))
                
                # 3. Copiar dados
                print("🔄 Copiando dados para tabela temporária...")
                db.session.execute(text("""
                    INSERT INTO pendencia_temp 
                    SELECT * FROM pendencia
                """))
                
                # 4. Remover tabela antiga
                print("🗑️ Removendo tabela antiga...")
                db.session.execute(text("DROP TABLE pendencia"))
                
                # 5. Renomear tabela temporária
                print("🔄 Renomeando tabela temporária...")
                db.session.execute(text("ALTER TABLE pendencia_temp RENAME TO pendencia"))
                
                db.session.commit()
                print("✅ Migração concluída com sucesso!")
                
            else:
                print("⚠️ Campo banco não encontrado na tabela")
                
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    migrate_banco_nullable()
