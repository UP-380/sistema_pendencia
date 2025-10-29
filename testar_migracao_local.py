"""
TESTE LOCAL DA MIGRAÇÃO - Sistema UP380

Este script testa a migração em uma CÓPIA do banco de produção
para garantir que tudo funcionará antes de aplicar em produção.

USO:
1. Copie seu banco de produção para: instance/pendencias_teste.db
2. Execute: python testar_migracao_local.py
3. Verifique se não há erros
4. Se tudo OK, pode aplicar em produção!
"""

import sqlite3
import os
import sys
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Usar banco de teste
DB_PATH = 'instance/pendencias_teste.db'

print("=" * 80)
print("TESTE LOCAL DE MIGRAÇÃO - Sistema UP380")
print("=" * 80)
print()

# Verificar se existe banco de teste
if not os.path.exists(DB_PATH):
    print("❌ Banco de teste não encontrado!")
    print()
    print("PARA CRIAR O BANCO DE TESTE:")
    print()
    print("1. Se tiver acesso ao banco de produção:")
    print("   - Copie: instance/pendencias.db")
    print("   - Para: instance/pendencias_teste.db")
    print()
    print("2. Ou baixe da VPS:")
    print("   scp usuario@VPS:~/sistema_pendencia/instance/pendencias.db instance/pendencias_teste.db")
    print()
    print("3. Depois execute novamente:")
    print("   python testar_migracao_local.py")
    print()
    sys.exit(1)

print(f"✅ Banco de teste encontrado: {DB_PATH}")
print()

# Importar o script de migração
import importlib.util
spec = importlib.util.spec_from_file_location("migracao", "migracao_producao_completa.py")
migracao = importlib.util.module_from_spec(spec)
sys.modules["migracao"] = migracao
spec.loader.exec_module(migracao)

# Alterar o caminho do banco no módulo de migração
migracao.DB_PATH = DB_PATH

# Executar teste
print("🧪 Iniciando teste de migração...")
print()

sucesso = migracao.main()

if sucesso:
    print()
    print("=" * 80)
    print("✅ TESTE DE MIGRAÇÃO CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print()
    print("📊 Estatísticas do banco de teste:")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Estatísticas
    cursor = conn.execute("SELECT COUNT(*) FROM segmento")
    print(f"   Segmentos: {cursor.fetchone()[0]}")
    
    cursor = conn.execute("SELECT COUNT(*) FROM empresa")
    print(f"   Empresas: {cursor.fetchone()[0]}")
    
    cursor = conn.execute("SELECT COUNT(*) FROM empresa WHERE segmento_id IS NOT NULL")
    print(f"   Empresas vinculadas: {cursor.fetchone()[0]}")
    
    cursor = conn.execute("SELECT COUNT(*) FROM pendencia")
    print(f"   Pendências: {cursor.fetchone()[0]}")
    
    conn.close()
    
    print()
    print("✅ A migração está PRONTA para ser aplicada em produção!")
    print()
    print("PRÓXIMOS PASSOS:")
    print("1. Faça commit e push para GitHub")
    print("2. Na VPS, execute: python3 migracao_producao_completa.py")
    print()
else:
    print()
    print("=" * 80)
    print("❌ TESTE DE MIGRAÇÃO FALHOU!")
    print("=" * 80)
    print()
    print("⚠️  NÃO aplique em produção até corrigir os erros!")
    print()
    print("Verifique:")
    print("1. Mensagens de erro acima")
    print("2. Estrutura do banco")
    print("3. Compatibilidade dos scripts")
    print()


