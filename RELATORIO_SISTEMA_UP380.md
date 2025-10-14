# 🏢 RELATÓRIO COMPLETO - SISTEMA DE GESTÃO DE PENDÊNCIAS UP380

## 📋 **RESUMO EXECUTIVO**

O **Sistema de Gestão de Pendências UP380** é uma aplicação web desenvolvida em **Flask (Python)** para gerenciar pendências financeiras de múltiplas empresas. O sistema implementa um fluxo de trabalho completo com controle de permissões granular, notificações automáticas, auditoria completa e validação dinâmica por tipo de pendência.

---

## 🏗️ **ARQUITETURA TÉCNICA DETALHADA**

### **Backend (Flask 3.0.2)**
```python
# Tecnologias principais
- Framework: Flask 3.0.2
- ORM: SQLAlchemy 2.0.25
- Banco: SQLite (pendencias.db)
- Email: Flask-Mail com SMTP Gmail
- Notificações: Microsoft Teams via Webhook
- Timezone: America/Sao_Paulo (pytz)
- Validação: Sistema próprio com regras dinâmicas
```

### **Frontend (Bootstrap 5.3.0)**
```html
<!-- Tecnologias principais -->
- CSS Framework: Bootstrap 5.3.0
- Ícones: Bootstrap Icons
- Fonte: Inter (Google Fonts)
- Templates: Jinja2 com filtros customizados
- Design: Responsivo e moderno
- JavaScript: Vanilla JS para interações
```

### **Infraestrutura (Docker)**
```yaml
# Containerização
- Docker + Docker Compose
- Nginx Alpine como proxy reverso
- Deploy: VPS Hostinger
- SSL: Let's Encrypt (configurado)
- Volumes: Dados persistentes
```

---

## 👥 **SISTEMA DE PERMISSÕES GRANULAR**

### **Tipos de Usuário e Permissões**

#### **1. ADMINISTRADOR (`adm`)**
```python
# Permissões totais
- ✅ Acesso completo a todas as funcionalidades
- ✅ Gerenciamento de usuários e empresas
- ✅ Criação, edição e resolução de pendências
- ✅ Importação de planilhas em lote
- ✅ Visualização de logs e relatórios
- ✅ Configuração de permissões personalizadas
- ✅ Acesso a todos os painéis (operador, supervisor, admin)
```

#### **2. SUPERVISOR (`supervisor`)**
```python
# Permissões de aprovação e gestão
- ✅ Aprovação final de pendências
- ✅ Visualização de pendências PENDENTE SUPERVISOR UP
- ✅ Recusa de pendências com motivo obrigatório
- ✅ Gerenciamento de empresas
- ✅ Visualização de logs completos
- ✅ Relatórios de operadores
- ✅ Importação de planilhas
- ✅ Devolução de pendências ao operador
```

#### **3. OPERADOR (`operador`)**
```python
# Permissões de operação
- ✅ Criação de pendências
- ✅ Informação de Natureza de Operação
- ✅ Visualização de pendências PENDENTE OPERADOR UP
- ✅ Recusa de respostas do cliente
- ✅ Importação de planilhas
- ✅ Acesso limitado por empresa
- ✅ Devolução de pendências ao cliente
```

#### **4. CLIENTE (`cliente`)**
```python
# Permissões limitadas
- ✅ Resposta a pendências via link único
- ✅ Visualização de pendências próprias
- ✅ Upload de anexos
- ✅ Complemento de informações
- ❌ Não pode criar pendências
- ❌ Não pode acessar painéis internos
```

### **Sistema de Controle de Acesso**
```python
# Decorador de permissão
@permissao_requerida('supervisor', 'adm', 'operador')

# Funções de validação
def checar_permissao(tipo_usuario, funcionalidade)
def checar_permissao_usuario(usuario_id, tipo_usuario, funcionalidade)
def configurar_permissoes_padrao()

# Tabelas de permissão
- PermissaoUsuarioTipo (padrão por tipo)
- PermissaoUsuarioPersonalizada (individual)
```

---

## 🗄️ **ESTRUTURA COMPLETA DO BANCO DE DADOS**

### **Tabela Principal: Pendencia**
```sql
CREATE TABLE pendencia (
    id INTEGER PRIMARY KEY,
    empresa VARCHAR(50) NOT NULL,                    -- Empresa da pendência
    tipo_pendencia VARCHAR(30) NOT NULL,             -- Tipo específico
    banco VARCHAR(50),                               -- Banco (opcional)
    data DATE,                                       -- Data da pendência
    data_abertura DATETIME NOT NULL,                 -- Data de criação
    fornecedor_cliente VARCHAR(200) NOT NULL,        -- Fornecedor/Cliente
    valor FLOAT NOT NULL,                            -- Valor da pendência
    observacao VARCHAR(300) DEFAULT 'DO QUE SE TRATA?',
    resposta_cliente VARCHAR(300),                   -- Resposta do cliente
    email_cliente VARCHAR(120),                      -- Email do cliente
    status VARCHAR(50) DEFAULT 'PENDENTE CLIENTE',   -- Status atual
    token_acesso VARCHAR(100) UNIQUE,                -- Token único
    data_resposta DATETIME,                          -- Data da resposta
    modificado_por VARCHAR(50),                      -- Último modificador
    nota_fiscal_arquivo VARCHAR(300),                -- Arquivo anexado
    natureza_operacao VARCHAR(500),                  -- Natureza informada
    motivo_recusa VARCHAR(500),                      -- Motivo da recusa
    motivo_recusa_supervisor VARCHAR(500),           -- Motivo recusa supervisor
    codigo_lancamento VARCHAR(64),                   -- Código do lançamento
    data_competencia DATE,                           -- Data competência
    data_baixa DATE,                                 -- Data da baixa
    natureza_sistema VARCHAR(120)                    -- Natureza do sistema
);
```

### **Tabela: Usuario**
```sql
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    senha_hash VARCHAR(200) NOT NULL,
    tipo VARCHAR(20) NOT NULL                        -- 'adm', 'supervisor', 'operador', 'cliente'
);
```

### **Tabela: Empresa**
```sql
CREATE TABLE empresa (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);
```

### **Tabela: LogAlteracao (Auditoria)**
```sql
CREATE TABLE log_alteracao (
    id INTEGER PRIMARY KEY,
    pendencia_id INTEGER NOT NULL,
    usuario VARCHAR(120) NOT NULL,
    tipo_usuario VARCHAR(50) NOT NULL,
    data_hora DATETIME NOT NULL,
    acao VARCHAR(100) NOT NULL,
    campo_alterado VARCHAR(100),
    valor_anterior VARCHAR(300),
    valor_novo VARCHAR(300)
);
```

### **Tabela: Importacao**
```sql
CREATE TABLE importacao (
    id INTEGER PRIMARY KEY,
    nome_arquivo VARCHAR(200) NOT NULL,
    usuario VARCHAR(120) NOT NULL,
    data_hora DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL,
    mensagem_erro TEXT
);
```

### **Tabela de Relacionamento: usuario_empresas**
```sql
-- Relacionamento many-to-many entre usuários e empresas
CREATE TABLE usuario_empresas (
    usuario_id INTEGER,
    empresa_id INTEGER,
    PRIMARY KEY (usuario_id, empresa_id)
);
```

---

## 🔄 **FLUXO DE TRABALHO DETALHADO**

### **Status das Pendências (6 tipos)**
```python
STATUS_PENDENCIAS = [
    'PENDENTE CLIENTE',           # Status inicial - aguardando cliente
    'PENDENTE OPERADOR UP',       # Após resposta do cliente
    'PENDENTE SUPERVISOR UP',     # Após operador informar natureza
    'RESOLVIDA',                  # Status final
    'PENDENTE COMPLEMENTO CLIENTE', # Cliente precisa complementar
    'DEVOLVIDA AO OPERADOR'       # Supervisor recusou e devolveu
]
```

### **Fluxo Completo de Aprovação**
```
1. OPERADOR cria pendência
   ↓
2. Status: PENDENTE CLIENTE
   ↓
3. Sistema envia email ao cliente
   ↓
4. CLIENTE responde via link único
   ↓
5. Status: PENDENTE OPERADOR UP
   ↓
6. OPERADOR informa Natureza de Operação
   ↓
7. Status: PENDENTE SUPERVISOR UP
   ↓
8. SUPERVISOR aprova ou recusa
   ↓
9. Status: RESOLVIDA ou DEVOLVIDA AO OPERADOR
```

### **Fluxos de Recusa**
```python
# Recusa pelo Operador
Operador recusa → Status: PENDENTE CLIENTE → Cliente vê motivo e resposta anterior

# Recusa pelo Supervisor  
Supervisor recusa → Status: DEVOLVIDA AO OPERADOR → Operador vê motivo
```

---

## 🏷️ **SISTEMA DE TIPOS DE PENDÊNCIA (8 tipos)**

### **Validação Dinâmica por Tipo**
```python
TIPO_RULES = {
    "Natureza Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data"],
        "forbidden": ["banco", "data_competencia", "data_baixa"],
        "columns": ["tipo", "fornecedor_cliente", "valor", "codigo_lancamento", "data", "observacao", "status", "modificado_por"]
    },
    "Competência Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data_competencia"],
        "forbidden": ["banco", "data_baixa"],
        "columns": ["tipo", "fornecedor_cliente", "valor", "codigo_lancamento", "data_competencia", "observacao", "status", "modificado_por"]
    },
    "Data da Baixa Errada": {
        "required": ["banco", "data_baixa", "fornecedor_cliente", "valor", "codigo_lancamento"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data_baixa", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao", "status", "modificado_por"]
    },
    "Cartão de Crédito Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]
    },
    "Pagamento Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]
    },
    "Recebimento Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]
    },
    "Nota Fiscal Não Anexada": {
        "required": ["fornecedor_cliente", "valor", "data"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]
    },
    "Nota Fiscal Não Identificada": {
        "required": ["fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]
    }
}
```

### **Funções de Validação**
```python
def validar_por_tipo(payload):
    """Valida campos obrigatórios e proibidos por tipo"""
    
def validar_row_por_tipo(tipo, row):
    """Valida linha da planilha conforme tipo"""
    
def obter_colunas_por_tipo(tipo_pendencia):
    """Retorna colunas específicas por tipo"""
```

---

## 🏢 **EMPRESAS SUPORTADAS (17 empresas)**

```python
EMPRESAS = [
    'ALIANZE', 'AUTOBRAS', 'BRTRUCK', 'CANAÂ', 'COOPERATRUCK', 'ELEVAMAIS',
    'SPEED', 'RAIO', 'EXODO', 'GTA', 'MOVIDAS', 'MASTER', 'PROTEGE ASSOCIAÇÕES',
    'TECH PROTEGE', 'UNIK', 'ARX', 'VALLE'
]
```

### **Integração Automática de Empresas**
```python
def integrar_nova_empresa(empresa):
    """Integra nova empresa automaticamente em todos os filtros"""
    # Adiciona aos filtros do dashboard
    # Disponibiliza para seleção de usuários
    # Notifica via Teams
```

---

## 📊 **FUNCIONALIDADES PRINCIPAIS**

### **Dashboard Inteligente**
```python
# Filtros disponíveis
- Empresa (múltipla seleção)
- Tipo de pendência
- Status
- Data de abertura
- Valor (min/max)
- Busca textual

# Contadores por status
- Pendente Cliente (amarelo)
- Pendente Operador UP (azul)  
- Pendente Supervisor UP (vermelho)
- Resolvida (verde)

# Acesso diferenciado por tipo de usuário
- Admin: Todas as pendências
- Supervisor: Pendências de suas empresas
- Operador: Pendências PENDENTE OPERADOR UP
- Cliente: Apenas suas pendências
```

### **Sistema de Importação Avançado**
```python
# Suporte a formatos
- Excel (.xlsx)
- CSV (via Excel)

# Validação por tipo
- Campos obrigatórios específicos
- Campos proibidos por tipo
- Validação de datas
- Validação de valores

# Funcionalidades
- Preview antes da importação
- Modelos específicos por tipo
- Histórico de importações
- Rollback em caso de erro
```

### **Gestão de Empresas**
```python
# Funcionalidades
- Criação de novas empresas
- Integração automática em filtros
- Relacionamento com usuários
- Notificação Teams para novas empresas
- Gestão de permissões por empresa
```

---

## 📧 **SISTEMA DE NOTIFICAÇÕES**

### **Email (Flask-Mail)**
```python
# Configuração SMTP
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True

# Tipos de notificação
- Nova pendência criada
- Resposta do cliente
- Pendência recusada
- Complemento solicitado
```

### **Microsoft Teams (Webhook)**
```python
# Webhook URL configurado
TEAMS_WEBHOOK_URL = "https://upfinance.webhook.office.com/..."

# Tipos de notificação
def notificar_teams_pendente_operador(pendencia):
def notificar_teams_pendente_supervisor(pendencia):
def notificar_teams_recusa_cliente(pendencia):
def notificar_teams_recusa_supervisor(pendencia):
def notificar_teams_nova_empresa(empresa):

# Formato das mensagens
- MessageCard com cores específicas
- @mentions para usuários relevantes
- Informações detalhadas da pendência
```

---

## 🔍 **SISTEMA DE AUDITORIA COMPLETO**

### **LogAlteracao - Rastreabilidade Total**
```python
# Campos do log
- pendencia_id: ID da pendência
- usuario: Email do usuário
- tipo_usuario: Tipo do usuário
- data_hora: Timestamp da ação
- acao: Tipo da ação realizada
- campo_alterado: Campo modificado
- valor_anterior: Valor antes da alteração
- valor_novo: Valor após alteração

# Tipos de ação registrados
- 'create': Criação de pendência
- 'update': Atualização de campo
- 'Resposta do Cliente': Resposta do cliente
- 'Complemento de Resposta': Complemento
- 'Informação de Natureza': Natureza informada
- 'Resolução de Pendência': Resolução final
- 'Recusa de Resposta': Recusa pelo operador
- 'Recusa de Supervisor': Recusa pelo supervisor
```

### **Funcionalidades de Auditoria**
```python
# Visualização de logs
- Logs por pendência específica
- Logs recentes do sistema
- Filtros por usuário, data, ação

# Exportação
- CSV com todos os logs
- Logs específicos por pendência
- Relatórios personalizados

# Interface
- Visualização amigável
- Histórico cronológico
- Detalhes de cada alteração
```

---

## 🚀 **DEPLOY E INFRAESTRUTURA**

### **Docker Configuration**
```dockerfile
# Dockerfile
FROM python:3.9-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libpq-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p logs
RUN chmod +x start.sh
EXPOSE 5000
CMD ["./start.sh"]
```

### **Docker Compose**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./instance:/app/instance
      - ./logs:/app/logs
      - ./static:/app/static
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/var/www/static
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped
```

### **Scripts de Deploy**
```bash
# start.sh - Inicialização
python migrate_natureza_operacao.py
python migrate_motivo_recusa_supervisor.py
python migrate_data_abertura.py
python migrate_novos_campos_pendencia.py
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# deploy_producao.sh - Deploy automatizado
git pull origin main
docker-compose down
docker-compose up -d --build
```

---

## 🎯 **FUNCIONALIDADES ESPECIAIS**

### **Sistema de Resposta Anterior**
```python
# Funcionalidade para cliente ver resposta anterior
- Busca última resposta nos logs
- Exibe resposta anterior quando recusado
- Botão "Usar como base" para edição
- Histórico completo de respostas
- Preserva contexto da recusa
```

### **Complemento de Resposta**
```python
# Sistema de complemento
- Status: PENDENTE COMPLEMENTO CLIENTE
- Cliente pode complementar resposta anterior
- Mantém histórico completo
- Preserva resposta original
- Log específico para complementos
```

### **Recusa de Supervisor**
```python
# Funcionalidade de recusa do supervisor
- Campo obrigatório para motivo
- Status: DEVOLVIDA AO OPERADOR
- Operador vê motivo da recusa
- Log específico da recusa
- Notificação Teams automática
```

---

## 📁 **ESTRUTURA DE ARQUIVOS**

```
sistema_pendencia/
├── app.py                          # Aplicação principal Flask
├── requirements.txt                # Dependências Python
├── Dockerfile                      # Configuração Docker
├── docker-compose.yml              # Orquestração containers
├── nginx.conf                      # Configuração Nginx
├── start.sh                        # Script de inicialização
├── deploy_producao.sh              # Script de deploy
├── .env                            # Variáveis de ambiente
├── instance/
│   └── pendencias.db              # Banco SQLite
├── static/
│   ├── css/                       # Estilos customizados
│   ├── js/                        # JavaScript
│   ├── notas_fiscais/             # Uploads de anexos
│   └── imagens/                   # Imagens
├── templates/
│   ├── base.html                  # Template base
│   ├── dashboard.html             # Dashboard principal
│   ├── login.html                 # Tela de login
│   ├── nova_pendencia.html        # Formulário nova pendência
│   ├── ver_pendencia.html         # Visualização pendência
│   ├── importar_planilha.html     # Importação
│   ├── operador_pendencias.html   # Painel operador
│   ├── supervisor_pendencias.html # Painel supervisor
│   └── admin/                     # Templates administrativos
├── logs/                          # Logs da aplicação
└── migrations/                    # Scripts de migração
    ├── migrate_natureza_operacao.py
    ├── migrate_motivo_recusa_supervisor.py
    ├── migrate_data_abertura.py
    └── migrate_novos_campos_pendencia.py
```

---

## 🔧 **COMANDOS ÚTEIS PARA MANUTENÇÃO**

### **Deploy Local**
```bash
# Atualizar código
git add .
git commit -m "Descrição da alteração"
git push origin main

# No servidor VPS
git pull origin main
docker-compose down
docker-compose up -d --build
```

### **Backup do Banco**
```bash
# Fazer backup
cp instance/pendencias.db instance/pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Copiar do container
docker cp sistema_pendencia-web-1:/app/instance/pendencias.db ./backup.db
```

### **Logs do Sistema**
```bash
# Ver logs dos containers
docker-compose logs web
docker-compose logs nginx

# Ver logs da aplicação
tail -f logs/app.log
```

### **Migrações de Banco**
```bash
# Executar migrações
python migrate_natureza_operacao.py
python migrate_motivo_recusa_supervisor.py
python migrate_data_abertura.py
python migrate_novos_campos_pendencia.py
```

---

## 🎯 **PROMPTS ÚTEIS PARA OUTRA IA**

### **Para Análise de Código**
```
"Analise o sistema UP380 e me ajude a [funcionalidade específica]. 
O sistema é Flask + SQLAlchemy + Bootstrap com 4 tipos de usuário (adm, supervisor, operador, cliente), 
8 tipos de pendência com validação dinâmica, sistema de aprovação em etapas, 
notificações Teams/Email e auditoria completa."
```

### **Para Debugging**
```
"Estou com erro no sistema UP380: [descrição do erro]. 
O sistema usa Flask, SQLAlchemy, tem 6 status de pendência, 
sistema de permissões granular e validação por tipo de pendência."
```

### **Para Novas Funcionalidades**
```
"Quero implementar [nova funcionalidade] no sistema UP380. 
O sistema já tem: fluxo de aprovação em etapas, validação dinâmica por tipo, 
sistema de logs completo, notificações Teams/Email, importação de planilhas."
```

### **Para Otimização**
```
"Como posso otimizar [aspecto específico] do sistema UP380? 
O sistema processa pendências de 17 empresas, tem validação por 8 tipos, 
auditoria completa e notificações automáticas."
```

---

## ✅ **CHECKLIST DE CONHECIMENTO**

- [x] **Arquitetura:** Flask + SQLAlchemy + Bootstrap + Docker
- [x] **Permissões:** 4 tipos de usuário com controle granular
- [x] **Fluxo:** 6 status de pendência com aprovação em etapas
- [x] **Validação:** 8 tipos de pendência com regras dinâmicas
- [x] **Banco:** 6 tabelas principais com relacionamentos
- [x] **Notificações:** Email + Teams com webhooks
- [x] **Auditoria:** Logs completos de todas as alterações
- [x] **Importação:** Excel com validação por tipo
- [x] **Empresas:** 17 empresas com integração automática
- [x] **Deploy:** Docker + Nginx + VPS Hostinger
- [x] **Funcionalidades:** Resposta anterior, complemento, recusa supervisor
- [x] **Manutenção:** Scripts de migração e backup

---

## 🎉 **SISTEMA PRONTO PARA SUPORTE**

Este relatório fornece conhecimento completo do sistema UP380 para que qualquer IA possa:
- Entender a arquitetura e funcionalidades
- Auxiliar com desenvolvimento e manutenção
- Sugerir melhorias e otimizações
- Resolver problemas específicos
- Implementar novas funcionalidades

**O sistema está 100% documentado e pronto para suporte especializado!** 🚀

