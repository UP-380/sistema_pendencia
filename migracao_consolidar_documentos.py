image.png"""
MIGRAÇÃO: CONSOLIDAR TIPOS DE DOCUMENTOS - Sistema UP380
Data: 28/10/2025

Este script consolida os tipos antigos de pendências de documentos:
- "NOTA FISCAL NÃO ANEXADA" → "DOCUMENTO NÃO ANEXADO"
- "NOTA FISCAL NÃO IDENTIFICADA" → "DOCUMENTO NÃO ANEXADO"

IMPORTANTE: 
- Faça backup antes de executar!
- Pode ser executado múltiplas vezes (é idempotente)
- Preserva todos os outros dados das pendências

USO:
    python migracao_consolidar_documentos.py
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

# Mapeamento de tipos antigos para novo
TIPOS_PARA_MIGRAR = {
    "NOTA FISCAL NÃO ANEXADA": "DOCUMENTO NÃO ANEXADO",
    "NOTA FISCAL NÃO IDENTIFICADA": "DOCUMENTO NÃO ANEXADO",
    # Variações possíveis (case sensitive)
    "Nota Fiscal Não Anexada": "DOCUMENTO NÃO ANEXADO",
    "Nota Fiscal Não Identificada": "DOCUMENTO NÃO ANEXADO",
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
    
    backup_path = f"{backup_dir}/pendencias_backup_docs_{timestamp}.db"
    
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

# ============================================================================
# ANÁLISE PRÉ-MIGRAÇÃO
# ============================================================================

def analisar_tipos_pendencias(conn):
    """Analisa tipos de pendências existentes"""
    print("\n📊 Analisando tipos de pendências no banco...\n")
    
    try:
        # Buscar todos os tipos únicos
        cursor = conn.execute("""
            SELECT tipo_pendencia, COUNT(*) as quantidade
            FROM pendencia
            GROUP BY tipo_pendencia
            ORDER BY quantidade DESC
        """)
        
        tipos_encontrados = cursor.fetchall()
        
        print("Tipos existentes no banco:")
        print("-" * 60)
        
        total_para_migrar = 0
        tipos_a_migrar = []
        
        for row in tipos_encontrados:
            tipo = row['tipo_pendencia']
            qtd = row['quantidade']
            
            # Verificar se é tipo a migrar
            if tipo in TIPOS_PARA_MIGRAR:
                marcador = "→ SERÁ MIGRADO"
                total_para_migrar += qtd
                tipos_a_migrar.append((tipo, qtd))
            else:
                marcador = ""
            
            print(f"  {tipo:<40} | {qtd:>5} registros {marcador}")
        
        print("-" * 60)
        print(f"TOTAL: {len(tipos_encontrados)} tipos diferentes")
        print()
        
        return total_para_migrar, tipos_a_migrar
        
    except Exception as e:
        print(f"❌ Erro ao analisar: {e}")
        return 0, []

# ============================================================================
# MIGRAÇÃO
# ============================================================================

def migrar_tipos_documentos(conn):
    """Migra os tipos de documentos antigos para o novo"""
    print("\n🔄 Iniciando migração de tipos de documentos...\n")
    
    try:
        total_migrado = 0
        detalhes_migracao = []
        
        for tipo_antigo, tipo_novo in TIPOS_PARA_MIGRAR.items():
            # Contar quantos registros têm esse tipo
            cursor = conn.execute(
                "SELECT COUNT(*) as qtd FROM pendencia WHERE tipo_pendencia = ?",
                (tipo_antigo,)
            )
            qtd = cursor.fetchone()['qtd']
            
            if qtd > 0:
                # Atualizar para o novo tipo
                cursor = conn.execute("""
                    UPDATE pendencia 
                    SET tipo_pendencia = ?
                    WHERE tipo_pendencia = ?
                """, (tipo_novo, tipo_antigo))
                
                registros_atualizados = cursor.rowcount
                total_migrado += registros_atualizados
                
                print(f"  ✓ {tipo_antigo}")
                print(f"    → {tipo_novo}")
                print(f"    Migrados: {registros_atualizados} registros")
                print()
                
                detalhes_migracao.append({
                    'tipo_antigo': tipo_antigo,
                    'tipo_novo': tipo_novo,
                    'quantidade': registros_atualizados
                })
        
        # Commit das mudanças
        conn.commit()
        
        return total_migrado, detalhes_migracao
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
        return 0, []

# ============================================================================
# VALIDAÇÃO PÓS-MIGRAÇÃO
# ============================================================================

def validar_migracao(conn, detalhes_migracao):
    """Valida se a migração foi bem-sucedida"""
    print("\n🔍 Validando migração...\n")
    
    try:
        # Verificar se ainda existem tipos antigos
        tipos_antigos_restantes = []
        
        for tipo_antigo in TIPOS_PARA_MIGRAR.keys():
            cursor = conn.execute(
                "SELECT COUNT(*) as qtd FROM pendencia WHERE tipo_pendencia = ?",
                (tipo_antigo,)
            )
            qtd = cursor.fetchone()['qtd']
            
            if qtd > 0:
                tipos_antigos_restantes.append((tipo_antigo, qtd))
        
        if tipos_antigos_restantes:
            print("⚠️  ATENÇÃO: Ainda existem tipos antigos no banco:")
            for tipo, qtd in tipos_antigos_restantes:
                print(f"   - {tipo}: {qtd} registros")
            return False
        
        # Verificar quantidade do novo tipo
        cursor = conn.execute(
            "SELECT COUNT(*) as qtd FROM pendencia WHERE tipo_pendencia = ?",
            ("DOCUMENTO NÃO ANEXADO",)
        )
        qtd_novo_tipo = cursor.fetchone()['qtd']
        
        print(f"✅ Tipo consolidado: DOCUMENTO NÃO ANEXADO")
        print(f"   Total de registros: {qtd_novo_tipo}")
        print()
        
        # Verificar integridade dos dados migrados
        print("Verificando integridade dos dados migrados:")
        
        # Contar registros com campos importantes não-nulos
        cursor = conn.execute("""
            SELECT COUNT(*) as total
            FROM pendencia
            WHERE tipo_pendencia = 'DOCUMENTO NÃO ANEXADO'
        """)
        total = cursor.fetchone()['total']
        
        cursor = conn.execute("""
            SELECT COUNT(*) as com_empresa
            FROM pendencia
            WHERE tipo_pendencia = 'DOCUMENTO NÃO ANEXADO'
            AND empresa IS NOT NULL AND empresa != ''
        """)
        com_empresa = cursor.fetchone()['com_empresa']
        
        cursor = conn.execute("""
            SELECT COUNT(*) as com_valor
            FROM pendencia
            WHERE tipo_pendencia = 'DOCUMENTO NÃO ANEXADO'
            AND valor IS NOT NULL AND valor > 0
        """)
        com_valor = cursor.fetchone()['com_valor']
        
        print(f"  ✓ Total de registros: {total}")
        print(f"  ✓ Com empresa: {com_empresa}/{total}")
        print(f"  ✓ Com valor: {com_valor}/{total}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False

# ============================================================================
# RELATÓRIO FINAL
# ============================================================================

def gerar_relatorio(total_migrado, detalhes_migracao, tempo_execucao):
    """Gera relatório final da migração"""
    print("\n" + "=" * 80)
    print("RELATÓRIO DE MIGRAÇÃO - CONSOLIDAÇÃO DE TIPOS DE DOCUMENTOS")
    print("=" * 80)
    print()
    
    if total_migrado == 0:
        print("ℹ️  Nenhum registro precisou ser migrado.")
        print("   Possíveis razões:")
        print("   - Migração já foi executada anteriormente")
        print("   - Não existem registros com os tipos antigos")
        print()
        return
    
    print(f"✅ Migração concluída com sucesso!")
    print()
    print(f"📊 Estatísticas:")
    print(f"   Total de registros migrados: {total_migrado}")
    print(f"   Tempo de execução: {tempo_execucao:.2f} segundos")
    print()
    
    print("📋 Detalhes da migração:")
    for detalhe in detalhes_migracao:
        print(f"   • {detalhe['tipo_antigo']}")
        print(f"     → {detalhe['tipo_novo']}")
        print(f"     {detalhe['quantidade']} registros")
        print()
    
    print("🎯 Tipo consolidado:")
    print("   DOCUMENTO NÃO ANEXADO")
    print()
    
    print("=" * 80)

# ============================================================================
# MAIN
# ============================================================================

def main():
    import time
    
    print("=" * 80)
    print("MIGRAÇÃO: CONSOLIDAÇÃO DE TIPOS DE DOCUMENTOS")
    print("Sistema UP380")
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
    
    print()
    
    # Conectar ao banco
    conn = conectar_banco(DB_PATH)
    if not conn:
        return False
    
    try:
        inicio = time.time()
        
        # Análise pré-migração
        total_para_migrar, tipos_a_migrar = analisar_tipos_pendencias(conn)
        
        if total_para_migrar == 0:
            print("\nℹ️  Nenhum registro para migrar.")
            print("   Os tipos antigos não foram encontrados no banco.")
            print("   Possível que a migração já tenha sido executada.")
            conn.close()
            return True
        
        print(f"\n⚠️  Serão migrados {total_para_migrar} registros")
        print(f"   De {len(tipos_a_migrar)} tipo(s) diferente(s)")
        print()
        
        # Confirmar migração (em produção, você pode querer adicionar input do usuário)
        print("🚀 Iniciando migração...")
        
        # Executar migração
        total_migrado, detalhes_migracao = migrar_tipos_documentos(conn)
        
        if total_migrado == 0:
            print("❌ Nenhum registro foi migrado.")
            conn.close()
            return False
        
        # Validar
        validacao_ok = validar_migracao(conn, detalhes_migracao)
        
        if not validacao_ok:
            print("⚠️  Validação identificou problemas. Verifique acima.")
        
        fim = time.time()
        tempo_execucao = fim - inicio
        
        # Relatório
        gerar_relatorio(total_migrado, detalhes_migracao, tempo_execucao)
        
        print(f"💾 Backup salvo em: {backup_path}")
        print("✅ Migração concluída!")
        print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        print(f"💾 Backup disponível em: {backup_path}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)


