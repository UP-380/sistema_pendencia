# 🚀 Guia de Implementação - Atualizações Sistema UP380 (2025)

Este guia descreve como implementar todas as atualizações feitas no sistema de pendências UP380.

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter:

1. **Backup completo do banco de dados atual**
   ```bash
   python backup_database.py
   ```

2. **Python 3.8+** instalado
3. **Git** para controle de versão

---

## 🔧 Passo 1: Instalar Novas Dependências

Execute no terminal:

```bash
pip install -r requirements.txt
```

As novas dependências incluem:
- `Flask-WTF` (proteção CSRF)
- `Flask-Limiter` (rate limiting)
- `Flask-Talisman` (headers de segurança)

---

## 🗄️ Passo 2: Inicializar/Atualizar Banco de Dados

### Opção A: Sistema Novo (Primeira Instalação)

```bash
python init_db.py
```

Este script irá:
- Criar todas as tabelas necessárias
- Criar usuários padrão (admin e cliente)
- Migrar empresas existentes
- Configurar permissões RBAC
- Opcionalmente criar segmentos básicos

### Opção B: Sistema Existente (Atualização)

Execute os scripts de migração na ordem:

```bash
# 1. Adicionar estrutura de segmentos
python migrate_adicionar_segmentos.py

# 2. Migrar tipos de pendência antigos
python migrate_nota_fiscal_para_documento.py

# 3. Configurar permissões do novo perfil cliente_supervisor
python migrate_cliente_supervisor.py
```

---

## ✅ Passo 3: Verificar Implementação

### 3.1 Testar Funcionalidades Principais

1. **Login no Sistema**
   - Email: `adm.pendencia@up380.com.br`
   - Senha: `Finance.@2`

2. **Verificar Navegação Hierárquica**
   - Acesse `/` → deve redirecionar para `/segmentos` (se houver segmentos)
   - Clique em um segmento → lista empresas do segmento
   - Clique em uma empresa → lista pendências

3. **Testar Formatação de Moeda**
   - Criar nova pendência → campo Valor deve formatar automaticamente como R$ 1.234,56
   - Editar pendência → valor deve aparecer formatado

4. **Testar Novos Tipos de Pendência**
   - Criar pendência com tipo "Documento Não Anexado"
   - Criar pendência com tipo "Lançamento Não Encontrado em Extrato"
   - Criar pendência com tipo "Lançamento Não Encontrado em Sistema"

5. **Testar Modal de Suporte**
   - Clicar em "Suporte" no menu → modal deve abrir com formulário ClickUp
   - Verificar que o log foi registrado em `/logs_recentes`

6. **Testar Perfil Cliente Supervisor**
   - Criar usuário do tipo "Cliente Supervisor"
   - Login com este usuário
   - Verificar acesso a:
     - ✅ Dashboards (pendentes, resolvidas)
     - ✅ Relatórios (mensal, operadores)
     - ✅ Exportação de logs
     - ✅ Download de anexos
     - ✅ Edição de observações
   - Verificar que NÃO tem acesso a:
     - ❌ Criar/editar pendências
     - ❌ Importar planilhas
     - ❌ Aprovar/recusar pendências
     - ❌ Gerenciar usuários/empresas

### 3.2 Testar Segurança

1. **CSRF Protection**
   - Tente fazer POST sem token CSRF → deve retornar erro 400

2. **Rate Limiting**
   - Faça múltiplas requisições rápidas → deve ser limitado após exceder limites

3. **Headers de Segurança**
   - Inspecione headers HTTP → deve incluir CSP, HSTS, X-Frame-Options, etc.

---

## 🎨 Passo 4: Personalização (Opcional)

### Configurar Segmentos Específicos

Edite o arquivo `migrate_adicionar_segmentos.py` e ajuste a lista:

```python
segmentos_exemplo = [
    'Seu Segmento 1',
    'Seu Segmento 2',
    'Seu Segmento 3'
]
```

### Associar Empresas aos Segmentos

Via interface administrativa:
1. Acesse `/gerenciar_empresas`
2. Edite cada empresa
3. Selecione o segmento apropriado

Ou via script SQL direto:
```python
from app import app, db, Empresa, Segmento

with app.app_context():
    # Exemplo: associar empresa ALIANZE ao segmento Financeiro
    empresa = Empresa.query.filter_by(nome='ALIANZE').first()
    segmento = Segmento.query.filter_by(nome='Financeiro').first()
    empresa.segmento_id = segmento.id
    db.session.commit()
```

### Ajustar URL do ClickUp

Edite `app.py` e atualize a variável `iframe_clickup` com sua URL:

```python
iframe_clickup = """
<iframe class="clickup-embed clickup-dynamic-height"
        src="https://forms.clickup.com/SEU_FORM_ID_AQUI"
        width="100%" height="100%"
        style="background: transparent; border: 1px solid #ccc;"></iframe>
<script async src="https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"></script>
"""
```

---

## 🔐 Passo 5: Configuração de Produção

### Ativar HTTPS e Segurança em Produção

No arquivo `.env` ou variáveis de ambiente:

```bash
# Ativar HTTPS
SESSION_COOKIE_SECURE=True

# Configurar Flask-Talisman
FLASK_ENV=production
```

No arquivo `app.py`, altere:

```python
# Linha ~62
talisman = Talisman(
    app,
    force_https=True,  # Alterar para True em produção
    strict_transport_security=True,
    content_security_policy=csp,
    content_security_policy_nonce_in=['script-src']
)
```

### Configurar Rate Limiting

Por padrão, os limites são:
- 200 requisições por dia por IP
- 50 requisições por hora por IP

Para ajustar, edite `app.py` (~44):

```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],  # Ajuste aqui
    storage_uri="memory://"
)
```

Para produção, considere usar Redis:
```python
storage_uri="redis://localhost:6379"
```

---

## 📊 Passo 6: Validação Final

Execute o checklist completo:

- [ ] Banco de dados atualizado com novas estruturas
- [ ] Migração de tipos de pendência concluída (sem registros "Nota Fiscal *")
- [ ] Permissões do `cliente_supervisor` configuradas
- [ ] Navegação hierárquica funcionando (Segmentos → Empresas → Pendências)
- [ ] Formatação de moeda BRL nos formulários
- [ ] Modal de suporte ClickUp abrindo e registrando logs
- [ ] Novos tipos de pendência disponíveis na importação
- [ ] CSRF ativo (formulários com token)
- [ ] Rate limiting ativo (limites respeitados)
- [ ] Headers de segurança presentes (CSP, HSTS, etc.)
- [ ] Uploads validados (extensões, tamanho)
- [ ] Backup configurado e testado

---

## 🐛 Troubleshooting

### Erro: "Tabela segmento não encontrada"

Execute:
```bash
python migrate_adicionar_segmentos.py
```

### Erro: "CSRF token missing"

Certifique-se de que todos os formulários POST incluem:
```html
<form method="POST">
    {{ csrf_token() }}  <!-- Adicionar esta linha -->
    <!-- resto do formulário -->
</form>
```

### Erro de importação: "parse_currency_to_float não reconhecido"

Reinicie o servidor Flask:
```bash
# Ctrl+C para parar
python app.py  # ou gunicorn/uwsgi conforme configuração
```

### Modal do ClickUp não abre

1. Verifique a URL do iframe em `app.py`
2. Verifique CSP no navegador (F12 → Console)
3. Adicione `forms.clickup.com` ao `frame-src` se necessário

### Permissões do cliente_supervisor não funcionam

Execute novamente:
```bash
python migrate_cliente_supervisor.py
```

Depois, force logout/login do usuário.

---

## 📚 Documentação Adicional

- `RELATORIO_COMPLETO_SISTEMA_UP380_2025.md` - Relatório completo das mudanças
- `DEPLOY_PRODUCAO.md` - Guia de deploy em produção
- `README_SISTEMA.md` - Documentação geral do sistema

---

## 🆘 Suporte

Para dúvidas ou problemas:

1. Consulte os logs do sistema: `/logs_recentes`
2. Verifique logs do servidor (console)
3. Abra um chamado via modal de suporte no sistema

---

## 📝 Notas Importantes

1. **Sempre faça backup antes de migrar** em produção
2. **Teste em staging** antes de aplicar em produção
3. **Documente qualquer personalização** feita no código
4. **Mantenha o `.env` seguro** e fora do controle de versão
5. **Use HTTPS em produção** para segurança das sessões

---

**Data de Criação**: Outubro/2025  
**Versão do Sistema**: 3.0  
**Compatibilidade**: Python 3.8+, Flask 3.0+, SQLite 3


