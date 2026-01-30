# 🚀 Deploy na VPS Hostinger

Este guia te ajudará a fazer o deploy do Sistema de Pendências na sua VPS da Hostinger.

## 📋 Pré-requisitos

- VPS Linux (Ubuntu/Debian recomendado)
- Acesso SSH à VPS
- Domínio (opcional, mas recomendado)

## 🔧 Passos para Deploy

### 1. Conectar na VPS via SSH
```bash
ssh usuario@seu_ip_vps
```

### 2. Clonar o repositório
```bash
git clone https://github.com/UP-380/sistema_pendencia.git
cd sistema_pendencia
```

### 3. Executar o script de deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

### 4. Configurar variáveis de ambiente
Edite o arquivo `.env` criado:
```bash
nano .env
```

**Configure especialmente:**
- `MAIL_USERNAME`: Seu email Gmail
- `MAIL_PASSWORD`: Senha de app do Gmail (não sua senha normal)
- `SECRET_KEY`: Deixe como está (gerada automaticamente)

### 5. Reiniciar a aplicação
```bash
docker-compose down
docker-compose up -d
```

## 📧 Configuração do Email

Para usar as funcionalidades de email, você precisa:

1. **Ativar autenticação de 2 fatores no Gmail**
2. **Gerar uma senha de app:**
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Mail" e "Outro (nome personalizado)"
   - Use essa senha no campo `MAIL_PASSWORD`

## 🌐 Configuração de Domínio (Opcional)

### Com Nginx (já configurado no docker-compose):
A aplicação estará disponível na porta 80.

### Com SSL/HTTPS:
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com
```

## 🔍 Comandos Úteis

### Ver logs da aplicação:
```bash
docker-compose logs -f web
```

### Parar a aplicação:
```bash
docker-compose down
```

### Reiniciar a aplicação:
```bash
docker-compose restart
```

### Atualizar o código:
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## 🔒 Segurança

- ✅ A aplicação roda em container isolado
- ✅ Nginx com rate limiting configurado
- ✅ Headers de segurança ativos
- ✅ Banco SQLite com permissões restritas

## 📊 Monitoramento

### Verificar status dos containers:
```bash
docker-compose ps
```

### Verificar uso de recursos:
```bash
docker stats
```

## 🆘 Troubleshooting

### Se a aplicação não subir:
```bash
# Ver logs detalhados
docker-compose logs web

# Verificar se as portas estão livres
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000
```

### Se o email não funcionar:
- Verifique se a senha de app está correta
- Teste com um email simples primeiro
- Verifique os logs: `docker-compose logs web`

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs: `docker-compose logs web`
2. Confirme se todas as variáveis de ambiente estão configuradas
3. Teste a conectividade: `curl http://localhost:5000/health` 