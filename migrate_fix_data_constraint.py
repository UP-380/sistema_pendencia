#!/usr/bin/env python3
"""
Script de migração para corrigir a constraint NOT NULL do campo data na tabela pendencia
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_fix_data_constraint():
    """Corrige a constraint NOT NULL do campo data na tabela pendencia"""
    
    with app.app_context():
        try:
            print("🔄 Iniciando migração: corrigindo constraint do campo data...")
            
            # 1. Verificar estrutura atual
            print("🔍 Verificando estrutura atual da tabela...")
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns = result.fetchall()
            
            data_column = next((col for col in columns if col[1] == 'data'), None)
            if data_column:
                print(f"📊 Campo 'data' atual: notnull={data_column[3]}, type={data_column[2]}")
                
                # Se já aceita NULL, não precisa fazer nada
                if data_column[3] == 0:
                    print("✅ Campo 'data' já aceita valores nulos!")
                    return
            
            # 2. Criar backup da tabela
            print("💾 Criando backup da tabela...")
            db.session.execute(text("""
                CREATE TABLE pendencia_backup AS 
                SELECT * FROM pendencia
            """))
            
            # 3. Criar nova tabela com estrutura correta
            print("📝 Criando nova tabela com estrutura correta...")
            db.session.execute(text("""
                CREATE TABLE pendencia_new (
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
            
            # 4. Copiar dados da tabela original
            print("🔄 Copiando dados para nova tabela...")
            db.session.execute(text("""
                INSERT INTO pendencia_new 
                SELECT * FROM pendencia
            """))
            
            # 5. Remover tabela original
            print("🗑️ Removendo tabela original...")
            db.session.execute(text("DROP TABLE pendencia"))
            
            # 6. Renomear nova tabela
            print("🔄 Renomeando nova tabela...")
            db.session.execute(text("ALTER TABLE pendencia_new RENAME TO pendencia"))
            
            # 7. Verificar resultado
            print("🔍 Verificando nova estrutura...")
            result = db.session.execute(text("PRAGMA table_info(pendencia)"))
            columns = result.fetchall()
            
            data_column = next((col for col in columns if col[1] == 'data'), None)
            if data_column and data_column[3] == 0:  # notnull = 0 significa que aceita NULL
                print("✅ Campo 'data' agora aceita valores nulos!")
            else:
                print("⚠️ Erro: Campo 'data' ainda não aceita valores nulos")
                raise Exception("Falha na migração do campo data")
            
            # 8. Verificar integridade dos dados
            count_original = db.session.execute(text("SELECT COUNT(*) FROM pendencia_backup")).scalar()
            count_new = db.session.execute(text("SELECT COUNT(*) FROM pendencia")).scalar()
            
            if count_original == count_new:
                print(f"✅ Dados preservados: {count_new} registros")
            else:
                print(f"⚠️ Atenção: Contagem diferente - Original: {count_original}, Nova: {count_new}")
            
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            
            # Tentar restaurar backup se existir
            try:
                print("🔄 Tentando restaurar backup...")
                db.session.execute(text("DROP TABLE IF EXISTS pendencia"))
                db.session.execute(text("ALTER TABLE pendencia_backup RENAME TO pendencia"))
                db.session.commit()
                print("✅ Backup restaurado!")
            except:
                print("❌ Falha ao restaurar backup")
            
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    migrate_fix_data_constraint()

