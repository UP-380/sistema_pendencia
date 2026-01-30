-- ============================================
-- MIGRAÇÃO: Reestruturação do Banco de Dados
-- Sistema UP380 - Gestão de Pendências
-- Data: 2026-01-28
-- Autor: Sistema de Análise Automática
-- ============================================

-- IMPORTANTE: Fazer backup antes de executar!
-- cp pendencias.db pendencias_backup_20260128.db

-- Habilitar foreign keys
PRAGMA foreign_keys = ON;

-- ============================================
-- FASE 1: CORREÇÕES CRÍTICAS
-- ============================================

PRAGMA user_version;

-- 1.1. Adicionar campo tipo_credito_debito
-- Para tipo de pendência "Lançamento Não Encontrado em Sistema"
ALTER TABLE pendencia ADD COLUMN tipo_credito_debito VARCHAR(10);

-- 1.2. Criar índices de performance
-- Índices simples para filtros comuns
CREATE INDEX IF NOT EXISTS idx_pendencia_empresa ON pendencia(empresa);
CREATE INDEX IF NOT EXISTS idx_pendencia_status ON pendencia(status);
CREATE INDEX IF NOT EXISTS idx_pendencia_tipo ON pendencia(tipo_pendencia);
CREATE INDEX IF NOT EXISTS idx_pendencia_data_abertura ON pendencia(data_abertura);
CREATE INDEX IF NOT EXISTS idx_pendencia_token ON pendencia(token_acesso);
CREATE INDEX IF NOT EXISTS idx_pendencia_email ON pendencia(email_cliente);
CREATE INDEX IF NOT EXISTS idx_pendencia_tipo_credito_debito ON pendencia(tipo_credito_debito);

-- Índices compostos para queries complexas
CREATE INDEX IF NOT EXISTS idx_pendencia_empresa_status ON pendencia(empresa, status);
CREATE INDEX IF NOT EXISTS idx_pendencia_status_tipo ON pendencia(status, tipo_pendencia);
CREATE INDEX IF NOT EXISTS idx_pendencia_empresa_tipo ON pendencia(empresa, tipo_pendencia);

-- Índices em log_alteracao
CREATE INDEX IF NOT EXISTS idx_log_pendencia_id ON log_alteracao(pendencia_id);
CREATE INDEX IF NOT EXISTS idx_log_data_hora ON log_alteracao(data_hora);
CREATE INDEX IF NOT EXISTS idx_log_usuario ON log_alteracao(usuario);
CREATE INDEX IF NOT EXISTS idx_log_tipo_usuario ON log_alteracao(tipo_usuario);

-- Índices em usuario
CREATE INDEX IF NOT EXISTS idx_usuario_tipo ON usuario(tipo);
CREATE INDEX IF NOT EXISTS idx_usuario_ativo ON usuario(ativo);
CREATE INDEX IF NOT EXISTS idx_usuario_email ON usuario(email);

-- Índices em empresa
CREATE INDEX IF NOT EXISTS idx_empresa_segmento ON empresa(segmento_id);
CREATE INDEX IF NOT EXISTS idx_empresa_nome ON empresa(nome);

-- Índices em importacao
CREATE INDEX IF NOT EXISTS idx_importacao_usuario ON importacao(usuario);
CREATE INDEX IF NOT EXISTS idx_importacao_data_hora ON importacao(data_hora);
CREATE INDEX IF NOT EXISTS idx_importacao_status ON importacao(status);

-- 1.3. Garantir unicidade de token
-- Índice único parcial (apenas para tokens não nulos)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_token_acesso 
ON pendencia(token_acesso) 
WHERE token_acesso IS NOT NULL;

-- ============================================
-- FASE 2: LIMPEZA DE DADOS
-- ============================================

-- 2.1. Remover espaços extras e normalizar
UPDATE pendencia SET empresa = TRIM(empresa) 
WHERE empresa != TRIM(empresa);

UPDATE pendencia SET fornecedor_cliente = TRIM(fornecedor_cliente) 
WHERE fornecedor_cliente != TRIM(fornecedor_cliente);

UPDATE pendencia SET email_cliente = TRIM(email_cliente) 
WHERE email_cliente IS NOT NULL AND email_cliente != TRIM(email_cliente);

UPDATE pendencia SET tipo_pendencia = TRIM(tipo_pendencia)
WHERE tipo_pendencia != TRIM(tipo_pendencia);

-- 2.2. Padronizar status (UPPERCASE)
UPDATE pendencia SET status = UPPER(TRIM(status)) 
WHERE status != UPPER(TRIM(status));

-- 2.3. Normalizar emails (lowercase)
UPDATE pendencia SET email_cliente = LOWER(TRIM(email_cliente))
WHERE email_cliente IS NOT NULL AND email_cliente != LOWER(TRIM(email_cliente));

UPDATE usuario SET email = LOWER(TRIM(email))
WHERE email != LOWER(TRIM(email));

-- ============================================
-- FASE 3: VERIFICAÇÕES E RELATÓRIOS
-- ============================================

-- 3.1. Verificar integridade do banco
PRAGMA integrity_check;

-- 3.2. Estatísticas gerais
SELECT '=== ESTATÍSTICAS DO BANCO ===' as info;

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
SELECT 'importacao' as tabela, COUNT(*) as total FROM importacao
UNION ALL
SELECT 'usuario_empresas' as tabela, COUNT(*) as total FROM usuario_empresas
UNION ALL
SELECT 'permissao_usuario_tipo' as tabela, COUNT(*) as total FROM permissao_usuario_tipo;

-- 3.3. Verificar índices criados
SELECT '=== ÍNDICES DA TABELA PENDENCIA ===' as info;

SELECT name as indice, sql as definicao
FROM sqlite_master 
WHERE type = 'index' 
AND tbl_name = 'pendencia'
AND name LIKE 'idx_%'
ORDER BY name;

-- 3.4. Verificar dados inconsistentes
SELECT '=== VERIFICAÇÃO DE INCONSISTÊNCIAS ===' as info;

-- Pendências com valor inválido
SELECT 'Pendências com valor <= 0' as problema, COUNT(*) as total
FROM pendencia WHERE valor <= 0;

-- Pendências sem email (status PENDENTE CLIENTE)
SELECT 'Pendências PENDENTE CLIENTE sem email' as problema, COUNT(*) as total
FROM pendencia 
WHERE status = 'PENDENTE CLIENTE' 
AND (email_cliente IS NULL OR email_cliente = '');

-- Tokens duplicados
SELECT 'Tokens duplicados' as problema, COUNT(*) as total
FROM (
    SELECT token_acesso, COUNT(*) as cnt
    FROM pendencia
    WHERE token_acesso IS NOT NULL
    GROUP BY token_acesso
    HAVING COUNT(*) > 1
);

-- Empresas não cadastradas
SELECT 'Empresas em pendências mas não cadastradas' as problema, COUNT(DISTINCT p.empresa) as total
FROM pendencia p
LEFT JOIN empresa e ON p.empresa = e.nome
WHERE e.id IS NULL;

-- Status inválidos
SELECT 'Pendências com status inválido' as problema, COUNT(*) as total
FROM pendencia
WHERE status NOT IN (
    'PENDENTE CLIENTE',
    'PENDENTE OPERADOR UP',
    'PENDENTE SUPERVISOR UP',
    'RESOLVIDA'
);

-- 3.5. Atualizar versão do schema
PRAGMA user_version = 2;

-- ============================================
-- FIM DA MIGRAÇÃO
-- ============================================

SELECT '=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===' as info;
SELECT 'Versão do schema: ' || user_version as info FROM pragma_user_version;
SELECT 'Data: ' || datetime('now', 'localtime') as info;
