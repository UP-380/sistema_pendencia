# 🌐 Configuração do Domínio UP380

## 📋 Passos para configurar o domínio UP380.com.br

### 1. Configurar DNS no provedor de domínio

Acesse o painel do seu provedor de domínio (GoDaddy, Namecheap, etc.) e configure os registros DNS:

#### Registro A (Principal):
```
Tipo: A
Nome: @ (ou deixe em branco)
Valor: 82.25.64.173
TTL: 3600 (ou padrão)
```

#### Registro A (www):
```
Tipo: A
Nome: www
Valor: 82.25.64.173
TTL: 3600 (ou padrão)
```

### 2. Aguardar propagação do DNS

Após configurar o DNS, aguarde de 15 minutos a 24 horas para a propagação completa.

### 3. Verificar se o DNS está funcionando

Execute na VPS:
```bash
nslookup up380.com.br
nslookup www.up380.com.br
```

### 4. Configurar SSL na VPS

Execute na VPS:
```bash
cd /root/sistema_pendencia
chmod +x setup_ssl.sh
./setup_ssl.sh
```

### 5. Atualizar configurações do sistema

Execute na VPS:
```bash
# Atualizar código
git pull origin main

# Parar containers
docker-compose down

# Executar migração do banco
python3 migrate_natureza_operacao.py

# Iniciar containers com nova configuração
docker-compose up --build -d

# Verificar status
docker-compose ps
```

### 6. Testar o acesso

Após a configuração, teste os seguintes URLs:
- ✅ https://up380.com.br
- ✅ https://www.up380.com.br
- ✅ http://up380.com.br (deve redirecionar para HTTPS)

### 7. Configurar renovação automática do SSL

Adicione ao crontab da VPS:
```bash
crontab -e
```

Adicione esta linha:
```
0 12 * * * /usr/bin/certbot renew --quiet && docker-compose restart nginx
```

## 🔧 Troubleshooting

### Se o SSL não funcionar:
1. Verifique se o DNS está propagado: `nslookup up380.com.br`
2. Verifique se a porta 80 está aberta: `netstat -tlnp | grep :80`
3. Verifique logs do Nginx: `docker-compose logs nginx`

### Se o domínio não carregar:
1. Verifique se os containers estão rodando: `docker-compose ps`
2. Verifique logs da aplicação: `docker-compose logs web`
3. Teste conectividade: `curl -I http://localhost`

## 📞 Suporte

Se encontrar problemas, verifique:
- Logs do Docker: `docker-compose logs`
- Status dos containers: `docker-compose ps`
- Configuração do Nginx: `docker exec -it sistema_pendencia_nginx_1 nginx -t` 