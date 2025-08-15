# 🚀 DEPLOY EM PRODUÇÃO - Sistema de Pendências UP380

## 📋 PRÉ-REQUISITOS

- ✅ VPS Linux (Ubuntu/Debian recomendado)
- ✅ Acesso SSH à VPS
- ✅ Domínio (opcional, mas recomendado)
- ✅ Email Gmail configurado com autenticação de 2 fatores

## 🔧 PASSO A PASSO DO DEPLOY

### **PASSO 1: Preparar o Código Local**

1. **Commit das alterações:**
```bash
git add .
git commit -m "Deploy em produção - Sistema UP380 atualizado"
git push origin main
```

2. **Verificar se tudo funciona localmente:**
```bash
python -c "import app; print('✅ Aplicação OK!')"
```

### **PASSO 2: Conectar na VPS**

```bash
ssh usuario@seu_ip_vps
```

### **PASSO 3: Clonar o Repositório**

```bash
# Se já existe, fazer pull
cd /caminho/do/projeto
git pull origin main

# Se é a primeira vez
git clone https://github.com/SEU_USUARIO/PLANILHA-DE-PENDENCIAS.git
cd PLANILHA-DE-PENDENCIAS
```

### **PASSO 4: Executar o Deploy**

```bash
# Dar permissão de execução
chmod +x deploy_producao.sh

# Executar o deploy
./deploy_producao.sh
```

### **PASSO 5: Configurar Email (OBRIGATÓRIO)**

1. **Editar o arquivo .env:**
```bash
nano .env
```

2. **Configurar as variáveis de email:**
```env
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app_do_gmail
MAIL_DEFAULT_SENDER=seu_email@gmail.com
```

3. **Como gerar senha de app do Gmail:**
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Mail" e "Outro (nome personalizado)"
   - Use essa senha no campo `MAIL_PASSWORD`

### **PASSO 6: Reiniciar a Aplicação**

```bash
docker-compose down
docker-compose up -d
```

## 🌐 CONFIGURAÇÃO DE DOMÍNIO (OPCIONAL)

### **Com SSL/HTTPS:**

1. **Instalar Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Obter certificado SSL:**
```bash
sudo certbot --nginx -d seu-dominio.com
```

3. **Renovação automática:**
```bash
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔍 VERIFICAÇÃO DO DEPLOY

### **Verificar se está funcionando:**

```bash
# Status dos containers
docker-compose ps

# Logs da aplicação
docker-compose logs -f web

# Testar conectividade
curl http://localhost:5000
```

### **Verificar funcionalidades:**

1. **Acesse:** `http://seu_ip_vps` ou `https://seu-dominio.com`
2. **Teste login** com um usuário existente
3. **Teste criação** de uma nova pendência
4. **Teste relatórios** mensais
5. **Teste exportação** CSV

## 🔧 COMANDOS ÚTEIS

### **Gerenciamento da Aplicação:**

```bash
# Ver logs em tempo real
docker-compose logs -f web

# Parar a aplicação
docker-compose down

# Reiniciar a aplicação
docker-compose restart

# Ver status dos containers
docker-compose ps

# Ver uso de recursos
docker stats
```

### **Atualizações:**

```bash
# Atualizar código
git pull origin main

# Reconstruir e reiniciar
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Backup do Banco:**

```bash
# Fazer backup
cp instance/pendencias.db instance/pendencias.db.backup.$(date +%Y%m%d_%H%M%S)

# Restaurar backup
cp instance/pendencias.db.backup.20241215_143022 instance/pendencias.db
```

## 🔒 SEGURANÇA

### **Configurações de Segurança:**

- ✅ Aplicação roda em container isolado
- ✅ Nginx com rate limiting
- ✅ Headers de segurança ativos
- ✅ Banco SQLite com permissões restritas
- ✅ Variáveis de ambiente protegidas

### **Firewall (Recomendado):**

```bash
# Instalar UFW
sudo apt install ufw

# Configurar regras
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 📊 MONITORAMENTO

### **Logs Importantes:**

```bash
# Logs da aplicação
docker-compose logs web

# Logs do Nginx
docker-compose logs nginx

# Logs do sistema
sudo journalctl -u docker
```

### **Métricas de Recursos:**

```bash
# Uso de CPU e memória
docker stats

# Espaço em disco
df -h

# Uso de memória
free -h
```

## 🆘 TROUBLESHOOTING

### **Problemas Comuns:**

1. **Aplicação não sobe:**
```bash
docker-compose logs web
# Verificar se há erros de sintaxe ou dependências
```

2. **Email não funciona:**
```bash
# Verificar configurações no .env
# Testar com email simples
# Verificar logs: docker-compose logs web
```

3. **Banco de dados corrompido:**
```bash
# Restaurar backup
cp instance/pendencias.db.backup.* instance/pendencias.db
docker-compose restart
```

4. **Porta 80 ocupada:**
```bash
sudo netstat -tlnp | grep :80
sudo lsof -i :80
# Parar serviço conflitante se necessário
```

### **Contatos de Suporte:**

- 📧 Email: suporte@up380.com
- 📱 WhatsApp: (11) 99999-9999
- 🌐 Sistema: http://seu-dominio.com/suporte

## ✅ CHECKLIST FINAL

- [ ] Código commitado e enviado para o repositório
- [ ] VPS acessível via SSH
- [ ] Docker e Docker Compose instalados
- [ ] Aplicação rodando (docker-compose ps)
- [ ] Email configurado e testado
- [ ] SSL configurado (se usando domínio)
- [ ] Backup do banco realizado
- [ ] Logs verificados (sem erros)
- [ ] Funcionalidades testadas
- [ ] Firewall configurado
- [ ] Monitoramento ativo

## 🎉 DEPLOY CONCLUÍDO!

Sua aplicação está rodando em produção! 

**URL de Acesso:** `http://seu_ip_vps` ou `https://seu-dominio.com`

**Próximos passos:**
1. Teste todas as funcionalidades
2. Configure monitoramento
3. Faça backup regular do banco
4. Mantenha o sistema atualizado
