# 📄 MIGRAÇÃO: CONSOLIDAÇÃO DE TIPOS DE DOCUMENTOS
## Sistema UP380

---

## 🎯 O QUE FAZ

Este script migra registros antigos de dois tipos de pendências para um tipo consolidado:

```
ANTES:
  ├─ "NOTA FISCAL NÃO ANEXADA"      (tipo antigo 1)
  └─ "NOTA FISCAL NÃO IDENTIFICADA" (tipo antigo 2)

DEPOIS:
  └─ "DOCUMENTO NÃO ANEXADO"        (tipo consolidado)
```

---

## ❓ QUANDO USAR

### Use este script SE:
- ✅ Você tem pendências antigas com tipos "NOTA FISCAL..."
- ✅ Quer consolidar em um único tipo "DOCUMENTO NÃO ANEXADO"
- ✅ Já atualizou o código (app.py) com o novo tipo

### NÃO use SE:
- ❌ Já executou essa migração antes
- ❌ Não tem registros antigos desses tipos
- ❌ Quer manter os tipos separados

---

## 📋 O QUE SERÁ ALTERADO

### Tabela: `pendencia`
### Campo: `tipo_pendencia`

**Registros afetados:**
```sql
-- Serão atualizados:
WHERE tipo_pendencia = 'NOTA FISCAL NÃO ANEXADA'
WHERE tipo_pendencia = 'NOTA FISCAL NÃO IDENTIFICADA'

-- Para:
SET tipo_pendencia = 'DOCUMENTO NÃO ANEXADO'
```

**IMPORTANTE:** 
- ✅ Preserva TODOS os outros campos (empresa, valor, fornecedor, etc)
- ✅ Apenas muda o tipo da pendência
- ✅ NÃO deleta nada
- ✅ NÃO modifica outros tipos

---

## 🚀 COMO USAR

### 1️⃣ Testar Localmente (Recomendado)

```bash
# Copiar banco de produção para teste
cp instance/pendencias.db instance/pendencias_teste.db

# Editar script (linha 13) para usar banco teste
# DB_PATH = 'instance/pendencias_teste.db'

# Executar teste
python migracao_consolidar_documentos.py

# Se OK, usar em produção
```

### 2️⃣ Executar em Produção

```bash
# Ir para pasta do sistema
cd ~/sistema_pendencia

# Executar migração
python3 migracao_consolidar_documentos.py

# O script vai:
# 1. Criar backup automático
# 2. Analisar tipos existentes
# 3. Migrar registros
# 4. Validar migração
# 5. Gerar relatório
```

---

## 📊 EXEMPLO DE SAÍDA

```
================================================================================
MIGRAÇÃO: CONSOLIDAÇÃO DE TIPOS DE DOCUMENTOS
Sistema UP380
================================================================================

🔒 Criando backup de segurança...
✅ Backup criado: backups/pendencias_backup_docs_20251028_153045.db (15.23 MB)

✅ Conectado ao banco: instance/pendencias.db

📊 Analisando tipos de pendências no banco...

Tipos existentes no banco:
------------------------------------------------------------
  Pagamento Não Identificado              |   145 registros
  Cartão de Crédito Não Identificado      |    89 registros
  NOTA FISCAL NÃO ANEXADA                 |    23 registros → SERÁ MIGRADO
  NOTA FISCAL NÃO IDENTIFICADA            |    12 registros → SERÁ MIGRADO
  Natureza Errada                         |     8 registros
  Recebimento Não Identificado            |     5 registros
------------------------------------------------------------
TOTAL: 6 tipos diferentes

⚠️  Serão migrados 35 registros
   De 2 tipo(s) diferente(s)

🚀 Iniciando migração...

🔄 Iniciando migração de tipos de documentos...

  ✓ NOTA FISCAL NÃO ANEXADA
    → DOCUMENTO NÃO ANEXADO
    Migrados: 23 registros

  ✓ NOTA FISCAL NÃO IDENTIFICADA
    → DOCUMENTO NÃO ANEXADO
    Migrados: 12 registros

🔍 Validando migração...

✅ Tipo consolidado: DOCUMENTO NÃO ANEXADO
   Total de registros: 35

Verificando integridade dos dados migrados:
  ✓ Total de registros: 35
  ✓ Com empresa: 35/35
  ✓ Com valor: 35/35

================================================================================
RELATÓRIO DE MIGRAÇÃO - CONSOLIDAÇÃO DE TIPOS DE DOCUMENTOS
================================================================================

✅ Migração concluída com sucesso!

📊 Estatísticas:
   Total de registros migrados: 35
   Tempo de execução: 0.15 segundos

📋 Detalhes da migração:
   • NOTA FISCAL NÃO ANEXADA
     → DOCUMENTO NÃO ANEXADO
     23 registros

   • NOTA FISCAL NÃO IDENTIFICADA
     → DOCUMENTO NÃO ANEXADO
     12 registros

🎯 Tipo consolidado:
   DOCUMENTO NÃO ANEXADO

================================================================================
💾 Backup salvo em: backups/pendencias_backup_docs_20251028_153045.db
✅ Migração concluída!
```

---

## 🔐 SEGURANÇA

### ✅ Backup Automático:
- Script cria backup antes de qualquer mudança
- Backup fica em: `backups/pendencias_backup_docs_TIMESTAMP.db`
- Pode executar múltiplas vezes (é idempotente)

### ✅ Validação:
- Verifica se tipos antigos ainda existem
- Valida integridade dos dados
- Gera relatório detalhado

### ✅ Rollback:
Se precisar reverter:
```bash
# Restaurar backup
cp backups/pendencias_backup_docs_TIMESTAMP.db instance/pendencias.db

# Reiniciar sistema
docker-compose restart
```

---

## ⚠️ IMPORTANTE

### Antes de executar:

1. **Fazer backup manual** (além do automático)
   ```bash
   cp instance/pendencias.db backups/manual_backup_$(date +%Y%m%d).db
   ```

2. **Verificar se código está atualizado**
   - `app.py` deve ter tipo "DOCUMENTO NÃO ANEXADO"
   - Planilha modelo deve ter nome correto
   - Templates devem usar novo nome

3. **Testar localmente** (recomendado)
   - Use cópia do banco
   - Valide resultado
   - Só depois aplique em produção

### Após executar:

1. **Validar no sistema**
   - Acesse as pendências antigas
   - Verifique se aparecem como "DOCUMENTO NÃO ANEXADO"
   - Teste filtros e buscas

2. **Manter backup por 7 dias**
   - Não delete backup imediatamente
   - Só delete após confirmar que tudo funciona

---

## 🧪 TESTE ANTES DE PRODUÇÃO

### Script de Teste Rápido:

```bash
# 1. Copiar banco
cp instance/pendencias.db instance/pendencias_teste.db

# 2. Verificar tipos antigos
sqlite3 instance/pendencias_teste.db "SELECT tipo_pendencia, COUNT(*) FROM pendencia WHERE tipo_pendencia LIKE '%NOTA FISCAL%' GROUP BY tipo_pendencia;"

# 3. Editar script para usar banco teste
# (mudar DB_PATH na linha 13)

# 4. Executar
python migracao_consolidar_documentos.py

# 5. Verificar resultado
sqlite3 instance/pendencias_teste.db "SELECT tipo_pendencia, COUNT(*) FROM pendencia WHERE tipo_pendencia = 'DOCUMENTO NÃO ANEXADO';"

# 6. Se OK, aplicar em produção com DB_PATH original
```

---

## 📊 VERIFICAÇÕES MANUAIS

### Antes da migração:

```sql
-- Contar registros com tipos antigos
SELECT tipo_pendencia, COUNT(*) as qtd
FROM pendencia
WHERE tipo_pendencia LIKE '%NOTA FISCAL%'
GROUP BY tipo_pendencia;
```

### Após a migração:

```sql
-- Verificar se ainda existem tipos antigos
SELECT COUNT(*) as restantes
FROM pendencia
WHERE tipo_pendencia LIKE '%NOTA FISCAL%';
-- Deve retornar: 0

-- Contar tipo consolidado
SELECT COUNT(*) as total
FROM pendencia
WHERE tipo_pendencia = 'DOCUMENTO NÃO ANEXADO';
```

---

## 🎯 QUANDO EXECUTAR NO DEPLOY

### Ordem de Execução:

```
1. migracao_producao_completa.py      (segmentos, estrutura)
   ↓
2. migracao_consolidar_documentos.py  (tipos de documentos)
   ↓
3. Reiniciar container Docker
```

### Na VPS:

```bash
cd ~/sistema_pendencia
docker-compose down

# Migração 1: Estrutura
python3 migracao_producao_completa.py

# Migração 2: Tipos de documentos
python3 migracao_consolidar_documentos.py

docker-compose build && docker-compose up -d
```

---

## ❓ FAQ

### P: Posso executar múltiplas vezes?
**R:** Sim! Se não houver registros para migrar, apenas informa e sai.

### P: Vai deletar alguma coisa?
**R:** Não! Apenas atualiza o campo `tipo_pendencia`.

### P: E se der erro?
**R:** O script faz rollback automático e mantém o backup.

### P: Quanto tempo demora?
**R:** Segundos. Depende da quantidade de registros.

### P: Precisa parar o sistema?
**R:** Recomendado, mas não obrigatório. SQLite suporta escritas concorrentes limitadas.

---

## ✅ CHECKLIST

Antes de executar em produção:

```
[ ] Código atualizado com tipo "DOCUMENTO NÃO ANEXADO"
[ ] Planilha modelo criada
[ ] Backup manual feito
[ ] Testado localmente (opcional)
[ ] Sistema pode ter downtime de ~1min
[ ] Backup automático será criado
[ ] Sabe restaurar backup se necessário
```

---

## 🎉 RESULTADO ESPERADO

Após executar:

```
✅ Tipos antigos ("NOTA FISCAL...") não existem mais
✅ Todos convertidos para "DOCUMENTO NÃO ANEXADO"
✅ Dados preservados (empresa, valor, etc)
✅ Sistema funciona normalmente
✅ Backup disponível para rollback
```

---

**Arquivo:** `migracao_consolidar_documentos.py`  
**Seguro:** ✅ Sim (com backup automático)  
**Reversível:** ✅ Sim (via backup)  
**Tempo:** ⚡ Segundos  
**Pronto para usar:** 🚀 Sim!


