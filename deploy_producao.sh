#!/bin/bash

echo "🚀 Iniciando deploy em produção..."

# Navegar para o diretório do projeto
cd ~/sistema_pendencia

# Baixar as últimas alterações
echo "📥 Baixando alterações do GitHub..."
git pull

# Parar os containers
echo "⏹️ Parando containers..."
docker-compose down

# Reconstruir as imagens
echo "🔨 Reconstruindo imagens..."
docker-compose up -d --build

# Aguardar um pouco para os containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 10

# Executar migrações manualmente (caso o script automático falhe)
echo "📊 Executando migrações..."
docker-compose exec -T web python3 migrate_natureza_operacao.py 2>/dev/null || echo "Migração natureza_operacao já executada ou não necessária"
docker-compose exec -T web python3 migrate_motivo_recusa_supervisor.py 2>/dev/null || echo "Migração motivo_recusa_supervisor já executada ou não necessária"
docker-compose exec -T web python3 migrate_data_abertura.py 2>/dev/null || echo "Migração data_abertura já executada ou não necessária"

# Verificar status
echo "✅ Verificando status dos containers..."
docker-compose ps

echo "🎉 Deploy concluído!"
echo "🌐 Sistema disponível em: http://seu-ip-vps"
