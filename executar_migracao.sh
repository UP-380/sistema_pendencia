#!/bin/bash

# Script para executar migração do banco de dados na VPS
echo "🔄 Executando migração do banco de dados..."

# Verificar se o container está rodando
if ! docker-compose ps | grep -q "web.*Up"; then
    echo "❌ Container web não está rodando. Iniciando..."
    docker-compose up -d
    sleep 10
fi

# Executar migração
echo "📝 Executando migração data_abertura..."
docker-compose exec -T web python migrate_producao.py

# Verificar se a migração foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "✅ Migração concluída com sucesso!"
    echo "🔄 Reiniciando aplicação..."
    docker-compose restart web
    echo "🎉 Sistema atualizado e funcionando!"
else
    echo "❌ Erro na migração. Verifique os logs:"
    docker-compose logs web
fi
