#!/usr/bin/env python3
"""
Script de Migração do Banco de Dados
Executa o arquivo migrate_reestruturar_banco.sql
"""

import sqlite3
import os
from datetime import datetime

def fazer_backup():
    """Cria backup do banco antes da migração"""
    backup_name = f"pendencias_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists('pendencias.db'):
        import shutil
        shutil.copy2('pendencias.db', backup_name)
        print(f"✅ Backup criado: {backup_name}")
        return backup_name
    else:
        print("⚠️  Banco de dados não encontrado!")
        return None

def executar_migração():
    """Executa o script SQL de migração"""
    print("="*80)
    print("MIGRAÇÃO DO BANCO DE DADOS")
    print("Sistema UP380 - Gestão de Pendências")
    print("="*80)
    
    # Fazer backup
    print("\n1. Criando backup...")
    backup = fazer_backup()
    
    if not backup:
        print("❌ Não foi possível criar backup. Abortando migração.")
        return False
    
    # Conectar ao banco
    print("\n2. Conectando ao banco de dados...")
    try:
        conn = sqlite3.connect('pendencias.db')
        cursor = conn.cursor()
        print("✅ Conectado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # Ler script SQL
    print("\n3. Lendo script de migração...")
    try:
        with open('migrate_reestruturar_banco.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        print("✅ Script carregado!")
    except Exception as e:
        print(f"❌ Erro ao ler script: {e}")
        conn.close()
        return False
    
    # Executar migração
    print("\n4. Executando migração...")
    try:
        # Executar cada comando separadamente
        comandos = sql_script.split(';')
        total = len(comandos)
        executados = 0
        
        for i, comando in enumerate(comandos, 1):
            comando = comando.strip()
            if comando and not comando.startswith('--'):
                try:
                    cursor.execute(comando)
                    executados += 1
                except sqlite3.OperationalError as e:
                    # Ignorar erros de "column already exists"
                    if "duplicate column name" in str(e).lower():
                        print(f"  ⏭️  Coluna já existe, pulando...")
                    elif "already exists" in str(e).lower():
                        print(f"  ⏭️  Índice já existe, pulando...")
                    else:
                        print(f"  ⚠️  Aviso: {e}")
                except Exception as e:
                    print(f"  ❌ Erro no comando {i}: {e}")
        
        conn.commit()
        print(f"✅ Migração concluída! ({executados}/{total} comandos executados)")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
        conn.close()
        return False
    
    # Verificar resultado
    print("\n5. Verificando resultado...")
    try:
        # Verificar se campo foi adicionado
        cursor.execute("PRAGMA table_info(pendencia)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if 'tipo_credito_debito' in colunas:
            print("  ✅ Campo 'tipo_credito_debito' adicionado com sucesso!")
        else:
            print("  ⚠️  Campo 'tipo_credito_debito' não foi adicionado")
        
        # Verificar índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indices = [row[0] for row in cursor.fetchall()]
        print(f"  ✅ {len(indices)} índices criados")
        
        # Estatísticas
        cursor.execute("SELECT COUNT(*) FROM pendencia")
        total_pendencias = cursor.fetchone()[0]
        print(f"  ✅ Total de pendências: {total_pendencias}")
        
    except Exception as e:
        print(f"  ⚠️  Erro na verificação: {e}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print(f"\n📁 Backup salvo em: {backup}")
    print("📝 Para reverter: cp {backup} pendencias.db")
    
    return True

if __name__ == '__main__':
    try:
        sucesso = executar_migração()
        if not sucesso:
            print("\n❌ Migração falhou! Verifique os erros acima.")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migração cancelada pelo usuário!")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
