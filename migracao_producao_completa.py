"""
MIGRAÇÃO COMPLETA PARA PRODUÇÃO - Sistema UP380
Data: 28/10/2025

Este script aplica TODAS as mudanças necessárias no banco de dados de produção:
1. Adiciona tabela de segmentos
2. Adiciona campo segmento_id em empresa
3. Migra empresas existentes para segmentos
4. Verifica/adiciona campo data_abertura em pendencia
5. Valida integridade dos dados

IMPORTANTE: Faça backup antes de executar!
"""

import sqlite3
from datetime import datetime
import os
import sys

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Caminho do banco (ajuste se necessário)
DB_PATH = 'instance/pendencias.db'

# Estrutura de segmentos
ESTRUTURA_SEGMENTOS = {
    "ALIANZE - Contabilidade e Consultoria": [
        "ALIANZE",
        "ALIANZE PARTICIPAÇÕES",
        "LM MARCELO"
    ],
    "7 MARES - Associação Social": [
        "7 MARES ASSOCIAÇÃO"
    ],
    "CEASB - Comércio e Serviços": [
        "CEASB COMÉRCIO E SERVIÇOS"
    ],
    "ISBB - Instituto Social": [
        "ISBB - INSTITUTO SOCIAL BEIRA MAR"
    ],
    "STYLLUS - Moda e Varejo": [
        "STYLLUS"
    ]
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def fazer_backup(db_path):
    """Cria backup do banco antes da migração"""
    if not os.path.exists(db_path):
        print(f"❌ Banco não encontrado: {db_path}")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_path = f"{backup_dir}/pendencias_backup_{timestamp}.db"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"✅ Backup criado: {backup_path} ({size_mb:.2f} MB)")
        return backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return None

def conectar_banco(db_path):
    """Conecta ao banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print(f"✅ Conectado ao banco: {db_path}")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

def tabela_existe(conn, nome_tabela):
    """Verifica se tabela existe"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (nome_tabela,)
    )
    return cursor.fetchone() is not None

def coluna_existe(conn, tabela, coluna):
    """Verifica se coluna existe em uma tabela"""
    cursor = conn.execute(f"PRAGMA table_info({tabela})")
    colunas = [row[1] for row in cursor.fetchall()]
    return coluna in colunas

# ============================================================================
# MIGRAÇÕES
# ============================================================================

def migrar_1_criar_tabela_segmento(conn):
    """Migração 1: Criar tabela de segmentos"""
    print("\n📦 Migração 1: Criando tabela 'segmento'...")
    
    if tabela_existe(conn, 'segmento'):
        print("   ⚠️  Tabela 'segmento' já existe, pulando...")
        return True
    
    try:
        conn.execute("""
            CREATE TABLE segmento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                cor TEXT DEFAULT '#1F4E78',
                icone TEXT DEFAULT 'building',
                ativo BOOLEAN DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("   ✅ Tabela 'segmento' criada com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar tabela: {e}")
        return False

def migrar_2_adicionar_campo_segmento_empresa(conn):
    """Migração 2: Adicionar campo segmento_id em empresa"""
    print("\n📦 Migração 2: Adicionando campo 'segmento_id' em 'empresa'...")
    
    if coluna_existe(conn, 'empresa', 'segmento_id'):
        print("   ⚠️  Coluna 'segmento_id' já existe, pulando...")
        return True
    
    try:
        conn.execute("ALTER TABLE empresa ADD COLUMN segmento_id INTEGER")
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_empresa_segmento 
            ON empresa(segmento_id)
        """)
        conn.commit()
        print("   ✅ Campo 'segmento_id' adicionado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao adicionar campo: {e}")
        return False

def migrar_3_popular_segmentos(conn):
    """Migração 3: Popular tabela de segmentos"""
    print("\n📦 Migração 3: Populando segmentos...")
    
    try:
        # Verificar se já tem segmentos
        cursor = conn.execute("SELECT COUNT(*) FROM segmento")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"   ⚠️  Já existem {count} segmentos, pulando...")
            return True
        
        # Inserir segmentos
        cores = ['#1F4E78', '#2E7D32', '#C62828', '#F57C00', '#7B1FA2']
        
        for idx, (segmento_nome, empresas) in enumerate(ESTRUTURA_SEGMENTOS.items()):
            cor = cores[idx % len(cores)]
            conn.execute(
                "INSERT INTO segmento (nome, descricao, cor) VALUES (?, ?, ?)",
                (segmento_nome, f"Segmento com {len(empresas)} empresa(s)", cor)
            )
        
        conn.commit()
        print(f"   ✅ {len(ESTRUTURA_SEGMENTOS)} segmentos criados!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao popular segmentos: {e}")
        conn.rollback()
        return False

def migrar_4_vincular_empresas_segmentos(conn):
    """Migração 4: Vincular empresas existentes aos segmentos"""
    print("\n📦 Migração 4: Vinculando empresas aos segmentos...")
    
    try:
        empresas_vinculadas = 0
        empresas_nao_encontradas = []
        
        for segmento_nome, empresas_lista in ESTRUTURA_SEGMENTOS.items():
            # Buscar ID do segmento
            cursor = conn.execute(
                "SELECT id FROM segmento WHERE nome = ?",
                (segmento_nome,)
            )
            segmento_row = cursor.fetchone()
            
            if not segmento_row:
                print(f"   ⚠️  Segmento '{segmento_nome}' não encontrado")
                continue
            
            segmento_id = segmento_row[0]
            
            # Vincular cada empresa
            for empresa_nome in empresas_lista:
                cursor = conn.execute(
                    "SELECT id, segmento_id FROM empresa WHERE nome = ?",
                    (empresa_nome,)
                )
                empresa_row = cursor.fetchone()
                
                if empresa_row:
                    if empresa_row[1] is None:  # Só atualiza se não tiver segmento
                        conn.execute(
                            "UPDATE empresa SET segmento_id = ? WHERE id = ?",
                            (segmento_id, empresa_row[0])
                        )
                        empresas_vinculadas += 1
                        print(f"   ✓ {empresa_nome} → {segmento_nome}")
                    else:
                        print(f"   ⚠️  {empresa_nome} já tem segmento")
                else:
                    empresas_nao_encontradas.append(empresa_nome)
        
        conn.commit()
        print(f"\n   ✅ {empresas_vinculadas} empresas vinculadas!")
        
        if empresas_nao_encontradas:
            print(f"   ⚠️  {len(empresas_nao_encontradas)} empresas não encontradas:")
            for emp in empresas_nao_encontradas:
                print(f"      - {emp}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erro ao vincular empresas: {e}")
        conn.rollback()
        return False

def migrar_5_verificar_campo_data_abertura(conn):
    """Migração 5: Verificar/adicionar campo data_abertura em pendencia"""
    print("\n📦 Migração 5: Verificando campo 'data_abertura' em 'pendencia'...")
    
    if coluna_existe(conn, 'pendencia', 'data_abertura'):
        print("   ✅ Campo 'data_abertura' já existe!")
        return True
    
    try:
        print("   ⚠️  Campo 'data_abertura' não existe, adicionando...")
        conn.execute("""
            ALTER TABLE pendencia 
            ADD COLUMN data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        
        # Atualizar registros existentes com data atual
        conn.execute("""
            UPDATE pendencia 
            SET data_abertura = CURRENT_TIMESTAMP 
            WHERE data_abertura IS NULL
        """)
        
        conn.commit()
        print("   ✅ Campo 'data_abertura' adicionado!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao adicionar campo: {e}")
        return False

def migrar_6_validar_integridade(conn):
    """Migração 6: Validar integridade dos dados"""
    print("\n📦 Migração 6: Validando integridade dos dados...")
    
    try:
        # Contar segmentos
        cursor = conn.execute("SELECT COUNT(*) FROM segmento")
        total_segmentos = cursor.fetchone()[0]
        print(f"   ✓ Segmentos: {total_segmentos}")
        
        # Contar empresas
        cursor = conn.execute("SELECT COUNT(*) FROM empresa")
        total_empresas = cursor.fetchone()[0]
        print(f"   ✓ Empresas: {total_empresas}")
        
        # Contar empresas com segmento
        cursor = conn.execute(
            "SELECT COUNT(*) FROM empresa WHERE segmento_id IS NOT NULL"
        )
        empresas_com_segmento = cursor.fetchone()[0]
        print(f"   ✓ Empresas vinculadas: {empresas_com_segmento}/{total_empresas}")
        
        # Contar pendências
        cursor = conn.execute("SELECT COUNT(*) FROM pendencia")
        total_pendencias = cursor.fetchone()[0]
        print(f"   ✓ Pendências: {total_pendencias}")
        
        # Contar pendências com data_abertura
        cursor = conn.execute(
            "SELECT COUNT(*) FROM pendencia WHERE data_abertura IS NOT NULL"
        )
        pendencias_com_data = cursor.fetchone()[0]
        print(f"   ✓ Pendências com data_abertura: {pendencias_com_data}/{total_pendencias}")
        
        print("   ✅ Validação concluída!")
        return True
    except Exception as e:
        print(f"   ❌ Erro na validação: {e}")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("MIGRAÇÃO COMPLETA PARA PRODUÇÃO - Sistema UP380")
    print("=" * 80)
    print()
    
    # Verificar se banco existe
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco não encontrado: {DB_PATH}")
        print(f"   Certifique-se de estar na pasta correta!")
        return False
    
    # Fazer backup
    print("🔒 Criando backup de segurança...")
    backup_path = fazer_backup(DB_PATH)
    if not backup_path:
        print("❌ Falha ao criar backup. Abortando migração.")
        return False
    
    # Conectar ao banco
    conn = conectar_banco(DB_PATH)
    if not conn:
        return False
    
    try:
        # Executar migrações em sequência
        migrações = [
            migrar_1_criar_tabela_segmento,
            migrar_2_adicionar_campo_segmento_empresa,
            migrar_3_popular_segmentos,
            migrar_4_vincular_empresas_segmentos,
            migrar_5_verificar_campo_data_abertura,
            migrar_6_validar_integridade
        ]
        
        print("\n🚀 Iniciando migrações...\n")
        
        for migração in migrações:
            if not migração(conn):
                print(f"\n❌ Migração falhou: {migração.__name__}")
                print(f"💾 Backup disponível em: {backup_path}")
                conn.close()
                return False
        
        print("\n" + "=" * 80)
        print("✅ TODAS AS MIGRAÇÕES CONCLUÍDAS COM SUCESSO!")
        print("=" * 80)
        print(f"\n💾 Backup salvo em: {backup_path}")
        print("🎉 Sistema atualizado e pronto para uso!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        print(f"💾 Backup disponível em: {backup_path}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)


