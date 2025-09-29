#!/usr/bin/env python3
"""
Script de migração para ajustar o campo data na tabela pendencia para aceitar valores nulos
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_data_nullable():
    """Ajusta o campo data na tabela pendencia para aceitar valores nulos"""
    
    with app.app_context():
        try:
            print("🔄 Iniciando migração: ajustando campo data...")
            
            # 1. Criar tabela temporária com a estrutura correta
            print("📝 Criando tabela temporária...")
            db.session.execute(text("""
                CREATE TABLE pendencia_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            
            # 2. Copiar dados da tabela original
            print("🔄 Copiando dados para tabela temporária...")
            db.session.execute(text("""
                INSERT INTO pendencia_temp 
                SELECT * FROM pendencia
            """))
            
            # 3. Remover tabela original
            print("🗑️ Removendo tabela original...")
            db.session.execute(text("DROP TABLE pendencia"))
            
            # 4. Renomear tabela temporária
            print("🔄 Renomeando tabela temporária...")
            db.session.execute(text("ALTER TABLE pendencia_temp RENAME TO pendencia"))
            
            # 5. Verificar resultado
            print("🔍 Verificando estrutura da tabela...")
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns = result.fetchall()
            
            data_column = next((col for col in columns if col[1] == 'data'), None)
            if data_column and data_column[3] == 0:  # notnull = 0 significa que aceita NULL
                print("✅ Campo 'data' agora aceita valores nulos!")
            else:
                print("⚠️ Verificar configuração do campo 'data'")
            
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    migrate_data_nullable()