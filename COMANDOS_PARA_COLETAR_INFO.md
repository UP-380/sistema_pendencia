# 🔧 COMANDOS PARA COLETAR INFORMAÇÕES
## Execute e me envie os resultados

---

## 📍 NO SEU COMPUTADOR (Windows)

### 1. Informações do Git Local

```powershell
# Ir para pasta do projeto
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"

# Status do git
git status

# Ver remote
git remote -v

# Ver branch
git branch

# Ver últimos commits
git log --oneline -10

# Ver arquivos modificados
git diff --name-status

# Ver arquivos não rastreados
git ls-files --others --exclude-standard
```

---

## 🌐 NA VPS (via SSH)

### 2. Conectar na VPS

```bash
# Conectar via SSH (substitua com suas credenciais)
ssh usuario@IP_DA_VPS

# Ou se usar porta diferente
ssh -p 22 usuario@IP_DA_VPS
```

### 3. Informações do Sistema

```bash
# Ver sistema operacional
cat /etc/os-release

# Ver usuário atual
whoami

# Ver pasta home
pwd

# Ir para pasta do sistema
cd ~/sistema_pendencia

# Listar arquivos
ls -la

# Ver estrutura de pastas (se tiver tree instalado)
tree -L 2

# Ou usar ls
ls -R
```

### 4. Informações do Docker

```bash
# Listar containers
docker ps -a

# Ver logs do container (substitua NOME_CONTAINER)
docker logs NOME_CONTAINER --tail 50

# Ver docker-compose
cat docker-compose.yml

# Ver Dockerfile
cat Dockerfile

# Ver imagens Docker
docker images

# Ver uso de recursos
docker stats --no-stream
```

### 5. Informações do Banco de Dados

```bash
# Localizar banco SQLite
find ~/sistema_pendencia -name "*.db"

# Ver tamanho do banco
ls -lh ~/sistema_pendencia/instance/pendencias.db

# Ver backups (se existir)
ls -lh ~/sistema_pendencia/backups/

# Contar registros (exemplo)
sqlite3 ~/sistema_pendencia/instance/pendencias.db "SELECT COUNT(*) FROM pendencia;"
```

### 6. Arquivos de Configuração

```bash
# Ver requirements.txt
cat requirements.txt

# Ver .env (se existir - CUIDADO com senhas!)
cat .env

# Ver nginx.conf (se existir)
cat nginx.conf

# Ver start.sh (se existir)
cat start.sh

# Ver deploy.sh (se existir)
cat deploy.sh
```

### 7. Processo Python/Gunicorn

```bash
# Ver processos Python rodando
ps aux | grep python

# Ver processos Gunicorn (se usar)
ps aux | grep gunicorn

# Ver portas em uso
netstat -tulpn | grep :5000
# ou
ss -tulpn | grep :5000
```

### 8. Git na VPS

```bash
# Ir para pasta do sistema
cd ~/sistema_pendencia

# Ver status do git
git status

# Ver remote
git remote -v

# Ver branch atual
git branch

# Ver último commit
git log --oneline -5
```

---

## 📋 TEMPLATE PARA ME ENVIAR

Copie e cole os resultados assim:

```
========================================
INFORMAÇÕES DO SISTEMA UP380
========================================

=== 1. GIT LOCAL (Windows) ===
git status:
[COLE AQUI]

git remote -v:
[COLE AQUI]

git branch:
[COLE AQUI]

=== 2. SISTEMA VPS ===
Sistema operacional:
[COLE AQUI]

Usuário:
[COLE AQUI]

=== 3. DOCKER ===
docker ps:
[COLE AQUI]

docker-compose.yml:
[COLE AQUI]

=== 4. BANCO DE DADOS ===
Localização do .db:
[COLE AQUI]

Tamanho:
[COLE AQUI]

=== 5. CONFIGURAÇÕES ===
requirements.txt:
[COLE AQUI]

Tem .env? (SIM/NÃO):
[RESPONDA]

Usa Nginx? (SIM/NÃO):
[RESPONDA]

=== 6. ACESSO ===
IP da VPS:
[INFORME]

Usuário SSH:
[INFORME]

Domínio/URL em produção:
[INFORME]

=== 7. OUTROS ===
Quantas pendências tem cadastradas (aprox)?
[INFORME]

Quando foi o último deploy?
[INFORME]

Tem backup recente?
[INFORME]
```

---

## ⚠️ ATENÇÃO

**NÃO me envie senhas ou tokens!**

Se o `.env` ou outros arquivos tiverem senhas, **REMOVA** antes de me enviar:
- Senhas de banco
- Tokens de API
- Chaves secretas
- Credentials

Substitua por:
```
SECRET_KEY=XXXXX (removido)
DATABASE_URL=XXXXX (removido)
```

---

## 🚀 DEPOIS QUE EU RECEBER

Vou criar para você:

1. ✅ **Script de backup automático**
2. ✅ **Script de deploy seguro**
3. ✅ **Comandos de migração**
4. ✅ **Guia passo a passo**
5. ✅ **Plano de rollback (se der errado)**

---

**Execute os comandos e me envie os resultados!** 📊

