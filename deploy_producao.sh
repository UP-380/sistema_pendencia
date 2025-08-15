#!/bin/bash

# 🚀 Script de Deploy para Produção - Sistema de Pendências UP380
echo "🚀 Iniciando deploy em PRODUÇÃO do Sistema de Pendências UP380..."

# Verificar se estamos no diretório correto
if [ ! -f "app.py" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do projeto!"
    exit 1
fi

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar Docker se não estiver instalado
echo "🐳 Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "📦 Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker instalado! Faça logout e login novamente para aplicar as permissões."
    exit 1
fi

# Instalar Docker Compose se não estiver instalado
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p logs
mkdir -p ssl
mkdir -p static/notas_fiscais

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

# Configurações de Produção
DEBUG=False
TESTING=False
EOF
    echo "⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações de email!"
    echo "📧 Configure especialmente:"
    echo "   - MAIL_USERNAME: Seu email Gmail"
    echo "   - MAIL_PASSWORD: Senha de app do Gmail"
    echo ""
    echo "🔐 Para gerar senha de app do Gmail:"
    echo "   1. Ative autenticação de 2 fatores no Gmail"
    echo "   2. Acesse: https://myaccount.google.com/apppasswords"
    echo "   3. Selecione 'Mail' e 'Outro (nome personalizado)'"
    echo ""
    read -p "Pressione ENTER após configurar o .env..."
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

# Fazer backup do banco de dados se existir
if [ -f "instance/pendencias.db" ]; then
    echo "💾 Fazendo backup do banco de dados..."
    cp instance/pendencias.db instance/pendencias.db.backup.$(date +%Y%m%d_%H%M%S)
fi

# Construir e iniciar containers
echo "🔨 Construindo containers..."
docker-compose build --no-cache

echo "🚀 Iniciando aplicação..."
docker-compose up -d

# Aguardar a aplicação subir
echo "⏳ Aguardando aplicação inicializar..."
sleep 10

# Verificar status
echo "🔍 Verificando status dos containers..."
docker-compose ps

# Verificar logs
echo "📋 Últimos logs da aplicação:"
docker-compose logs --tail=20 web

echo ""
echo "✅ Deploy concluído com sucesso!"
echo ""
echo "🌐 Acesse sua aplicação:"
echo "   - HTTP:  http://$(curl -s ifconfig.me)"
echo "   - HTTPS: https://$(curl -s ifconfig.me) (se configurado SSL)"
echo ""
echo "📧 Configure o email no arquivo .env antes de usar as funcionalidades de email"
echo ""
echo "🔧 Comandos úteis:"
echo "   - Ver logs: docker-compose logs -f web"
echo "   - Parar: docker-compose down"
echo "   - Reiniciar: docker-compose restart"
echo "   - Atualizar: git pull && docker-compose build && docker-compose up -d"
