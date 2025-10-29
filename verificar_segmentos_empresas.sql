-- ============================================
-- SQL para Verificar Segmentos e Empresas
-- ============================================

-- 1. Ver todas as empresas e seus segmentos
SELECT 
    e.id,
    e.nome as empresa,
    COALESCE(s.nome, 'Sem Segmento') as segmento,
    e.segmento_id
FROM empresa e
LEFT JOIN segmento s ON e.segmento_id = s.id
ORDER BY s.nome, e.nome;

-- 2. Contar empresas por segmento
SELECT 
    COALESCE(s.nome, 'Sem Segmento') as segmento,
    COUNT(e.id) as total_empresas
FROM empresa e
LEFT JOIN segmento s ON e.segmento_id = s.id
GROUP BY s.id, s.nome
ORDER BY total_empresas DESC;

-- 3. Ver empresas SEM segmento (precisam ser categorizadas)
SELECT 
    id,
    nome
FROM empresa
WHERE segmento_id IS NULL
ORDER BY nome;

-- 4. Ver empresas COM segmento
SELECT 
    e.id,
    e.nome as empresa,
    s.nome as segmento
FROM empresa e
INNER JOIN segmento s ON e.segmento_id = s.id
ORDER BY s.nome, e.nome;

-- 5. Estatísticas gerais
SELECT 
    COUNT(*) as total_empresas,
    COUNT(segmento_id) as empresas_com_segmento,
    COUNT(*) - COUNT(segmento_id) as empresas_sem_segmento
FROM empresa;

-- 6. Ver segmentos e quantas empresas cada um tem
SELECT 
    s.id,
    s.nome as segmento,
    COUNT(e.id) as total_empresas
FROM segmento s
LEFT JOIN empresa e ON e.segmento_id = s.id
GROUP BY s.id, s.nome
ORDER BY s.nome;

-- 7. Empresas por segmento (detalhado)
-- FUNERÁRIA
SELECT 'FUNERÁRIA' as segmento, nome as empresa
FROM empresa
WHERE segmento_id = (SELECT id FROM segmento WHERE nome = 'FUNERÁRIA')
ORDER BY nome;

-- PROTEÇÃO VEICULAR
SELECT 'PROTEÇÃO VEICULAR' as segmento, nome as empresa
FROM empresa
WHERE segmento_id = (SELECT id FROM segmento WHERE nome = 'PROTEÇÃO VEICULAR')
ORDER BY nome;

-- FARMÁCIA
SELECT 'FARMÁCIA' as segmento, nome as empresa
FROM empresa
WHERE segmento_id = (SELECT id FROM segmento WHERE nome = 'FARMÁCIA')
ORDER BY nome;

-- ============================================
-- QUERIES ÚTEIS PARA PRODUÇÃO
-- ============================================

-- Vincular empresa a segmento manualmente (se necessário)
-- UPDATE empresa SET segmento_id = 1 WHERE nome = 'NOME_DA_EMPRESA';

-- Remover vínculo de segmento
-- UPDATE empresa SET segmento_id = NULL WHERE nome = 'NOME_DA_EMPRESA';

-- Ver empresas que precisam ser categorizadas (em produção)
SELECT 
    id,
    nome,
    'Precisa categorizar' as status
FROM empresa
WHERE segmento_id IS NULL
ORDER BY nome;


