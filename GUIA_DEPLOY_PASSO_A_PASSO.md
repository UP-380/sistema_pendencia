# 🚀 GUIA COMPLETO: DEPLOY PARA PRODUÇÃO VPS

## ⚠️ IMPORTANTE
Este guia irá atualizar sua aplicação em produção SEM PERDER NENHUM DADO.
As migrações foram preparadas para serem **IDEMPOTENTES** (podem ser executadas múltiplas vezes sem problemas).

---

## 📦 PARTE 1: PREPARAR E ENVIAR CÓDIGO (WINDOWS)

### 1️⃣ Verificar o que foi modificado

Abra o **PowerShell** na pasta do projeto e execute:

```powershell
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
git status
```

**O que você deve ver:**
- Arquivos modificados (modified)
- Arquivos novos (untracked)

---

### 2️⃣ Adicionar todos os arquivos ao Git

```powershell
# Adicionar TODOS os arquivos modificados e novos
git add .

# Verificar o que será commitado
git status
```

**Você deve ver:**
- ✅ `app.py` (modificado)
- ✅ `requirements.txt` (modificado)
- ✅ `templates/base.html` (modificado)
- ✅ `templates/supervisor_pendencias.html` (modificado)
- ✅ `templates/editar_pendencia.html` (modificado)
- ✅ `templates/nova_pendencia.html` (modificado)
- ✅ `templates/importar_planilha.html` (modificado)
- ✅ `static/up380.css` (modificado)
- ✅ `migracao_producao_completa.py` (novo)
- ✅ `migracao_consolidar_documentos.py` (novo)
- ✅ `modelo_*.xlsx` (novos - 9 arquivos)
- ✅ Arquivos de documentação `.md` (novos)

---

### 3️⃣ Fazer o commit

```powershell
git commit -m "feat: Adiciona sistema de segmentos, ajustes frontend e novas planilhas modelo

- Implementa sistema completo de segmentos e vinculação de empresas
- Adiciona planilhas modelo individuais para cada tipo de pendência
- Corrige campo Banco para sempre aparecer nos formulários
- Melhora parsing de valores monetários em formato brasileiro
- Ajusta modal do supervisor para textos longos
- Inclui migrações de banco de dados seguras
- Adiciona consolidação de tipos de documentos antigos"
```

---

### 4️⃣ Enviar para o GitHub

```powershell
git push origin main
```

**Se pedir usuário e senha:**
- Usuário: seu email do GitHub
- Senha: seu **Personal Access Token** (não é a senha normal!)

---

## 🔧 PARTE 2: FAZER BACKUP DA PRODUÇÃO (VPS)

### 1️⃣ Conectar à VPS via SSH

```powershell
ssh seu_usuario@seu_ip_da_vps
```

**Exemplo:**
```powershell
ssh root@123.456.789.0
```

---

### 2️⃣ Fazer backup do banco de dados ATUAL

```bash
# Ir para a pasta do projeto
cd ~/sistema_pendencia

# Criar pasta de backups se não existir
mkdir -p backups

# Fazer backup com data/hora
docker exec sistema_pendencia-web-1 python backup_database.py

# OU manualmente:
docker cp sistema_pendencia-web-1:/app/instance/pendencias.db ./backups/pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Verificar se o backup foi criado
ls -lh backups/
```

**✅ IMPORTANTE:** Guarde este backup! Se algo der errado, você pode restaurar.

---

## 🔄 PARTE 3: ATUALIZAR O CÓDIGO NA VPS

### 1️⃣ Ir para a pasta do projeto

```bash
cd ~/sistema_pendencia
```

---

### 2️⃣ Verificar a branch atual

```bash
git branch
git status
```

---

### 3️⃣ Puxar as atualizações do GitHub

```bash
# Buscar as atualizações
git fetch origin

# Atualizar o código
git pull origin main
```

**Se aparecer conflitos:**
```bash
# Ver quais arquivos têm conflito
git status

# Se quiser usar SEMPRE a versão nova do GitHub:
git reset --hard origin/main
```

---

### 4️⃣ Verificar se os arquivos foram atualizados

```bash
# Verificar se os arquivos de migração estão presentes
ls -lh migra*.py

# Verificar se as planilhas foram criadas
ls -lh modelo_*.xlsx

# Verificar a data de modificação do app.py
ls -lh app.py
```

---

## 🗄️ PARTE 4: EXECUTAR AS MIGRAÇÕES (SEM PERDER DADOS!)

### 1️⃣ Parar os containers

```bash
docker-compose down
```

---

### 2️⃣ Executar a migração PRINCIPAL (Segmentos + Campos)

```bash
# Executar a migração dentro do container
docker-compose run --rm web python migracao_producao_completa.py
```

**O que esta migração faz:**
- ✅ Cria tabela `segmento` se não existir
- ✅ Adiciona coluna `segmento_id` na tabela `empresa` se não existir
- ✅ Cria segmentos padrão (AGRO, CONSTRUÇÃO, EDUCAÇÃO, etc.)
- ✅ Vincula empresas existentes aos segmentos automaticamente
- ✅ Adiciona campo `data` na tabela `pendencia` se não existir
- ✅ Preenche datas faltantes com `data_abertura`
- ✅ **NÃO PERDE NENHUM DADO EXISTENTE**

**Saída esperada:**
```
=== INICIANDO MIGRAÇÃO PARA PRODUÇÃO ===
[OK] Tabela 'segmento' criada com sucesso
[OK] Coluna 'segmento_id' adicionada à tabela 'empresa'
[OK] 6 segmentos criados
[OK] 15 empresas vinculadas aos segmentos
[OK] Coluna 'data' adicionada à tabela 'pendencia'
[OK] 120 pendências atualizadas com datas
=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===
```

---

### 3️⃣ Executar a migração de DOCUMENTOS (Consolidação)

```bash
# Executar a segunda migração
docker-compose run --rm web python migracao_consolidar_documentos.py
```

**O que esta migração faz:**
- ✅ Converte pendências antigas:
  - "NOTA FISCAL NÃO ANEXADA" → "DOCUMENTO NÃO ANEXADO"
  - "NOTA FISCAL NÃO IDENTIFICADA" → "DOCUMENTO NÃO ANEXADO"
- ✅ Registra logs de todas as alterações
- ✅ Mantém histórico completo
- ✅ **NÃO APAGA NADA, APENAS RENOMEIA**

**Saída esperada:**
```
=== MIGRAÇÃO: CONSOLIDAR TIPOS DE DOCUMENTOS ===
[INFO] 45 pendências de 'NOTA FISCAL NÃO ANEXADA' encontradas
[INFO] 23 pendências de 'NOTA FISCAL NÃO IDENTIFICADA' encontradas
[OK] 68 pendências migradas para 'DOCUMENTO NÃO ANEXADO'
[OK] 68 logs criados
=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===
```

---

## 🚀 PARTE 5: REINICIAR A APLICAÇÃO

### 1️⃣ Subir os containers novamente

```bash
# Subir os containers em modo detached (background)
docker-compose up -d --build
```

**O que acontece:**
- Reconstrói a imagem Docker com o código novo
- Instala dependências atualizadas do `requirements.txt`
- Inicia a aplicação

---

### 2️⃣ Verificar se os containers estão rodando

```bash
docker-compose ps
```

**Saída esperada:**
```
NAME                       STATUS              PORTS
sistema_pendencia-web-1    Up 10 seconds      0.0.0.0:5000->5000/tcp
```

---

### 3️⃣ Verificar os logs da aplicação

```bash
# Ver os logs em tempo real
docker-compose logs -f web

# OU apenas as últimas 50 linhas
docker-compose logs --tail=50 web
```

**Procure por:**
- ✅ `Running on http://0.0.0.0:5000`
- ✅ Sem erros de importação
- ✅ Sem erros de banco de dados

**Para sair dos logs:** Pressione `Ctrl + C`

---

## ✅ PARTE 6: VALIDAR A APLICAÇÃO

### 1️⃣ Testar o acesso via navegador

Abra seu navegador e acesse:
```
http://seu_ip_da_vps:5000
```

**OU se tiver domínio configurado:**
```
https://seu-dominio.com.br
```

---

### 2️⃣ Fazer login e verificar

1. ✅ Faça login com seu usuário
2. ✅ Vá em **"Segmentos"** no menu
3. ✅ Verifique se os segmentos aparecem (AGRO, CONSTRUÇÃO, etc.)
4. ✅ Clique em um segmento e veja se as empresas aparecem
5. ✅ Vá em **"Empresas"** no menu
6. ✅ Clique em **"Nova Pendência"**
7. ✅ Verifique se o campo **"Banco"** aparece
8. ✅ Vá em **"Importar Planilha"**
9. ✅ Baixe uma planilha modelo e veja se baixa corretamente
10. ✅ Vá em **"Supervisor"** (se for supervisor/adm)
11. ✅ Abra uma pendência e veja se o modal aparece correto

---

### 3️⃣ Verificar pendências existentes

```bash
# Conectar no container
docker exec -it sistema_pendencia-web-1 bash

# Abrir o Python
python

# Verificar os dados
from app import db, Pendencia, Empresa, Segmento

# Ver quantas pendências existem
print(f"Total de pendências: {Pendencia.query.count()}")

# Ver quantos segmentos existem
print(f"Total de segmentos: {Segmento.query.count()}")

# Ver quantas empresas existem
print(f"Total de empresas: {Empresa.query.count()}")

# Ver empresas por segmento
for seg in Segmento.query.all():
    print(f"{seg.nome}: {len(seg.empresas)} empresas")

# Sair
exit()
exit
```

---

## 🆘 PARTE 7: SE ALGO DER ERRADO

### ❌ Caso 1: Erro durante a migração

```bash
# Parar containers
docker-compose down

# Restaurar o backup
docker cp ./backups/pendencias_backup_XXXXXXXX_XXXXXX.db sistema_pendencia-web-1:/app/instance/pendencias.db

# Subir novamente
docker-compose up -d

# Ver os logs do erro
docker-compose logs --tail=100 web
```

---

### ❌ Caso 2: Aplicação não inicia

```bash
# Ver os logs completos
docker-compose logs web

# Ver erros do Python
docker-compose logs web | grep -i error

# Verificar se o banco existe
docker exec -it sistema_pendencia-web-1 ls -lh instance/

# Reiniciar completamente
docker-compose down
docker-compose up -d --build
```

---

### ❌ Caso 3: Página em branco ou erro 500

```bash
# Ver logs em tempo real
docker-compose logs -f web

# Verificar permissões
docker exec -it sistema_pendencia-web-1 bash
ls -lh instance/
chmod 644 instance/pendencias.db
exit

# Reiniciar
docker-compose restart web
```

---

## 📊 PARTE 8: COMANDOS ÚTEIS

### Verificar espaço em disco
```bash
df -h
```

### Ver uso de memória
```bash
free -h
```

### Ver containers rodando
```bash
docker ps
```

### Ver imagens Docker
```bash
docker images
```

### Limpar containers antigos
```bash
docker system prune -a
```

### Ver logs específicos
```bash
# Logs do Nginx (se usar)
docker-compose logs nginx

# Logs do banco (se usar PostgreSQL)
docker-compose logs db
```

---

## 🎯 RESUMO DOS COMANDOS

### NO WINDOWS (PowerShell):
```powershell
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
git add .
git commit -m "Atualização com segmentos e melhorias"
git push origin main
```

### NA VPS (SSH):
```bash
# Backup
cd ~/sistema_pendencia
docker cp sistema_pendencia-web-1:/app/instance/pendencias.db ./backups/pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Atualizar código
git pull origin main

# Parar
docker-compose down

# Migrar
docker-compose run --rm web python migracao_producao_completa.py
docker-compose run --rm web python migracao_consolidar_documentos.py

# Subir
docker-compose up -d --build

# Verificar
docker-compose logs -f web
```

---

## ✅ CHECKLIST FINAL

Antes de considerar o deploy concluído, verifique:

- [ ] Backup do banco foi feito
- [ ] Código foi puxado do Git
- [ ] Migração 1 executada sem erros
- [ ] Migração 2 executada sem erros
- [ ] Containers estão rodando (`docker-compose ps`)
- [ ] Aplicação abre no navegador
- [ ] Login funciona
- [ ] Menu "Segmentos" aparece e funciona
- [ ] Empresas estão vinculadas aos segmentos
- [ ] Campo "Banco" aparece nos formulários
- [ ] Planilhas modelo podem ser baixadas
- [ ] Modal do supervisor funciona corretamente
- [ ] Pendências antigas ainda aparecem
- [ ] Não há erros nos logs

---

## 📞 SUPORTE

Se encontrar qualquer erro:

1. **Anote a mensagem de erro COMPLETA**
2. **Copie os logs:** `docker-compose logs web > erro.log`
3. **Tire um print da tela**
4. **Me envie para análise**

---

## 🎉 PRONTO!

Seu sistema está atualizado em produção com:
- ✅ Sistema de Segmentos
- ✅ Planilhas modelo individuais
- ✅ Campo Banco corrigido
- ✅ Modal do supervisor ajustado
- ✅ Consolidação de tipos de documentos
- ✅ Todos os dados preservados

**Bom trabalho! 🚀**


