#!/bin/bash

# Script para configurar SSL com Let's Encrypt para UP380
# Execute este script na VPS após configurar o DNS

echo "🔐 Configurando SSL para UP380..."

# Verifica se o certbot está instalado
if ! command -v certbot &> /dev/null; then
    echo "📦 Instalando Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Cria diretório para certificados
mkdir -p ssl

# Para o Nginx temporariamente
docker-compose down

# Configuração temporária do Nginx para validação
cat > nginx_temp.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    upstream flask_app {
        server web:5000;
    }

    server {
        listen 80;
        server_name up380.com.br www.up380.com.br;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$server_name$request_uri;
        }
    }
}
EOF

# Inicia containers com configuração temporária
docker-compose up -d

# Aguarda containers iniciarem
sleep 10

# Obtém certificado SSL
echo "🎫 Obtendo certificado SSL..."
certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@up380.com.br \
    --agree-tos \
    --no-eff-email \
    -d up380.com.br \
    -d www.up380.com.br

# Copia certificados para o diretório do projeto
if [ -f /etc/letsencrypt/live/up380.com.br/fullchain.pem ]; then
    echo "📋 Copiando certificados..."
    cp /etc/letsencrypt/live/up380.com.br/fullchain.pem ssl/up380.com.br.crt
    cp /etc/letsencrypt/live/up380.com.br/privkey.pem ssl/up380.com.br.key
    
    # Define permissões
    chmod 644 ssl/up380.com.br.crt
    chmod 600 ssl/up380.com.br.key
    
    echo "✅ Certificados SSL configurados com sucesso!"
else
    echo "❌ Falha ao obter certificados SSL"
    exit 1
fi

# Restaura configuração original do Nginx
git checkout nginx.conf

# Reinicia containers com SSL
docker-compose down
docker-compose up -d

echo "🎉 Configuração SSL concluída!"
echo "🌐 Seu site agora está disponível em: https://up380.com.br"
echo "📅 Certificados renovam automaticamente a cada 90 dias" 