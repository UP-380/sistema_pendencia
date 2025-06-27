#!/bin/bash

# Script de Deploy para VPS Hostinger
echo "🚀 Iniciando deploy do Sistema de Pendências..."

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar Docker e Docker Compose
echo "🐳 Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "📦 Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << EOF
# Configurações do Flask
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
FLASK_APP=app.py

# Configurações de Email (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app_do_gmail
MAIL_DEFAULT_SENDER=seu_email@gmail.com

# Configurações do Banco de Dados
SQLALCHEMY_DATABASE_URI=sqlite:///pendencias.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
EOF
    echo "⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações de email!"
fi

# Construir e iniciar containers
echo "🔨 Construindo containers..."
docker-compose build

echo "🚀 Iniciando aplicação..."
docker-compose up -d

echo "✅ Deploy concluído!"
echo "🌐 Acesse: http://SEU_IP_VPS"
echo "📧 Configure o email no arquivo .env antes de usar as funcionalidades de email" 