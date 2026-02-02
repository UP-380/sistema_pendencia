import os
import sqlite3
import shutil
from datetime import datetime

# Configurações de Caminho
BASE_DIR = os.getcwd()
DB_FILE = 'instance/pendencias.db'
BACKUP_NAME = f"instance/pendencias_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def conectar():
    if not os.path.exists(DB_FILE):
        print(f"❌ Erro: Banco de dados não encontrado em {DB_FILE}")
        return None
    return sqlite3.connect(DB_FILE)

def migrar():
    print(f"🚀 Iniciando Migração Definitiva para Produção...")
    
    # --- PASSO 1: BACKUP DE SEGURANÇA ---
    print(f"📦 Criando backup de segurança em: {BACKUP_NAME}...")
    try:
        shutil.copy2(DB_FILE, BACKUP_NAME)
        print("✅ Backup concluído com sucesso!")
    except Exception as e:
        print(f"❌ FALHA CRÍTICA NO BACKUP: {e}")
        return

    conn = conectar()
    if not conn: return
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # --- PASSO 2: ALINHAMENTO DE ESTRUTURA (TABELA PENDENCIA) ---
        print("🔍 Verificando se faltam colunas na tabela 'pendencia'...")
        cursor.execute("PRAGMA table_info(pendencia)")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        
        # Estrutura Sagrada (Conforme Localhost)
        colunas_necessarias = {
            "banco": "VARCHAR(50)",
            "data": "DATE",
            "data_abertura": "DATETIME",
            "natureza_operacao": "VARCHAR(500)",
            "codigo_lancamento": "VARCHAR(64)",
            "data_competencia": "DATE",
            "data_baixa": "DATE",
            "natureza_sistema": "VARCHAR(120)",
            "tipo_credito_debito": "VARCHAR(10)"
        }
        
        for col_nome, col_tipo in colunas_necessarias.items():
            if col_nome not in colunas_existentes:
                print(f"   ➕ Adicionando coluna: {col_nome}")
                cursor.execute(f"ALTER TABLE pendencia ADD COLUMN {col_nome} {col_tipo}")

        # --- PASSO 3: PARAMETRIZAÇÃO VISUAL DOS SEGMENTOS ---
        print("🎨 Atualizando identidade visual dos Segmentos...")
        
        # Mapeamento baseado nos nomes REAIS encontrados na sua VPS
        estilo_segmentos = {
            'FUNERÁRIA': ('#1B365D', 'heart'),
            'PROTEÇÃO VEICULAR': ('#008c6a', 'shield'),
            'FARMÁCIA': ('#d32f2f', 'medkit'),
            'EDUCACIONAL': ('#1976d2', 'graduation-cap'),
            'LOGISTICA E TRANSPORTE': ('#f57c00', 'truck'),
            'SUPERMERCADO': ('#388e3c', 'shopping-cart'),
            'SOFTWARE E DESENVOLVIMENTO': ('#455a64', 'code'),
            'EVENTOS': ('#7b1fa2', 'calendar-star'),
            'AGRONEGOCIO': ('#689f38', 'leaf'),
            'SAUDE': ('#00bcd4', 'user-md'),
            'ACADEMIA': ('#e64a19', 'dumbbell'),
            'ROUPAS E ACESSORIOS': ('#c2185b', 'tshirt'),
            'ARQUITETURA': ('#5d4037', 'pencil-ruler')
        }

        for nome, (cor, icone) in estilo_segmentos.items():
            cursor.execute("UPDATE segmento SET cor = ?, icone = ? WHERE nome = ?", (cor, icone, nome))

        # --- PASSO 4: NORMALIZAÇÃO DE DADOS ---
        print("🧹 Normalizando dados antigos (2159 registros)...")
        
        # Garante que status não fiquem vazios
        cursor.execute("UPDATE pendencia SET status = 'PENDENTE CLIENTE' WHERE status IS NULL OR status = ''")
        
        # Inicializa data_abertura para registros que não possuem (usando a data da pendência como base se possível)
        cursor.execute("UPDATE pendencia SET data_abertura = data || ' 00:00:00' WHERE data_abertura IS NULL AND data IS NOT NULL")
        cursor.execute("UPDATE pendencia SET data_abertura = CURRENT_TIMESTAMP WHERE data_abertura IS NULL")

        # --- PASSO 5: PERFORMANCE ---
        print("⚡ Criando índices para o novo Dashboard...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pend_empresa_status ON pendencia(empresa, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pend_status_tipo ON pendencia(status, tipo_pendencia)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa_segmento_id ON empresa(segmento_id)")

        conn.commit()
        print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"💎 Todos os dados foram preservados e o banco agora segue o modelo sagrado.")
        print(f"ℹ️ Backup original mantido em: {BACKUP_NAME}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO DURANTE A MIGRAÇÃO: {e}")
        print("⚠️ O banco não foi alterado. Verifique o erro acima.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrar()
