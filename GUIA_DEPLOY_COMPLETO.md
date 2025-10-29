# 🚀 GUIA COMPLETO DE DEPLOY - Sistema UP380
## Do desenvolvimento local → GitHub → VPS Produção

---

## 📋 ÍNDICE

1. [Preparação Local](#1-preparação-local)
2. [Commit e Push para GitHub](#2-commit-e-push-para-github)
3. [Deploy na VPS](#3-deploy-na-vps)
4. [Validação](#4-validação)
5. [Rollback (se necessário)](#5-rollback-se-necessário)

---

## 🎯 O QUE SERÁ ATUALIZADO

### ✅ Mudanças Implementadas:
1. **Sistema de Segmentos**
   - Nova tabela `segmento`
   - Campo `segmento_id` em `empresa`
   - Rotas e templates para segmentos

2. **Dashboard com Gráficos**
   - API endpoint `/api/dados_graficos`
   - `static/graficos.js`
   - `static/chart.min.js` (local)

3. **Planilhas Modelo Corrigidas**
   - 9 planilhas com campos corretos
   - Banco e fornecedor em todas

4. **Melhorias no Sistema**
   - Exclusão de empresas com validação
   - Campo data_abertura em pendências
   - CSP ajustado

---

## 1. PREPARAÇÃO LOCAL

### 1.1. Verificar Status Atual

```bash
# Ir para pasta do projeto
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"

# Ver status
git status

# Ver arquivos modificados
git diff --name-only
```

### 1.2. Adicionar Novos Arquivos

```bash
# Adicionar planilhas modelo
git add modelo_*.xlsx

# Adicionar script de migração
git add migracao_producao_completa.py

# Adicionar arquivos modificados
git add app.py
git add requirements.txt
git add templates/
git add static/

# Adicionar documentação (opcional)
git add *.md
```

### 1.3. Verificar o que será commitado

```bash
# Ver lista de arquivos staged
git status

# Ver diferenças dos arquivos
git diff --cached
```

---

## 2. COMMIT E PUSH PARA GITHUB

### 2.1. Fazer Commit

```bash
# Commit com mensagem descritiva
git commit -m "feat: Implementação completa de segmentos, correção de planilhas e melhorias no dashboard

- Adiciona sistema de segmentos para organização de empresas
- Corrige planilhas modelo com todos os campos necessários (banco, fornecedor)
- Implementa gráficos do dashboard com Chart.js local
- Adiciona validações na exclusão de empresas
- Adiciona campo data_abertura em pendências
- Inclui script de migração para produção (migracao_producao_completa.py)
- Ajusta CSP para permitir funcionamento dos gráficos

Arquivos principais modificados:
- app.py: Rotas de segmentos, API gráficos, validações
- templates/: Novos templates para segmentos
- static/: graficos.js e chart.min.js
- modelo_*.xlsx: 9 planilhas corrigidas
- migracao_producao_completa.py: Script de migração

IMPORTANTE: Executar migracao_producao_completa.py na VPS antes de iniciar"
```

### 2.2. Push para GitHub

```bash
# Push para branch main (ou master)
git push origin main

# Se for a primeira vez:
git push -u origin main
```

### 2.3. Verificar no GitHub

```
1. Acesse: https://github.com/seu-usuario/seu-repositorio
2. Verifique se o commit apareceu
3. Verifique se todos os arquivos estão lá
```

---

## 3. DEPLOY NA VPS

### 3.1. Conectar na VPS

```bash
# Conectar via SSH
ssh usuario@IP_DA_VPS

# Exemplo:
ssh root@123.456.789.012
```

### 3.2. Ir para Pasta do Sistema

```bash
# Ir para pasta
cd ~/sistema_pendencia

# Ver branch atual
git branch

# Ver status
git status
```

### 3.3. BACKUP ANTES DE TUDO! 🔒

```bash
# Criar pasta de backups se não existir
mkdir -p backups

# Backup do banco de dados
cp instance/pendencias.db backups/pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Backup de todo o sistema
tar -czf backups/sistema_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude='backups' \
    --exclude='.git' \
    --exclude='__pycache__' \
    .

# Verificar backups
ls -lh backups/

echo "✅ Backups criados com sucesso!"
```

### 3.4. Parar o Container Docker

```bash
# Listar containers rodando
docker ps

# Parar o container (substitua NOME_CONTAINER)
docker stop NOME_CONTAINER

# Ou se estiver usando docker-compose:
docker-compose down

echo "⏸️  Container parado"
```

### 3.5. Atualizar Código do GitHub

```bash
# Pull do código novo
git pull origin main

# Ver o que mudou
git log --oneline -5

# Verificar se arquivos foram atualizados
ls -la modelo_*.xlsx
ls -la migracao_producao_completa.py

echo "✅ Código atualizado do GitHub"
```

### 3.6. Executar Migração do Banco de Dados

```bash
# Rodar script de migração
python3 migracao_producao_completa.py

# O script vai:
# 1. Criar backup automático
# 2. Adicionar tabela segmento
# 3. Adicionar campo segmento_id em empresa
# 4. Popular segmentos
# 5. Vincular empresas aos segmentos
# 6. Verificar campo data_abertura
# 7. Validar integridade dos dados

# Se tudo der certo, você verá:
# ✅ TODAS AS MIGRAÇÕES CONCLUÍDAS COM SUCESSO!
```

### 3.7. Atualizar Dependências (se necessário)

```bash
# Atualizar requirements (se mudou)
pip install -r requirements.txt --upgrade

# Ou se usar venv:
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 3.8. Rebuild do Container Docker

```bash
# Se usar docker-compose:
docker-compose build

# Ou rebuild da imagem:
docker build -t sistema_up380 .

echo "✅ Container rebuilded"
```

### 3.9. Iniciar Container

```bash
# Se usar docker-compose:
docker-compose up -d

# Ou docker run:
docker start NOME_CONTAINER

# Verificar se está rodando
docker ps

# Ver logs
docker logs NOME_CONTAINER --tail 50 -f

# Pressione Ctrl+C para sair dos logs

echo "🚀 Container iniciado!"
```

### 3.10. Verificar Aplicação

```bash
# Testar se está respondendo
curl http://localhost:5000

# Ou acessar pelo navegador:
# http://SEU_DOMINIO
```

---

## 4. VALIDAÇÃO

### 4.1. Testes na VPS

```bash
# Conectar ao container (se necessário)
docker exec -it NOME_CONTAINER bash

# Verificar banco de dados
sqlite3 instance/pendencias.db "SELECT COUNT(*) FROM segmento;"
sqlite3 instance/pendencias.db "SELECT COUNT(*) FROM empresa WHERE segmento_id IS NOT NULL;"
sqlite3 instance/pendencias.db "SELECT COUNT(*) FROM pendencia;"

# Sair do container
exit
```

### 4.2. Testes no Navegador

```
✅ Acesse: http://SEU_DOMINIO

Testar:
1. Login funciona?
2. Dashboard aparece com gráficos?
3. Menu "Segmentos" aparece?
4. Consegue acessar /segmentos?
5. Consegue ver empresas por segmento?
6. Importação de planilha funciona?
7. Baixar planilha modelo funciona?
8. Todos os campos aparecem (banco, fornecedor)?
```

### 4.3. Checklist de Validação

```
[ ] Sistema acessível
[ ] Login funciona
[ ] Dashboard carrega
[ ] Gráficos aparecem
[ ] Menu Segmentos visível
[ ] Listar segmentos funciona
[ ] Ver empresas por segmento funciona
[ ] Pendências antigas estão lá
[ ] Importação funciona
[ ] Planilhas modelo baixam corretamente
[ ] Campos banco e fornecedor aparecem
```

---

## 5. ROLLBACK (Se Necessário)

### Se algo der errado:

```bash
# 1. Parar container
docker-compose down

# 2. Restaurar backup do banco
cp backups/pendencias_backup_TIMESTAMP.db instance/pendencias.db

# 3. Voltar código anterior
git reset --hard HEAD~1

# 4. Rebuild
docker-compose build

# 5. Iniciar
docker-compose up -d

# 6. Verificar
docker ps
docker logs NOME_CONTAINER
```

---

## 📝 RESUMO DOS COMANDOS

### No Windows (Local):

```bash
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
git add .
git commit -m "feat: Implementação de segmentos e correções"
git push origin main
```

### Na VPS:

```bash
ssh usuario@IP_VPS
cd ~/sistema_pendencia

# Backup
mkdir -p backups
cp instance/pendencias.db backups/pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Parar
docker-compose down

# Atualizar
git pull origin main

# Migrar
python3 migracao_producao_completa.py

# Rebuild e iniciar
docker-compose build
docker-compose up -d

# Verificar
docker ps
docker logs -f NOME_CONTAINER
```

---

## ⚠️ PONTOS DE ATENÇÃO

### ❗ IMPORTANTE:

1. **SEMPRE faça backup antes**
2. **Teste a migração localmente primeiro** (opcional mas recomendado)
3. **Mantenha o backup do banco** até confirmar que tudo funciona
4. **Documente o tempo de downtime**
5. **Avise usuários** se necessário

### 🔍 Se der erro na migração:

1. O script cria backup automático
2. Veja a mensagem de erro
3. Restaure o backup
4. Me avise do erro para ajustar

### 📞 Suporte:

Se encontrar problemas:
1. Copie mensagem de erro completa
2. Execute: `docker logs NOME_CONTAINER`
3. Me envie para análise

---

## 🎉 SUCESSO!

Se tudo funcionou:
```
✅ Código no GitHub
✅ VPS atualizada
✅ Migração executada
✅ Dados preservados
✅ Sistema funcionando
✅ Novas funcionalidades ativas
```

**Parabéns! Deploy concluído com sucesso!** 🚀

---

**Tempo estimado total:** 15-30 minutos
**Downtime estimado:** 5-10 minutos
**Dificuldade:** Média
**Reversibilidade:** Alta (com backups)


