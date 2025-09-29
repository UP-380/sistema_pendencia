#!/bin/bash

# Criar diretório de backup se não existir
mkdir -p /root/backups

# Data atual para nome do arquivo
DATA=$(date +"%Y%m%d_%H%M%S")

# Caminho do banco de dados (ajuste se necessário)
DB_PATH="/root/PLANILHA\ DE\ PENDENCIAS/instance/pendencias.db"
BACKUP_PATH="/root/backups/pendencias_backup_${DATA}.db"

# Parar o container Docker se estiver rodando
echo "🛑 Parando container da aplicação..."
docker-compose down

# Fazer o backup
echo "📦 Criando backup do banco de dados..."
cp "${DB_PATH}" "${BACKUP_PATH}"

# Reiniciar o container
echo "🚀 Reiniciando a aplicação..."
docker-compose up -d

# Verificar se o backup foi criado
if [ -f "${BACKUP_PATH}" ]; then
    echo "✅ Backup criado com sucesso em: ${BACKUP_PATH}"
    ls -lh "${BACKUP_PATH}"
else
    echo "❌ Erro ao criar backup!"
fi