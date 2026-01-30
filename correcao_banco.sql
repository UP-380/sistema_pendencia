-- Script de Correção do Banco de Dados
-- Sistema de Pendências UP380

-- Habilitar foreign keys
PRAGMA foreign_keys = ON;

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_pendencia_empresa ON pendencia(empresa);
CREATE INDEX IF NOT EXISTS idx_pendencia_status ON pendencia(status);
CREATE INDEX IF NOT EXISTS idx_pendencia_tipo ON pendencia(tipo_pendencia);
CREATE INDEX IF NOT EXISTS idx_pendencia_data_abertura ON pendencia(data_abertura);
CREATE INDEX IF NOT EXISTS idx_pendencia_token ON pendencia(token_acesso);

-- Adicionar campo tipo_credito_debito
ALTER TABLE pendencia ADD COLUMN tipo_credito_debito VARCHAR(10);

-- Verificar integridade
PRAGMA integrity_check;
