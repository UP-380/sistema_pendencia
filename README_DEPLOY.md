# 📦 DEPLOY DO SISTEMA UP380 - README
## Versão 2.0 - Implementação de Segmentos e Melhorias

---

## 🎯 O QUE FOI IMPLEMENTADO

### ✅ 1. Sistema de Segmentos
- Nova tabela `segmento` no banco
- Campo `segmento_id` em `empresa`
- Organização hierárquica de empresas
- Templates e rotas para gerenciar segmentos
- 5 segmentos pré-configurados

### ✅ 2. Dashboard com Gráficos
- API endpoint `/api/dados_graficos`
- Chart.js rodando localmente
- Arquivo `static/graficos.js` separado
- CSP ajustado para permitir gráficos
- Filtros por data funcionando

### ✅ 3. Planilhas Modelo Corrigidas
- 9 planilhas com campos corretos
- Campo **banco** em TODAS
- Campo **fornecedor** em TODAS
- Alinhadas com TIPO_RULES do código
- Formatação profissional

### ✅ 4. Melhorias no Sistema
- Validações na exclusão de empresas
- Campo `data_abertura` em pendências
- Modais informativos
- Logs detalhados
- Tratamento de erros melhorado

---

## 📁 ARQUIVOS CRIADOS/MODIFICADOS

### 🔧 Arquivos de Migração e Deploy:
```
✓ migracao_producao_completa.py      → Script de migração principal
✓ testar_migracao_local.py            → Teste local antes de produção
✓ GUIA_DEPLOY_COMPLETO.md             → Guia detalhado passo a passo
✓ COMANDOS_DEPLOY_RAPIDO.md           → Comandos prontos copy/paste
✓ CHECKLIST_DEPLOY_PRODUCAO.md        → Checklist de informações
✓ COMANDOS_PARA_COLETAR_INFO.md       → Comandos para coletar info
✓ README_DEPLOY.md                    → Este arquivo
```

### 📊 Planilhas Modelo (9 arquivos):
```
✓ modelo_natureza_errada.xlsx
✓ modelo_competencia_errada.xlsx
✓ modelo_data_da_baixa_errada.xlsx
✓ modelo_cartao_de_credito_nao_identificado.xlsx
✓ modelo_pagamento_nao_identificado.xlsx
✓ modelo_recebimento_nao_identificado.xlsx
✓ modelo_documento_nao_anexado.xlsx
✓ modelo_lancamento_nao_encontrado_em_extrato.xlsx
✓ modelo_lancamento_nao_encontrado_em_sistema.xlsx
```

### 🐍 Código Python:
```
✓ app.py                               → Rotas, modelos, validações
✓ requirements.txt                     → Dependências (se mudou)
```

### 🎨 Templates:
```
✓ templates/segmentos.html             → Lista de segmentos
✓ templates/empresas_por_segmento.html → Empresas de um segmento
✓ templates/admin/gerenciar_segmentos.html → Admin de segmentos
✓ templates/admin/form_segmento.html   → Formulário segmento
✓ templates/admin/form_empresa.html    → Form empresa (com segmento)
✓ templates/admin/gerenciar_empresas.html → Lista empresas (melhorada)
✓ templates/base.html                  → Menu com link Segmentos
✓ templates/pre_dashboard.html         → Dashboard com gráficos
✓ templates/dashboard.html             → Dashboard melhorado
```

### 🎨 Arquivos Estáticos:
```
✓ static/graficos.js                   → JavaScript dos gráficos
✓ static/chart.min.js                  → Chart.js local
✓ static/up380.css                     → CSS atualizado
```

### 📚 Documentação:
```
✓ PLANILHAS_COMPLETAS_FINAL.md         → Doc das planilhas
✓ Vários outros .md                    → Histórico de implementação
```

---

## 🚀 GUIA RÁPIDO DE DEPLOY

### Opção 1: Siga o Guia Completo
```bash
# Abra e siga passo a passo:
GUIA_DEPLOY_COMPLETO.md
```

### Opção 2: Use Comandos Rápidos
```bash
# Copie e cole os comandos de:
COMANDOS_DEPLOY_RAPIDO.md
```

---

## ⚡ RESUMO SUPER RÁPIDO

### 1️⃣ No Windows:
```powershell
cd "C:\Users\Luiz Marcelo\Desktop\PLANILHA DE PENDENCIAS"
git add .
git commit -m "feat: Sistema UP380 v2.0 - Segmentos e melhorias"
git push origin main
```

### 2️⃣ Na VPS:
```bash
cd ~/sistema_pendencia
cp instance/pendencias.db backups/backup_$(date +%Y%m%d_%H%M%S).db
docker-compose down
git pull origin main
python3 migracao_producao_completa.py
docker-compose build && docker-compose up -d
```

### 3️⃣ Validar:
```
Acesse: http://SEU_DOMINIO
Teste: Login, Dashboard, Segmentos, Importação
```

---

## 🔐 SEGURANÇA

### ✅ Backups Automáticos:
- Script de migração cria backup automático
- Backup manual recomendado antes de tudo
- Mantém backups dos últimos 7 dias

### ✅ Rollback Disponível:
- Código: `git reset --hard HEAD~1`
- Banco: Restaurar de backup
- Container: Rebuild com código anterior

---

## 📊 MIGRAÇÕES DO BANCO

### O que será executado:

1. **Criar tabela `segmento`**
   ```sql
   CREATE TABLE segmento (
       id INTEGER PRIMARY KEY,
       nome TEXT NOT NULL,
       descricao TEXT,
       cor TEXT,
       ...
   )
   ```

2. **Adicionar campo em `empresa`**
   ```sql
   ALTER TABLE empresa ADD COLUMN segmento_id INTEGER
   ```

3. **Popular segmentos**
   - ALIANZE - Contabilidade e Consultoria
   - 7 MARES - Associação Social
   - CEASB - Comércio e Serviços
   - ISBB - Instituto Social
   - STYLLUS - Moda e Varejo

4. **Vincular empresas aos segmentos**
   - Baseado em estrutura pré-definida
   - Mantém dados existentes

5. **Verificar campo `data_abertura`**
   - Adiciona se não existir
   - Preenche com data atual para registros antigos

---

## 🧪 TESTE LOCAL (Recomendado)

### Antes de aplicar em produção:

```bash
# 1. Copiar banco de produção (ou usar banco local)
cp instance/pendencias.db instance/pendencias_teste.db

# 2. Testar migração
python testar_migracao_local.py

# 3. Se OK, aplicar em produção
```

---

## ⏱️ TEMPO ESTIMADO

| Etapa | Tempo |
|-------|-------|
| Commit local | 2 min |
| Backup VPS | 2 min |
| Pull código | 1 min |
| Migração banco | 2-3 min |
| Rebuild Docker | 5-8 min |
| Validação | 3 min |
| **TOTAL** | **15-20 min** |

**Downtime:** ~5-10 minutos

---

## ❓ FAQ - PERGUNTAS FREQUENTES

### P: Vou perder dados?
**R:** Não! O script cria backup automático antes de qualquer mudança.

### P: Posso voltar atrás?
**R:** Sim! Há backup do banco e do código via git.

### P: E se der erro?
**R:** O script detecta e para. Você restaura o backup e nada muda.

### P: Precisa parar o sistema?
**R:** Sim, por ~5-10 minutos para atualizar.

### P: Usuários vão perceber?
**R:** Verão o sistema offline por alguns minutos. Avise se possível.

### P: Posso testar antes?
**R:** Sim! Use `testar_migracao_local.py` com cópia do banco.

---

## 📞 SUPORTE

### Se algo der errado:

1. **Copie mensagem de erro completa**
2. **Execute:** `docker logs NOME_CONTAINER`
3. **Verifique:** `git status` e `git log`
4. **Mantenha:** Backup do banco intacto
5. **Me envie:** Logs e erros para análise

---

## ✅ CHECKLIST PRÉ-DEPLOY

```
[ ] Código local está funcionando
[ ] Planilhas modelo testadas
[ ] Git status limpo (tudo commitado)
[ ] Acesso SSH à VPS confirmado
[ ] Backup do banco de produção feito
[ ] Docker funcionando na VPS
[ ] Tempo de downtime comunicado (se necessário)
[ ] Teste local da migração (opcional mas recomendado)
```

---

## ✅ CHECKLIST PÓS-DEPLOY

```
[ ] Sistema acessível
[ ] Login funciona
[ ] Dashboard carrega
[ ] Gráficos aparecem
[ ] Menu Segmentos visível
[ ] Listar segmentos funciona
[ ] Empresas vinculadas aos segmentos
[ ] Pendências antigas preservadas
[ ] Importação funciona
[ ] Planilhas modelo baixam
[ ] Campos banco e fornecedor aparecem
```

---

## 🎉 RESULTADO ESPERADO

Após o deploy:

```
✅ Sistema UP380 v2.0 em produção
✅ Segmentos organizando empresas
✅ Dashboard com gráficos funcionais
✅ Planilhas modelo corrigidas
✅ Todos os dados preservados
✅ Zero perda de informação
✅ Melhorias ativas
```

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- `GUIA_DEPLOY_COMPLETO.md` - Guia detalhado
- `COMANDOS_DEPLOY_RAPIDO.md` - Comandos prontos
- `migracao_producao_completa.py` - Script comentado
- `PLANILHAS_COMPLETAS_FINAL.md` - Info das planilhas

---

**PRONTO PARA DEPLOY! BOA SORTE! 🚀**

Se tiver dúvidas, consulte os guias ou me avise!


