#!/usr/bin/env python3
"""
Script de Análise Completa do Banco de Dados
Sistema de Pendências UP380

Este script analisa:
- Estrutura de todas as tabelas
- Integridade referencial
- Índices existentes
- Constraints e validações
- Dados inconsistentes
- Sugestões de melhorias
"""

import sqlite3
import json
from datetime import datetime

def conectar_banco():
    """Conecta ao banco de dados"""
    try:
        conn = sqlite3.connect('pendencias.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def listar_tabelas(conn):
    """Lista todas as tabelas do banco"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def analisar_estrutura_tabela(conn, tabela):
    """Analisa a estrutura de uma tabela"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"TABELA: {tabela}")
    print(f"{'='*80}")
    print(f"{'Nome':<30} {'Tipo':<15} {'NULL':<8} {'Default':<15} {'PK':<5}")
    print(f"{'-'*80}")
    
    for col in colunas:
        nome = col[1]
        tipo = col[2]
        not_null = "NOT NULL" if col[3] == 1 else "NULL"
        default = col[4] if col[4] else "-"
        pk = "PK" if col[5] > 0 else ""
        print(f"{nome:<30} {tipo:<15} {not_null:<8} {str(default):<15} {pk:<5}")
    
    return colunas

def verificar_indices(conn, tabela):
    """Verifica índices de uma tabela"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({tabela})")
    indices = cursor.fetchall()
    
    if indices:
        print(f"\n📊 Índices:")
        for idx in indices:
            nome_idx = idx[1]
            unique = "UNIQUE" if idx[2] == 1 else "NON-UNIQUE"
            cursor.execute(f"PRAGMA index_info({nome_idx})")
            colunas_idx = cursor.fetchall()
            colunas_nomes = [col[2] for col in colunas_idx]
            print(f"  • {nome_idx} ({unique}): {', '.join(colunas_nomes)}")
    else:
        print(f"\n⚠️  Nenhum índice encontrado (além da PK)")

def verificar_foreign_keys(conn, tabela):
    """Verifica foreign keys de uma tabela"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({tabela})")
    fks = cursor.fetchall()
    
    if fks:
        print(f"\n🔗 Foreign Keys:")
        for fk in fks:
            tabela_ref = fk[2]
            coluna_local = fk[3]
            coluna_ref = fk[4]
            print(f"  • {coluna_local} → {tabela_ref}.{coluna_ref}")
    else:
        print(f"\n⚠️  Nenhuma foreign key definida")

def contar_registros(conn, tabela):
    """Conta registros de uma tabela"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    total = cursor.fetchone()[0]
    print(f"\n📈 Total de registros: {total}")
    return total

def analisar_pendencias(conn):
    """Análise específica da tabela pendencia"""
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE DETALHADA: PENDENCIAS")
    print(f"{'='*80}")
    
    # Contagem por status
    cursor.execute("""
        SELECT status, COUNT(*) as total 
        FROM pendencia 
        GROUP BY status 
        ORDER BY total DESC
    """)
    print(f"\n📊 Pendências por Status:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]}")
    
    # Contagem por tipo
    cursor.execute("""
        SELECT tipo_pendencia, COUNT(*) as total 
        FROM pendencia 
        GROUP BY tipo_pendencia 
        ORDER BY total DESC
    """)
    print(f"\n📊 Pendências por Tipo:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]}")
    
    # Contagem por empresa
    cursor.execute("""
        SELECT empresa, COUNT(*) as total 
        FROM pendencia 
        GROUP BY empresa 
        ORDER BY total DESC
        LIMIT 10
    """)
    print(f"\n📊 Top 10 Empresas com mais Pendências:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]}")
    
    # Verificar dados inconsistentes
    print(f"\n⚠️  Verificação de Inconsistências:")
    
    # Pendências sem email_cliente
    cursor.execute("SELECT COUNT(*) FROM pendencia WHERE email_cliente IS NULL OR email_cliente = ''")
    sem_email = cursor.fetchone()[0]
    if sem_email > 0:
        print(f"  ❌ {sem_email} pendências SEM email_cliente")
    
    # Pendências sem fornecedor_cliente
    cursor.execute("SELECT COUNT(*) FROM pendencia WHERE fornecedor_cliente IS NULL OR fornecedor_cliente = ''")
    sem_fornecedor = cursor.fetchone()[0]
    if sem_fornecedor > 0:
        print(f"  ❌ {sem_fornecedor} pendências SEM fornecedor_cliente")
    
    # Pendências com valor zero ou negativo
    cursor.execute("SELECT COUNT(*) FROM pendencia WHERE valor <= 0")
    valor_invalido = cursor.fetchone()[0]
    if valor_invalido > 0:
        print(f"  ❌ {valor_invalido} pendências com valor <= 0")
    
    # Pendências sem data
    cursor.execute("SELECT COUNT(*) FROM pendencia WHERE data IS NULL")
    sem_data = cursor.fetchone()[0]
    if sem_data > 0:
        print(f"  ⚠️  {sem_data} pendências SEM data")
    
    # Tokens duplicados
    cursor.execute("""
        SELECT token_acesso, COUNT(*) as total 
        FROM pendencia 
        WHERE token_acesso IS NOT NULL
        GROUP BY token_acesso 
        HAVING COUNT(*) > 1
    """)
    tokens_dup = cursor.fetchall()
    if tokens_dup:
        print(f"  ❌ {len(tokens_dup)} tokens DUPLICADOS (problema crítico!)")

def analisar_usuarios(conn):
    """Análise específica da tabela usuario"""
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE DETALHADA: USUARIOS")
    print(f"{'='*80}")
    
    # Contagem por tipo
    cursor.execute("""
        SELECT tipo, COUNT(*) as total 
        FROM usuario 
        GROUP BY tipo 
        ORDER BY total DESC
    """)
    print(f"\n📊 Usuários por Tipo:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]}")
    
    # Usuários ativos vs inativos
    cursor.execute("""
        SELECT ativo, COUNT(*) as total 
        FROM usuario 
        GROUP BY ativo
    """)
    print(f"\n📊 Usuários por Status:")
    for row in cursor.fetchall():
        status = "Ativo" if row[0] == 1 else "Inativo"
        print(f"  • {status}: {row[1]}")
    
    # Verificar emails duplicados
    cursor.execute("""
        SELECT email, COUNT(*) as total 
        FROM usuario 
        GROUP BY email 
        HAVING COUNT(*) > 1
    """)
    emails_dup = cursor.fetchall()
    if emails_dup:
        print(f"\n  ❌ {len(emails_dup)} emails DUPLICADOS (problema crítico!)")
        for row in emails_dup:
            print(f"     • {row[0]}: {row[1]} ocorrências")

def analisar_empresas(conn):
    """Análise específica da tabela empresa"""
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE DETALHADA: EMPRESAS")
    print(f"{'='*80}")
    
    total = contar_registros(conn, 'empresa')
    
    # Empresas por segmento
    cursor.execute("""
        SELECT s.nome as segmento, COUNT(e.id) as total 
        FROM empresa e
        LEFT JOIN segmento s ON e.segmento_id = s.id
        GROUP BY s.nome
        ORDER BY total DESC
    """)
    print(f"\n📊 Empresas por Segmento:")
    for row in cursor.fetchall():
        segmento = row[0] if row[0] else "Sem Segmento"
        print(f"  • {segmento}: {row[1]}")
    
    # Empresas sem segmento
    cursor.execute("SELECT COUNT(*) FROM empresa WHERE segmento_id IS NULL")
    sem_segmento = cursor.fetchone()[0]
    if sem_segmento > 0:
        print(f"\n  ⚠️  {sem_segmento} empresas SEM segmento definido")

def gerar_relatorio_problemas(conn):
    """Gera relatório de problemas encontrados"""
    cursor = conn.cursor()
    problemas = []
    
    print(f"\n{'='*80}")
    print(f"RELATÓRIO DE PROBLEMAS E SUGESTÕES")
    print(f"{'='*80}")
    
    # 1. Verificar foreign keys não definidas
    print(f"\n🔴 PROBLEMAS CRÍTICOS:")
    
    cursor.execute("PRAGMA foreign_key_list(pendencia)")
    fks_pendencia = cursor.fetchall()
    if not fks_pendencia:
        print(f"  ❌ Tabela 'pendencia' NÃO possui foreign keys definidas")
        print(f"     → Campo 'empresa' deveria referenciar 'empresa.nome'")
        problemas.append("FK: pendencia.empresa → empresa.nome")
    
    cursor.execute("PRAGMA foreign_key_list(log_alteracao)")
    fks_log = cursor.fetchall()
    if not fks_log:
        print(f"  ❌ Tabela 'log_alteracao' NÃO possui foreign keys definidas")
        print(f"     → Campo 'pendencia_id' deveria referenciar 'pendencia.id'")
        problemas.append("FK: log_alteracao.pendencia_id → pendencia.id")
    
    # 2. Verificar índices faltantes
    print(f"\n🟡 OTIMIZAÇÕES RECOMENDADAS:")
    
    cursor.execute("PRAGMA index_list(pendencia)")
    indices_pendencia = [idx[1] for idx in cursor.fetchall()]
    
    indices_recomendados = [
        ("pendencia", "empresa", "Filtros por empresa"),
        ("pendencia", "status", "Filtros por status"),
        ("pendencia", "tipo_pendencia", "Filtros por tipo"),
        ("pendencia", "data_abertura", "Ordenação por data"),
        ("log_alteracao", "pendencia_id", "Joins com pendencia"),
        ("log_alteracao", "data_hora", "Ordenação de logs"),
    ]
    
    for tabela, coluna, motivo in indices_recomendados:
        idx_nome = f"idx_{tabela}_{coluna}"
        if idx_nome not in indices_pendencia:
            print(f"  📊 Criar índice em {tabela}.{coluna} ({motivo})")
            problemas.append(f"INDEX: {tabela}.{coluna}")
    
    # 3. Verificar constraints faltantes
    print(f"\n🟡 CONSTRAINTS RECOMENDADAS:")
    
    print(f"  ✓ CHECK: pendencia.valor > 0")
    print(f"  ✓ CHECK: pendencia.status IN ('PENDENTE CLIENTE', 'PENDENTE OPERADOR UP', 'PENDENTE SUPERVISOR UP', 'RESOLVIDA')")
    print(f"  ✓ CHECK: usuario.tipo IN ('adm', 'supervisor', 'operador', 'cliente')")
    problemas.append("CONSTRAINTS: Adicionar validações CHECK")
    
    return problemas

def gerar_script_correcao(problemas):
    """Gera script SQL de correção"""
    print(f"\n{'='*80}")
    print(f"SCRIPT DE CORREÇÃO SQL")
    print(f"{'='*80}\n")
    
    script = f"""-- Script de Correção do Banco de Dados
-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Sistema de Pendências UP380

-- ============================================
-- 1. HABILITAR FOREIGN KEYS
-- ============================================
PRAGMA foreign_keys = ON;

-- ============================================
-- 2. CRIAR ÍNDICES PARA PERFORMANCE
-- ============================================

-- Índices na tabela pendencia
CREATE INDEX IF NOT EXISTS idx_pendencia_empresa ON pendencia(empresa);
CREATE INDEX IF NOT EXISTS idx_pendencia_status ON pendencia(status);
CREATE INDEX IF NOT EXISTS idx_pendencia_tipo_pendencia ON pendencia(tipo_pendencia);
CREATE INDEX IF NOT EXISTS idx_pendencia_data_abertura ON pendencia(data_abertura);
CREATE INDEX IF NOT EXISTS idx_pendencia_email_cliente ON pendencia(email_cliente);
CREATE INDEX IF NOT EXISTS idx_pendencia_token_acesso ON pendencia(token_acesso);

-- Índices na tabela log_alteracao
CREATE INDEX IF NOT EXISTS idx_log_pendencia_id ON log_alteracao(pendencia_id);
CREATE INDEX IF NOT EXISTS idx_log_data_hora ON log_alteracao(data_hora);
CREATE INDEX IF NOT EXISTS idx_log_usuario ON log_alteracao(usuario);

-- Índices na tabela usuario
CREATE INDEX IF NOT EXISTS idx_usuario_tipo ON usuario(tipo);
CREATE INDEX IF NOT EXISTS idx_usuario_ativo ON usuario(ativo);

-- Índices na tabela empresa
CREATE INDEX IF NOT EXISTS idx_empresa_segmento_id ON empresa(segmento_id);
CREATE INDEX IF NOT EXISTS idx_empresa_nome ON empresa(nome);

-- ============================================
-- 3. VERIFICAR DADOS INCONSISTENTES
-- ============================================

-- Listar pendências com valor inválido
SELECT 'ATENÇÃO: Pendências com valor <= 0' as alerta, COUNT(*) as total
FROM pendencia WHERE valor <= 0;

-- Listar pendências sem email
SELECT 'ATENÇÃO: Pendências sem email_cliente' as alerta, COUNT(*) as total
FROM pendencia WHERE email_cliente IS NULL OR email_cliente = '';

-- Listar tokens duplicados
SELECT 'CRÍTICO: Tokens duplicados' as alerta, token_acesso, COUNT(*) as total
FROM pendencia
WHERE token_acesso IS NOT NULL
GROUP BY token_acesso
HAVING COUNT(*) > 1;

-- ============================================
-- 4. ADICIONAR CAMPO TIPO_CREDITO_DEBITO
-- ============================================

-- Adicionar nova coluna para Lançamento Não Encontrado em Sistema
ALTER TABLE pendencia ADD COLUMN tipo_credito_debito VARCHAR(10);

-- Criar índice para o novo campo
CREATE INDEX IF NOT EXISTS idx_pendencia_tipo_credito_debito ON pendencia(tipo_credito_debito);

-- ============================================
-- 5. VERIFICAÇÃO FINAL
-- ============================================

-- Contar registros por tabela
SELECT 'pendencia' as tabela, COUNT(*) as total FROM pendencia
UNION ALL
SELECT 'usuario' as tabela, COUNT(*) as total FROM usuario
UNION ALL
SELECT 'empresa' as tabela, COUNT(*) as total FROM empresa
UNION ALL
SELECT 'segmento' as tabela, COUNT(*) as total FROM segmento
UNION ALL
SELECT 'log_alteracao' as tabela, COUNT(*) as total FROM log_alteracao
UNION ALL
SELECT 'importacao' as tabela, COUNT(*) as total FROM importacao;

-- Verificar integridade
PRAGMA integrity_check;
"""
    
    print(script)
    
    # Salvar em arquivo
    with open('correcao_banco.sql', 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"\n✅ Script salvo em: correcao_banco.sql")

def main():
    """Função principal"""
    print(f"{'='*80}")
    print(f"ANÁLISE COMPLETA DO BANCO DE DADOS")
    print(f"Sistema de Pendências UP380")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    conn = conectar_banco()
    if not conn:
        return
    
    try:
        # Listar tabelas
        tabelas = listar_tabelas(conn)
        print(f"\n📋 Tabelas encontradas: {', '.join(tabelas)}")
        
        # Analisar cada tabela
        for tabela in tabelas:
            analisar_estrutura_tabela(conn, tabela)
            verificar_indices(conn, tabela)
            verificar_foreign_keys(conn, tabela)
            contar_registros(conn, tabela)
        
        # Análises específicas
        if 'pendencia' in tabelas:
            analisar_pendencias(conn)
        
        if 'usuario' in tabelas:
            analisar_usuarios(conn)
        
        if 'empresa' in tabelas:
            analisar_empresas(conn)
        
        # Gerar relatório de problemas
        problemas = gerar_relatorio_problemas(conn)
        
        # Gerar script de correção
        gerar_script_correcao(problemas)
        
        print(f"\n{'='*80}")
        print(f"✅ ANÁLISE CONCLUÍDA")
        print(f"{'='*80}")
        print(f"\n📄 Próximos passos:")
        print(f"  1. Revisar o relatório acima")
        print(f"  2. Executar o script: correcao_banco.sql")
        print(f"  3. Fazer backup antes de aplicar mudanças")
        
    except Exception as e:
        print(f"\n❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == '__main__':
    main()
