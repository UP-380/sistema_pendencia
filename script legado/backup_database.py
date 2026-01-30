#!/usr/bin/env python3
"""
Script para fazer backup do banco de dados SQLite
"""

import os
import shutil
from datetime import datetime
import sqlite3

def fazer_backup():
    """Realiza o backup do banco de dados com timestamp"""
    
    # Diretório de backup
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Caminho do banco de dados
    db_path = 'instance/pendencias.db'
    
    # Verificar se o banco existe
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return False
    
    try:
        # Gerar nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'pendencias_backup_{timestamp}.db')
        
        # Verificar integridade do banco antes do backup
        print("🔍 Verificando integridade do banco de dados...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        if result != "ok":
            print("❌ Erro na integridade do banco de dados!")
            return False
            
        conn.close()
        
        # Realizar o backup
        print(f"📦 Fazendo backup do banco de dados...")
        shutil.copy2(db_path, backup_file)
        
        # Verificar se o backup foi criado
        if os.path.exists(backup_file):
            tamanho = os.path.getsize(backup_file) / (1024 * 1024)  # Tamanho em MB
            print(f"✅ Backup criado com sucesso em: {backup_file}")
            print(f"📊 Tamanho do backup: {tamanho:.2f} MB")
            return True
        else:
            print("❌ Erro ao criar arquivo de backup")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o backup: {e}")
        return False

if __name__ == "__main__":
    print("=== Backup do Banco de Dados ===")
    fazer_backup()