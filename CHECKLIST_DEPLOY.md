# ✅ CHECKLIST DE DEPLOY - MARQUE CONFORME VAI FAZENDO

## 📦 FASE 1: PREPARAÇÃO (WINDOWS)

- [ ] Abri o PowerShell na pasta do projeto
- [ ] Executei `git status` e vi os arquivos modificados
- [ ] Executei `git add .` para adicionar tudo
- [ ] Executei `git commit` com mensagem descritiva
- [ ] Executei `git push origin main` e código foi enviado

---

## 🔒 FASE 2: BACKUP (VPS)

- [ ] Conectei na VPS via SSH
- [ ] Fui para a pasta `~/sistema_pendencia`
- [ ] Criei a pasta `backups` (se não existir)
- [ ] Executei o backup do banco de dados
- [ ] Verifiquei que o arquivo `.db` foi criado em `backups/`

---

## 🔄 FASE 3: ATUALIZAÇÃO (VPS)

- [ ] Executei `git pull origin main`
- [ ] Código foi atualizado sem conflitos
- [ ] Verifiquei que `migracao_producao_completa.py` existe
- [ ] Verifiquei que `migracao_consolidar_documentos.py` existe
- [ ] Verifiquei que as planilhas `modelo_*.xlsx` existem (9 arquivos)

---

## 🗄️ FASE 4: MIGRAÇÃO (VPS)

- [ ] Executei `docker-compose down` para parar containers
- [ ] Executei `migracao_producao_completa.py` - SEM ERROS
- [ ] Vi mensagem de sucesso da migração 1
- [ ] Executei `migracao_consolidar_documentos.py` - SEM ERROS
- [ ] Vi mensagem de sucesso da migração 2

---

## 🚀 FASE 5: REINICIAR (VPS)

- [ ] Executei `docker-compose up -d --build`
- [ ] Container subiu sem erros
- [ ] Executei `docker-compose ps` e vi status "Up"
- [ ] Executei `docker-compose logs` e não vi erros

---

## ✅ FASE 6: VALIDAÇÃO

### No Navegador:
- [ ] Abri o sistema no navegador
- [ ] Fiz login com sucesso
- [ ] Menu "Segmentos" aparece
- [ ] Cliquei em "Segmentos" e vi os segmentos (AGRO, CONSTRUÇÃO, etc.)
- [ ] Cliquei em um segmento e vi as empresas
- [ ] Menu "Empresas" funciona normalmente
- [ ] Cliquei em "Nova Pendência" e campo "Banco" aparece
- [ ] Fui em "Importar Planilha" e dropdown aparece
- [ ] Baixei uma planilha modelo com sucesso
- [ ] Modal do supervisor abre corretamente (se supervisor/adm)

### No Container (Opcional):
- [ ] Entrei no container: `docker exec -it sistema_pendencia-web-1 bash`
- [ ] Executei Python e verifiquei contagens
- [ ] Todas as pendências antigas ainda existem
- [ ] Empresas estão vinculadas aos segmentos

---

## 🎯 RESULTADO FINAL

- [ ] ✅ Sistema funcionando 100%
- [ ] ✅ Nenhum dado foi perdido
- [ ] ✅ Todas as funcionalidades novas funcionam
- [ ] ✅ Backup guardado em local seguro

---

## 📝 ANOTAÇÕES

**Data do deploy:** ___/___/______

**Horário início:** ___:___

**Horário fim:** ___:___

**Problemas encontrados:**


**Observações:**


---

## 🆘 SE DER ERRO

**PARE IMEDIATAMENTE E:**

1. Copie a mensagem de erro completa
2. Execute: `docker-compose logs web > erro.log`
3. Tire print da tela
4. Não execute mais nenhum comando
5. Me envie os logs para análise

**NUNCA:**
- ❌ Delete o banco de dados
- ❌ Execute comandos que você não entende
- ❌ Force push ou reset hard sem backup

---

## 🎉 PARABÉNS!

Se todos os itens acima estão marcados, seu deploy foi um SUCESSO! 🚀

**Sistema atualizado com:**
- ✅ Sistema de Segmentos completo
- ✅ 9 Planilhas modelo individuais
- ✅ Campo Banco sempre visível
- ✅ Modal supervisor ajustado
- ✅ Tipos de documentos consolidados
- ✅ Zero perda de dados

---

**Criado em:** $(date)
**Versão:** 1.0


