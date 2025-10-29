# ⚡ COMANDOS RÁPIDOS PARA DEPLOY
## Copy & Paste - Sistema UP380

---

## 📍 PARTE 1: NO SEU WINDOWS

### 1️⃣ Ir para pasta e verificar

```powershell
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
git status
```

### 2️⃣ Adicionar tudo e commitar

```powershell
git add .
git commit -m "feat: Implementação de segmentos, correção de planilhas e melhorias no dashboard - Sistema UP380 v2.0

- Sistema de segmentos para organização de empresas
- Planilhas modelo corrigidas (9 arquivos com banco e fornecedor)
- Dashboard com gráficos funcionais (Chart.js local)
- Validações na exclusão de empresas
- Campo data_abertura em pendências
- Script de migração completo (migracao_producao_completa.py)

IMPORTANTE: Executar migracao_producao_completa.py na VPS"
```

### 3️⃣ Enviar para GitHub

```powershell
git push origin main
```

**✅ PRONTO NO WINDOWS!**

---

## 🌐 PARTE 2: NA VPS (via SSH)

### 1️⃣ Conectar na VPS

```bash
ssh SEU_USUARIO@SEU_IP_VPS
# Exemplo: ssh root@123.456.789.012
```

### 2️⃣ Ir para pasta do sistema

```bash
cd ~/sistema_pendencia
pwd
ls -la
```

### 3️⃣ BACKUP (CRÍTICO!)

```bash
# Criar pasta de backups
mkdir -p backups

# Backup do banco
cp instance/pendencias.db backups/pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Backup do sistema completo
tar -czf backups/sistema_backup_$(date +%Y%m%d_%H%M%S).tar.gz --exclude='backups' --exclude='.git' --exclude='__pycache__' .

# Verificar
ls -lh backups/

echo "✅ Backups criados!"
```

### 4️⃣ Parar container

```bash
# Ver containers rodando
docker ps

# Parar (método 1 - docker-compose)
docker-compose down

# OU parar (método 2 - docker direto)
# docker stop NOME_DO_CONTAINER

echo "⏸️  Container parado"
```

### 5️⃣ Atualizar código do GitHub

```bash
# Pull
git pull origin main

# Ver mudanças
git log --oneline -5

# Verificar arquivos novos
ls -la modelo_*.xlsx
ls -la migracao_producao_completa.py

echo "✅ Código atualizado!"
```

### 6️⃣ Rodar migrações do banco

```bash
# Migração 1: Estrutura (segmentos, campos)
python3 migracao_producao_completa.py

# Aguarde: ✅ TODAS AS MIGRAÇÕES CONCLUÍDAS COM SUCESSO!

# Migração 2: Consolidar tipos de documentos
python3 migracao_consolidar_documentos.py

# Aguarde: ✅ Migração concluída!
```

### 7️⃣ Rebuild e iniciar

```bash
# Rebuild (método 1 - docker-compose)
docker-compose build
docker-compose up -d

# OU rebuild (método 2 - docker direto)
# docker build -t sistema_up380 .
# docker start NOME_DO_CONTAINER

echo "🚀 Container iniciado!"
```

### 8️⃣ Verificar

```bash
# Ver containers
docker ps

# Ver logs (pressione Ctrl+C para sair)
docker logs NOME_DO_CONTAINER --tail 50 -f
```

### 9️⃣ Testar

```bash
# Testar endpoint
curl http://localhost:5000

# Verificar banco
sqlite3 instance/pendencias.db "SELECT COUNT(*) FROM segmento;"
sqlite3 instance/pendencias.db "SELECT COUNT(*) FROM empresa WHERE segmento_id IS NOT NULL;"

echo "✅ Deploy concluído!"
```

**✅ PRONTO NA VPS!**

---

## 🧪 PARTE 3: VALIDAÇÃO NO NAVEGADOR

Acesse: `http://SEU_DOMINIO`

### Checklist:
```
[ ] Sistema abre?
[ ] Login funciona?
[ ] Dashboard carrega?
[ ] Gráficos aparecem?
[ ] Menu "Segmentos" aparece?
[ ] Consegue acessar /segmentos?
[ ] Pendências antigas estão lá?
[ ] Importar planilha funciona?
[ ] Campos banco e fornecedor aparecem?
```

---

## 🆘 SE DER ERRO - ROLLBACK RÁPIDO

```bash
# Na VPS:

# 1. Parar container
docker-compose down

# 2. Restaurar backup (ajuste o timestamp)
cp backups/pendencias_backup_20251028_120000.db instance/pendencias.db

# 3. Voltar código
git reset --hard HEAD~1

# 4. Rebuild e iniciar
docker-compose build
docker-compose up -d

# 5. Verificar
docker ps
docker logs NOME_DO_CONTAINER
```

---

## 📋 RESUMO ULTRA-RÁPIDO

### Windows:
```powershell
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
git add .
git commit -m "feat: Sistema UP380 v2.0 - Segmentos e melhorias"
git push origin main
```

### VPS:
```bash
cd ~/sistema_pendencia
mkdir -p backups
cp instance/pendencias.db backups/backup_$(date +%Y%m%d_%H%M%S).db
docker-compose down
git pull origin main
python3 migracao_producao_completa.py
python3 migracao_consolidar_documentos.py
docker-compose build
docker-compose up -d
docker ps
```

---

## ⏱️ TEMPO ESTIMADO

- ✅ Windows (local): **2 minutos**
- ✅ VPS (backup): **2 minutos**
- ✅ VPS (deploy): **5-10 minutos**
- ✅ Validação: **3 minutos**

**Total: ~15-20 minutos**

---

## 🎯 VARIÁVEIS PARA AJUSTAR

Substitua antes de executar:

- `SEU_USUARIO` → Seu usuário SSH (ex: root)
- `SEU_IP_VPS` → IP da sua VPS (ex: 123.456.789.012)
- `NOME_DO_CONTAINER` → Nome do seu container Docker
- `SEU_DOMINIO` → URL de produção (ex: sistema.seudominio.com)

---

**PRONTO! COMANDOS PRONTOS PARA USAR!** 🚀

Copie, cole e execute! ⚡

