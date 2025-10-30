# ✅ CHECKLIST VISUAL - DEPLOY SEM LIMITADORES

## 📅 Data do Deploy: ___/___/2025
## ⏰ Horário de Início: ___:___
## 👤 Responsável: ________________

---

## 🖥️ FASE 1: DESENVOLVIMENTO (Windows)

### Verificação Inicial:
- [ ] Todos os arquivos estão salvos
- [ ] Nenhum erro de sintaxe nos arquivos
- [ ] Terminal aberto na pasta correta

### Git - Commitar Alterações:
```powershell
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
```

- [ ] Comando `cd` executado
- [ ] Pasta correta confirmada (`pwd` ou `Get-Location`)

```powershell
git status
```
- [ ] Status verificado
- [ ] Arquivos modificados listados: `app.py`, `nginx.conf`

```powershell
git add app.py nginx.conf DEPLOY_SEM_LIMITES.md COMANDOS_DEPLOY_SEM_LIMITES.txt RESUMO_ALTERACOES_SEM_LIMITES.md CHECKLIST_VISUAL_DEPLOY.md
```
- [ ] Arquivos adicionados ao stage

```powershell
git commit -m "fix: Remove limitadores + corrige login (SameSite=Lax)"
```
- [ ] Commit criado com sucesso
- [ ] Mensagem do commit correta

```powershell
git push origin main
```
- [ ] Push para GitHub bem-sucedido
- [ ] Sem erros de autenticação

### Verificação Final no Windows:
- [ ] GitHub atualizado (verificar no navegador)
- [ ] Último commit aparece no repositório

**⏱️ Tempo estimado: 5 minutos**  
**✅ Fase 1 concluída em: ___:___**

---

## 🖥️ FASE 2: VPS - BACKUP

### Conectar na VPS:
```bash
ssh root@SEU_IP_VPS
```
- [ ] Conectado na VPS com sucesso
- [ ] Prompt mostra: `root@nsX:~#`

### Navegar para a pasta:
```bash
cd ~/sistema_pendencia
```
- [ ] Pasta correta
- [ ] Comando `pwd` retorna: `/root/sistema_pendencia`

### Criar pasta de backup:
```bash
mkdir -p backups
```
- [ ] Pasta criada

### Fazer backup do banco de dados:
```bash
cp instance/pendencias.db backups/pendencias_backup_$(date +%Y%m%d_%H%M%S).db
```
- [ ] Backup criado

### Verificar backup:
```bash
ls -lh backups/
```
- [ ] Arquivo de backup listado
- [ ] Tamanho do arquivo parece correto (não é 0 bytes)
- [ ] Nome do arquivo: `pendencias_backup_XXXXXXXX_XXXXXX.db`

**📝 Anotar nome do backup:** _______________________________

**⏱️ Tempo estimado: 3 minutos**  
**✅ Fase 2 concluída em: ___:___**

---

## 🖥️ FASE 3: VPS - ATUALIZAR CÓDIGO

### Puxar atualizações do Git:
```bash
git pull origin main
```
- [ ] Pull executado com sucesso
- [ ] Mensagem mostra: "Fast-forward" ou "Already up to date"
- [ ] Arquivos atualizados: `app.py`, `nginx.conf`

### Verificar alterações:
```bash
git log -3 --oneline
```
- [ ] Último commit é o de remoção dos limitadores
- [ ] Mensagem do commit está correta

### Verificar conteúdo dos arquivos:
```bash
grep -n "SESSION_COOKIE_SAMESITE" app.py
```
- [ ] Mostra linha com: `'Lax'`

```bash
grep -n "limit_req" nginx.conf
```
- [ ] Linhas comentadas (começam com `#`)

**⏱️ Tempo estimado: 2 minutos**  
**✅ Fase 3 concluída em: ___:___**

---

## 🖥️ FASE 4: VPS - REBUILD CONTAINERS

### ⚠️ ATENÇÃO: Esta etapa vai derrubar o sistema temporariamente!

### Parar containers:
```bash
docker-compose down
```
- [ ] Containers parados
- [ ] Mensagem: "Stopping sistema_pendencia-web-1 ... done"
- [ ] Mensagem: "Stopping sistema_pendencia-nginx-1 ... done"

### Reconstruir imagens (SEM CACHE):
```bash
docker-compose build --no-cache
```
- [ ] Build iniciado
- [ ] Baixando dependências
- [ ] Build concluído sem erros
- [ ] Mensagem final: "Successfully built"

**⏱️ Tempo estimado: 3-5 minutos**

### Subir containers:
```bash
docker-compose up -d
```
- [ ] Containers criados
- [ ] Mensagem: "Creating sistema_pendencia-web-1 ... done"
- [ ] Mensagem: "Creating sistema_pendencia-nginx-1 ... done"

### Verificar status:
```bash
docker-compose ps
```
- [ ] `sistema_pendencia-web-1` com status: `Up`
- [ ] `sistema_pendencia-nginx-1` com status: `Up`
- [ ] Porta 5000 mapeada (web)
- [ ] Portas 80 e 443 mapeadas (nginx)

**⏱️ Tempo estimado: 1 minuto**  
**✅ Fase 4 concluída em: ___:___**

---

## 🖥️ FASE 5: VPS - VERIFICAR LOGS

### Ver logs do web:
```bash
docker-compose logs web | tail -50
```
- [ ] Logs aparecem
- [ ] Sem erros críticos
- [ ] Mensagem mostra: "Serving Flask app"
- [ ] Sem linhas com "ERROR" ou "CRITICAL"

### Ver logs do nginx:
```bash
docker-compose logs nginx | tail -30
```
- [ ] Logs aparecem
- [ ] Nginx iniciado com sucesso
- [ ] Sem mensagens de erro
- [ ] Sem "emerg" ou "alert"

### Testar aplicação localmente:
```bash
curl http://localhost:5000
```
- [ ] Retorna HTML (página de login)
- [ ] Sem erro 500 ou 502
- [ ] Resposta recebida

**⏱️ Tempo estimado: 2 minutos**  
**✅ Fase 5 concluída em: ___:___**

---

## 🖥️ FASE 6: VPS - VERIFICAR BANCO DE DADOS

### Entrar no container e verificar dados:
```bash
docker exec -it sistema_pendencia-web-1 python3 << 'EOF'
from app import db, Pendencia, Usuario, Empresa
print(f"Pendências: {Pendencia.query.count()}")
print(f"Usuários: {Usuario.query.count()}")
print(f"Empresas: {Empresa.query.count()}")
EOF
```

**📝 Anotar valores:**
- [ ] Pendências: _______ (deve ser > 0 se tinha dados antes)
- [ ] Usuários: _______ (deve ser > 0)
- [ ] Empresas: _______ (deve ser > 0)

**✅ Os números batem com os esperados?** [ ] Sim [ ] Não

Se **NÃO**, restaurar backup:
```bash
docker-compose down
cp backups/pendencias_backup_XXXXXXXX_XXXXXX.db instance/pendencias.db
docker-compose up -d
```

**⏱️ Tempo estimado: 1 minuto**  
**✅ Fase 6 concluída em: ___:___**

---

## 🌐 FASE 7: TESTES NO NAVEGADOR

### Teste com Administrador:

#### 1. Limpar cache do navegador:
- [ ] Pressionar `Ctrl + Shift + Del`
- [ ] Marcar: Cookies e dados de sites
- [ ] Marcar: Imagens e arquivos em cache
- [ ] Período: Todo o período
- [ ] Clicar em "Limpar dados"
- [ ] Fechar navegador completamente
- [ ] Aguardar 15 segundos

#### 2. Fazer login:
- [ ] Abrir navegador
- [ ] Acessar: http://sistemapendencia.up380.com.br
- [ ] Tela de login aparece
- [ ] Inserir credenciais de admin
- [ ] Clicar em "Entrar"
- [ ] **Login bem-sucedido** (não volta para tela de login)
- [ ] Página de segmentos aparece

#### 3. Testar funcionalidades:
- [ ] Dashboard carrega sem erros
- [ ] Gráficos aparecem
- [ ] Lista de pendências carrega
- [ ] Consegue abrir uma pendência existente

#### 4. Criar nova pendência:
- [ ] Clicar em "Nova Pendência"
- [ ] Preencher formulário
- [ ] Clicar em "Salvar"
- [ ] Pendência criada com sucesso (sem erro 429)

#### 5. Testar upload de arquivo:
- [ ] Fazer upload de um arquivo na pendência
- [ ] Upload completa sem erros
- [ ] Arquivo aparece anexado

### Teste com Operador:

#### 1. Limpar cache:
- [ ] Operador limpou cache do navegador
- [ ] Navegador fechado e reaberto

#### 2. Fazer login:
- [ ] Operador consegue fazer login
- [ ] Não ocorre loop de login
- [ ] Dashboard aparece

#### 3. Testar funcionalidades:
- [ ] Operador consegue criar pendência
- [ ] Operador consegue editar pendência
- [ ] Operador consegue fazer upload
- [ ] Operador consegue importar planilha

### Teste com Cliente:

#### 1. Limpar cache:
- [ ] Cliente limpou cache
- [ ] Navegador fechado e reaberto

#### 2. Fazer login e responder:
- [ ] Cliente consegue fazer login
- [ ] Cliente vê apenas suas empresas
- [ ] Cliente consegue responder pendências
- [ ] Cliente consegue fazer upload de resposta

**⏱️ Tempo estimado: 10-15 minutos**  
**✅ Fase 7 concluída em: ___:___**

---

## 🖥️ FASE 8: MONITORAMENTO PÓS-DEPLOY

### Verificar logs em tempo real (5 minutos):
```bash
docker-compose logs -f
```
- [ ] Logs fluindo normalmente
- [ ] Requisições aparecem
- [ ] Sem erros 429
- [ ] Sem erros 500
- [ ] Pressionar `Ctrl+C` para sair

### Verificar uso de recursos:
```bash
docker stats --no-stream
```
- [ ] CPU do web: _______% (esperado: < 50%)
- [ ] Memória do web: _______MB (esperado: < 500MB)
- [ ] CPU do nginx: _______% (esperado: < 10%)
- [ ] Memória do nginx: _______MB (esperado: < 50MB)

### Verificar conectividade externa:

**No seu computador (não na VPS):**
- [ ] Acessar: http://sistemapendencia.up380.com.br
- [ ] Site carrega
- [ ] Sem erro de SSL (se HTTPS)
- [ ] Login funciona

**⏱️ Tempo estimado: 10 minutos**  
**✅ Fase 8 concluída em: ___:___**

---

## 📢 FASE 9: COMUNICAÇÃO

### Avisar usuários:
- [ ] Enviar e-mail/mensagem para todos os operadores
- [ ] Informar que devem limpar cache do navegador
- [ ] Informar as melhorias implementadas
- [ ] Fornecer contato para suporte

### Mensagem modelo:
```
📢 Atualização do Sistema - 30/10/2025

Olá!

Realizamos uma atualização importante no sistema de pendências:

✅ Corrigido problema de login (loop)
✅ Removidos limites de requisições (sem mais erro 429)
✅ Uploads sem limite de tamanho
✅ Sistema mais rápido e estável

IMPORTANTE: 
Antes de usar o sistema, limpe o cache do navegador:
1. Pressione Ctrl + Shift + Del
2. Marque: Cookies e cache
3. Período: Todo o período
4. Clique em "Limpar dados"
5. Feche e abra o navegador novamente

Qualquer problema, entre em contato.

Atenciosamente,
Equipe de TI
```

- [ ] Mensagem enviada
- [ ] Usuários confirmaram recebimento

**⏱️ Tempo estimado: 5 minutos**  
**✅ Fase 9 concluída em: ___:___**

---

## 📊 FASE 10: RELATÓRIO FINAL

### Estatísticas do Deploy:

| Item | Status |
|------|--------|
| Backup criado | ✅ [ ] Sim [ ] Não |
| Git atualizado | ✅ [ ] Sim [ ] Não |
| Containers reconstruídos | ✅ [ ] Sim [ ] Não |
| Dados preservados | ✅ [ ] Sim [ ] Não |
| Login funcionando | ✅ [ ] Sim [ ] Não |
| Erro 429 eliminado | ✅ [ ] Sim [ ] Não |
| Uploads funcionando | ✅ [ ] Sim [ ] Não |
| Usuários avisados | ✅ [ ] Sim [ ] Não |

### Resumo:

**Horário de conclusão:** ___:___  
**Tempo total de deploy:** _______ minutos  
**Downtime (sistema fora do ar):** _______ minutos  

**Problemas encontrados:**
- [ ] Nenhum
- [ ] Sim, descrição: _________________________________

**Rollback necessário?**
- [ ] Não
- [ ] Sim, motivo: _________________________________

### Assinaturas:

**Responsável pelo deploy:**  
Nome: ________________  
Assinatura: ________________  
Data/Hora: ___/___/2025 - ___:___

**Validador (se aplicável):**  
Nome: ________________  
Assinatura: ________________  
Data/Hora: ___/___/2025 - ___:___

---

## 🎯 CHECKLIST DE VALIDAÇÃO (24h APÓS DEPLOY)

### Dia Seguinte - Verificar:

- [ ] Sistema está online
- [ ] Nenhum usuário reportou problemas
- [ ] Logs sem erros críticos
- [ ] Performance estável
- [ ] Todos os módulos funcionando

### Comandos para verificação 24h depois:

```bash
# Ver logs das últimas 24h
docker-compose logs --since 24h | grep -i error

# Ver estatísticas
docker stats --no-stream

# Ver uptime dos containers
docker-compose ps

# Contar requisições bem-sucedidas
docker-compose logs nginx | grep "GET" | wc -l
```

**Tudo funcionando normalmente após 24h?** [ ] Sim [ ] Não

Se **SIM**: Deploy concluído com sucesso! 🎉  
Se **NÃO**: Investigar logs e considerar rollback.

---

## 📞 CONTATOS DE EMERGÊNCIA

**Em caso de problemas críticos, contactar:**

1. **Desenvolvedor/Suporte:**  
   Nome: ________________  
   Telefone: ________________  
   E-mail: ________________

2. **Backup do Desenvolvedor:**  
   Nome: ________________  
   Telefone: ________________  
   E-mail: ________________

---

## 🆘 COMANDOS DE EMERGÊNCIA

### Se tudo der errado, restaurar backup:

```bash
# Parar sistema
docker-compose down

# Restaurar banco (substituir XXXXXXXX pelo nome do backup)
cp backups/pendencias_backup_XXXXXXXX_XXXXXX.db instance/pendencias.db

# Subir novamente
docker-compose up -d

# Verificar
docker-compose ps
docker-compose logs -f
```

### Se precisar reverter código (Git):

```bash
# Ver últimos commits
git log --oneline

# Reverter para commit anterior (substituir HASH)
git reset --hard HASH

# Reconstruir
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

**✅ DEPLOY COMPLETO E VALIDADO!**

**Data de conclusão:** ___/___/2025  
**Horário:** ___:___  
**Status final:** [ ] Sucesso [ ] Parcial [ ] Falha

---

**🎉 PARABÉNS! SISTEMA SEM LIMITADORES EM PRODUÇÃO!**

