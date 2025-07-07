#!/usr/bin/env python3
"""
Script de migração para adicionar o campo natureza_operacao ao banco de dados
"""

import sqlite3
import os

def migrate_database():
    """Adiciona o campo natureza_operacao à tabela pendencia"""
    
    db_path = 'instance/pendencias.db'
    
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em {db_path}")
        return
    
    try:
        # Conecta ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se o campo já existe
        cursor.execute("PRAGMA table_info(pendencia)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'natureza_operacao' not in columns:
            print("Adicionando campo natureza_operacao...")
            
            # Adiciona o novo campo
            cursor.execute("""
                ALTER TABLE pendencia 
                ADD COLUMN natureza_operacao TEXT
            """)
            
            conn.commit()
            print("✅ Campo natureza_operacao adicionado com sucesso!")
        else:
            print("✅ Campo natureza_operacao já existe!")
        
        # Verifica se há pendências com status antigos que precisam ser migradas
        cursor.execute("""
            SELECT id, status FROM pendencia 
            WHERE status = 'Pendente UP' 
            AND resposta_cliente IS NOT NULL
        """)
        
        pendencias_para_migrar = cursor.fetchall()
        
        if pendencias_para_migrar:
            print(f"Migrando {len(pendencias_para_migrar)} pendências para novo fluxo...")
            
            for pendencia_id, status in pendencias_para_migrar:
                # Migra para PENDENTE OPERADOR UP
                cursor.execute("""
                    UPDATE pendencia 
                    SET status = 'PENDENTE OPERADOR UP' 
                    WHERE id = ?
                """, (pendencia_id,))
            
            conn.commit()
            print("✅ Pendências migradas para novo fluxo!")
        
        conn.close()
        print("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migração do banco de dados...")
    migrate_database() 