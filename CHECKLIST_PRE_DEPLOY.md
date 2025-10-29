# ✅ Checklist Pré-Deploy - Atualizações Sistema UP380

Use este checklist para garantir que todas as atualizações foram implementadas e testadas corretamente antes do deploy em produção.

---

## 📦 1. Instalação de Dependências

### Verificar Dependências Instaladas

```bash
# Verificar Flask e extensões
python -m pip list | findstr Flask

# Deve mostrar (versões mínimas):
# Flask>=3.0.2 ou Flask>=2.3.3 (compatível)
# Flask-SQLAlchemy>=3.1.1 ou >=3.0.5
# Flask-Mail>=0.9.1
# Flask-WTF>=1.2.1 ou >=1.1.1
```

### Instalar Novas Dependências

```bash
pip install Flask-Limiter>=3.5.0
pip install Flask-Talisman>=1.1.0

# Ou simplesmente:
pip install -r requirements.txt
```

### ✅ Checklist
- [ ] Flask-WTF instalado
- [ ] Flask-Limiter instalado
- [ ] Flask-Talisman instalado
- [ ] Todas as dependências do requirements.txt instaladas

---

## 🗄️ 2. Banco de Dados

### Em Desenvolvimento (Sistema Novo)

```bash
python init_db.py
```

### Em Produção (Atualização)

```bash
# 1. BACKUP OBRIGATÓRIO
python backup_database.py

# 2. Verificar backup
ls -lh *.db  # Linux/Mac
dir *.db     # Windows

# 3. Executar migrações em ordem
python migrate_adicionar_segmentos.py
python migrate_nota_fiscal_para_documento.py
python migrate_cliente_supervisor.py
```

### ✅ Checklist
- [ ] Backup do banco de dados realizado
- [ ] Tabela `segmento` criada
- [ ] Coluna `segmento_id` adicionada à tabela `empresa`
- [ ] Tipos de pendência migrados (sem "Nota Fiscal *")
- [ ] Permissões `cliente_supervisor` configuradas
- [ ] Nenhum erro durante as migrações

---

## 🔒 3. Segurança

### Verificar Configurações

#### CSRF Protection

No código:
```python
# app.py (linha ~43)
csrf = CSRFProtect(app)
```

Teste:
```bash
# Tentar POST sem token → deve retornar 400
curl -X POST http://localhost:5000/nova
```

#### Rate Limiting

No código:
```python
# app.py (linha ~44)
limiter = Limiter(...)
```

Teste:
```bash
# Fazer múltiplas requisições rápidas
for i in {1..60}; do curl http://localhost:5000/; done
```

#### Headers de Segurança

No código:
```python
# app.py (linha ~62)
talisman = Talisman(...)
```

Teste:
```bash
# Verificar headers
curl -I http://localhost:5000/
# Deve incluir: Content-Security-Policy, Strict-Transport-Security
```

### ✅ Checklist
- [ ] CSRF Protection ativo
- [ ] Rate Limiting configurado
- [ ] Talisman configurado com CSP
- [ ] Headers de segurança presentes
- [ ] Configurações de sessão segura (HttpOnly, SameSite)
- [ ] Validação de uploads ativa (16MB, extensões permitidas)

### Configurações de Produção

Arquivo `.env`:
```bash
SESSION_COOKIE_SECURE=True
FLASK_ENV=production
SECRET_KEY=<gerar_nova_chave_segura>
```

Arquivo `app.py` (linha ~62):
```python
talisman = Talisman(
    app,
    force_https=True,  # ← ALTERAR PARA TRUE
    ...
)
```

### ✅ Checklist Produção
- [ ] `SESSION_COOKIE_SECURE=True` no .env
- [ ] `force_https=True` no Talisman
- [ ] SECRET_KEY única e segura gerada
- [ ] HTTPS configurado no servidor

---

## 🎨 4. Frontend

### Verificar Templates Criados

```bash
# Verificar existência
ls templates/segmentos.html
ls templates/empresas_por_segmento.html
```

### Testar Formatação de Moeda

1. Acesse `/nova`
2. Digite valor no campo "Valor"
3. Deve formatar automaticamente como "R$ 0,00"

### Testar Modal de Suporte

1. Clique em "Suporte" no menu
2. Modal deve abrir com iframe do ClickUp
3. Verificar log em `/logs_recentes`

### ✅ Checklist
- [ ] Template `segmentos.html` existe
- [ ] Template `empresas_por_segmento.html` existe
- [ ] Formatação de moeda funciona em `/nova`
- [ ] Formatação de moeda funciona em `/editar/<id>`
- [ ] Modal de suporte abre corretamente
- [ ] Log de suporte registrado

---

## 🧪 5. Testes Funcionais

### Navegação Hierárquica

1. Acesse `/` → deve redirecionar
2. Acesse `/segmentos` → lista segmentos (se houver)
3. Clique em um segmento → lista empresas
4. Clique em uma empresa → mostra pendências

### Tipos de Pendência

1. Criar pendência tipo "Documento Não Anexado"
2. Criar pendência tipo "Lançamento Não Encontrado em Extrato"
3. Criar pendência tipo "Lançamento Não Encontrado em Sistema"
4. Importar planilha com novos tipos

### Perfil Cliente Supervisor

1. Criar usuário tipo "Cliente Supervisor"
2. Login com este usuário
3. Testar permissões:

**DEVE CONSEGUIR:**
- Ver dashboards (pendentes, resolvidas)
- Ver relatórios (mensal, operadores)
- Baixar anexos
- Exportar logs
- Editar observações

**NÃO DEVE CONSEGUIR:**
- Criar pendências
- Editar pendências
- Importar planilhas
- Aprovar/recusar
- Gerenciar usuários/empresas

### ✅ Checklist
- [ ] Navegação hierárquica funciona
- [ ] Novos tipos de pendência disponíveis
- [ ] Perfil cliente_supervisor com permissões corretas
- [ ] Parse de moeda funciona na importação
- [ ] Tipos antigos não aparecem mais nos selects

---

## 📊 6. Validação de Dados

### Verificar Migração de Tipos

```python
from app import app, db, Pendencia

with app.app_context():
    # Não deve ter tipos antigos
    antigos = Pendencia.query.filter(
        Pendencia.tipo_pendencia.in_([
            'Nota Fiscal Não Anexada',
            'Nota Fiscal Não Identificada'
        ])
    ).count()
    
    print(f"Tipos antigos remanescentes: {antigos}")  # Deve ser 0
    
    # Deve ter novos tipos
    novos = Pendencia.query.filter(
        Pendencia.tipo_pendencia == 'Documento Não Anexado'
    ).count()
    
    print(f"Novos tipos migrados: {novos}")
```

### Verificar Segmentos

```python
from app import app, db, Segmento

with app.app_context():
    segmentos = Segmento.query.all()
    for seg in segmentos:
        print(f"{seg.nome}: {len(seg.empresas)} empresas")
```

### ✅ Checklist
- [ ] Nenhuma pendência com tipos antigos
- [ ] Pendências migradas para "Documento Não Anexado"
- [ ] Segmentos criados (se aplicável)
- [ ] Empresas associadas aos segmentos (se aplicável)

---

## 🚀 7. Performance e Logs

### Testar Rate Limiting

```bash
# Fazer 60 requisições em sequência
for i in {1..60}; do curl -s http://localhost:5000/ > /dev/null; echo $i; done
```

Deve limitar após ~50 requisições/hora.

### Verificar Logs

```python
from app import app, db, LogAlteracao

with app.app_context():
    # Log de suporte
    logs_suporte = LogAlteracao.query.filter_by(
        acao='open_support_modal'
    ).count()
    
    print(f"Logs de suporte: {logs_suporte}")
```

### ✅ Checklist
- [ ] Rate limiting funcionando
- [ ] Logs sendo gerados corretamente
- [ ] Log de suporte registrado
- [ ] Performance aceitável (< 500ms para listagens)

---

## 📝 8. Documentação

### Verificar Arquivos

```bash
ls -1 *.md
# Deve listar:
# - IMPLEMENTACAO_ATUALIZACOES_2025.md
# - RESUMO_IMPLEMENTACAO.md
# - CHECKLIST_PRE_DEPLOY.md
# - RELATORIO_COMPLETO_SISTEMA_UP380_2025.md
```

### Verificar Scripts

```bash
ls -1 migrate*.py init_db.py
# Deve listar:
# - init_db.py
# - migrate_adicionar_segmentos.py
# - migrate_cliente_supervisor.py
# - migrate_nota_fiscal_para_documento.py
# - migrar_nota_fiscal_automatico.py
```

### ✅ Checklist
- [ ] Todos os arquivos de documentação presentes
- [ ] Todos os scripts de migração presentes
- [ ] README atualizado (se aplicável)

---

## 🎯 9. Checklist Final Pré-Deploy

### Antes do Deploy

- [ ] Backup completo realizado e testado
- [ ] Todas as dependências instaladas
- [ ] Migrações testadas em staging
- [ ] Testes funcionais passando
- [ ] Segurança configurada
- [ ] Documentação completa
- [ ] Plano de rollback preparado

### Durante o Deploy

- [ ] Agendar janela de manutenção
- [ ] Notificar usuários
- [ ] Executar migrações em ordem
- [ ] Ativar configurações de produção
- [ ] Reiniciar aplicação
- [ ] Verificar logs de inicialização

### Após o Deploy

- [ ] Testar login
- [ ] Testar navegação básica
- [ ] Testar criação de pendência
- [ ] Verificar formatação de moeda
- [ ] Testar perfil cliente_supervisor
- [ ] Monitorar logs por 1 hora
- [ ] Verificar métricas de performance

---

## 🆘 10. Rollback (Se Necessário)

### Em caso de problema crítico:

```bash
# 1. Parar aplicação
# Ctrl+C ou systemctl stop app

# 2. Restaurar backup
mv pendencias.db pendencias.db.NEW
cp pendencias.db.backup pendencias.db

# 3. Reverter código (se necessário)
git reset --hard HEAD~1

# 4. Reinstalar dependências antigas
pip install -r requirements.txt.old

# 5. Reiniciar aplicação
python app.py
```

### ✅ Checklist Rollback
- [ ] Backup restaurado
- [ ] Código revertido
- [ ] Aplicação funcionando
- [ ] Usuários notificados
- [ ] Problema documentado para análise

---

## 📞 Contatos de Suporte

- **Desenvolvedor**: [Preencher]
- **Admin Sistema**: adm.pendencia@up380.com.br
- **Suporte Técnico**: Via modal no sistema

---

**Data**: ___/___/2025  
**Responsável**: ____________________  
**Status**: [ ] Aprovado para Deploy  [ ] Necessita Correções


