# 📋 CHECKLIST - DEPLOY PARA PRODUÇÃO
## Sistema UP380 - Hostinger VPS + Docker

---

## 🔍 INFORMAÇÕES NECESSÁRIAS

Por favor, me forneça as seguintes informações para eu te ajudar com o deploy seguro:

---

### 1. **INFORMAÇÕES DO GIT/GITHUB**

```bash
# Execute estes comandos e me envie o resultado:

# Verificar status atual
git status

# Verificar remote atual
git remote -v

# Verificar branch atual
git branch

# Verificar últimos commits
git log --oneline -5
```

**Perguntas:**
- [ ] Já tem repositório no GitHub? Se sim, qual a URL?
- [ ] Qual branch está usando? (main/master/develop)
- [ ] Último commit foi quando?

---

### 2. **INFORMAÇÕES DO DOCKER**

```bash
# Execute na VPS e me envie:

# Listar containers rodando
docker ps

# Ver conteúdo do docker-compose.yml
cat ~/sistema_pendencia/docker-compose.yml

# Ver conteúdo do Dockerfile
cat ~/sistema_pendencia/Dockerfile
```

**Perguntas:**
- [ ] Nome do container em produção?
- [ ] Porta exposta?
- [ ] Como o Docker foi configurado?

---

### 3. **INFORMAÇÕES DO BANCO DE DADOS**

```bash
# Execute e me envie:

# Localizar arquivo do banco
find ~/sistema_pendencia -name "*.db"

# Tamanho do banco atual
ls -lh ~/sistema_pendencia/instance/pendencias.db

# Verificar se há backup
ls -lh ~/sistema_pendencia/backups/
```

**Perguntas:**
- [ ] Banco de dados: SQLite? Onde está o arquivo?
- [ ] Quantos registros/pendências tem em produção (aprox.)?
- [ ] Já tem rotina de backup automático?

---

### 4. **ARQUIVOS IMPORTANTES**

```bash
# Me envie o conteúdo destes arquivos:

# Requirements atual
cat ~/sistema_pendencia/requirements.txt

# Variáveis de ambiente (se existir)
cat ~/sistema_pendencia/.env

# Configuração do Nginx (se existir)
cat ~/sistema_pendencia/nginx.conf

# Script de start
cat ~/sistema_pendencia/start.sh
```

**Perguntas:**
- [ ] Usa variáveis de ambiente (.env)?
- [ ] Usa Nginx como proxy reverso?
- [ ] Tem SSL/HTTPS configurado?
- [ ] Qual domínio está usando?

---

### 5. **ACESSO À VPS**

**Perguntas:**
- [ ] Tem acesso SSH à VPS?
- [ ] IP ou hostname da VPS?
- [ ] Usuário SSH (root? outro?)
- [ ] Sistema operacional (Ubuntu? CentOS? Debian?)

---

### 6. **ARQUIVOS LOCAIS (Seu Computador)**

```bash
# Execute NO SEU COMPUTADOR e me envie:

# Ver git status local
git status

# Ver arquivos modificados não commitados
git diff --name-only

# Ver arquivos não rastreados
git ls-files --others --exclude-standard
```

**Perguntas:**
- [ ] Tem backup local do sistema?
- [ ] Tem as planilhas modelo criadas?
- [ ] Tem todas as mudanças salvas?

---

### 7. **MIGRAÇÕES E DADOS**

**Perguntas:**
- [ ] Precisa rodar alguma migração de banco? (adicionar colunas, tabelas, etc)
- [ ] Tem scripts de migração já criados? Quais?
- [ ] Os dados em produção usam estrutura antiga ou nova?

**Scripts de migração que vi no projeto:**
```
- migrate_add_segmento.py
- migrate_cliente_supervisor.py
- migrate_add_data_abertura.py
- migrate_adicionar_segmentos.py
- migrar_nota_fiscal_automatico.py
- (outros...)
```

---

### 8. **PROCESSO ATUAL DE DEPLOY**

**Perguntas:**
- [ ] Como você faz deploy atualmente? (manual? script?)
- [ ] Já teve algum problema em deploy anterior?
- [ ] Tempo de downtime aceitável? (5min? 10min? 0?)

---

## 📸 PRINTS/LOGS ÚTEIS

Por favor, me envie prints ou logs de:

1. **Dashboard do sistema em produção** (para ver se está funcionando)
2. **Saída de `docker ps`** (containers rodando)
3. **Estrutura de pastas** (`tree -L 2 ~/sistema_pendencia` ou `ls -la ~/sistema_pendencia`)
4. **Logs recentes** (`docker logs <container_name> --tail 50`)

---

## 🎯 PLANO DE AÇÃO (Após receber as informações)

Com essas informações, vou te ajudar a:

### ✅ FASE 1: Preparação Local
1. Commitar todas as mudanças
2. Criar tag de versão
3. Push para GitHub
4. Validar que tudo está no repositório

### ✅ FASE 2: Backup Produção
1. Fazer backup completo do banco
2. Fazer backup dos arquivos
3. Backup do container Docker
4. Validar backups

### ✅ FASE 3: Migrações
1. Identificar migrações necessárias
2. Testar migrações localmente
3. Preparar rollback se necessário

### ✅ FASE 4: Deploy
1. Parar container temporariamente
2. Pull do código novo
3. Rodar migrações
4. Rebuild do container
5. Restart
6. Validação

### ✅ FASE 5: Validação
1. Testar funcionalidades críticas
2. Verificar dados
3. Testar planilhas novas
4. Confirmar que tudo funciona

---

## 📝 RESPONDA ESTE CHECKLIST

**Copie este template e preencha:**

```
=== INFORMAÇÕES DO SISTEMA ===

1. GitHub:
   - URL do repo: 
   - Branch atual: 
   - Último commit: 

2. Docker:
   - Nome do container: 
   - Porta: 
   - Resultado de `docker ps`: 

3. Banco de Dados:
   - Localização: 
   - Tamanho: 
   - Qtd de pendências (aprox): 

4. VPS:
   - IP/Hostname: 
   - Usuário SSH: 
   - Sistema operacional: 

5. Domínio:
   - URL de produção: 
   - Tem SSL? 

6. Migrações:
   - Precisa migrar estrutura de segmentos? 
   - Precisa adicionar campo banco na tabela? 
   - Outras migrações necessárias: 

7. Arquivos:
   - Tem .env? 
   - Usa Nginx? 
   - Tem start.sh? 
```

---

## 🚨 IMPORTANTE

**ANTES DE QUALQUER DEPLOY:**
- ✅ Fazer backup completo
- ✅ Testar localmente
- ✅ Ter plano de rollback
- ✅ Avisar usuários (se necessário)

---

**Assim que você me passar essas informações, vou criar um guia passo a passo COMPLETO e SEGURO para o deploy!** 🚀

