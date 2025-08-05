# 🏢 Sistema de Gestão de Pendências UP380

## 📋 **VISÃO GERAL DO SISTEMA**

O **Sistema de Gestão de Pendências UP380** é uma aplicação web desenvolvida em **Flask (Python)** para gerenciar pendências financeiras de múltiplas empresas. O sistema implementa um fluxo de trabalho completo com controle de permissões, notificações automáticas e auditoria completa.

---

## 🏗️ **ARQUITETURA E TECNOLOGIAS**

### **Backend:**
- **Framework:** Flask 3.0.2
- **Banco de Dados:** SQLite (com SQLAlchemy ORM)
- **Autenticação:** Sistema próprio com hash de senhas
- **Email:** Flask-Mail com SMTP
- **Notificações:** Microsoft Teams via Webhook

### **Frontend:**
- **Framework CSS:** Bootstrap 5.3.0
- **Ícones:** Bootstrap Icons
- **Fonte:** Inter (Google Fonts)
- **Design:** Responsivo e moderno

### **Infraestrutura:**
- **Containerização:** Docker + Docker Compose
- **Proxy Reverso:** Nginx
- **SSL:** Let's Encrypt
- **Deploy:** VPS Hostinger

---

## 👥 **TIPOS DE USUÁRIOS E PERMISSÕES**

### **1. ADMINISTRADOR (adm)**
**Permissões Totais:**
- ✅ Acesso completo a todas as funcionalidades
- ✅ Gerenciamento de usuários e empresas
- ✅ Criação, edição e resolução de pendências
- ✅ Importação de planilhas
- ✅ Visualização de logs e relatórios
- ✅ Configuração de permissões

### **2. SUPERVISOR (supervisor)**
**Permissões:**
- ✅ Aprovação final de pendências
- ✅ Visualização de pendências PENDENTE SUPERVISOR UP
- ✅ Resolução de pendências
- ✅ Gerenciamento de empresas
- ✅ Visualização de logs
- ✅ Relatórios de operadores

### **3. OPERADOR (operador)**
**Permissões:**
- ✅ Criação de pendências
- ✅ Informação de Natureza de Operação
- ✅ Visualização de pendências PENDENTE OPERADOR UP
- ✅ Recusa de respostas do cliente
- ✅ Importação de planilhas
- ✅ Acesso limitado por empresa

### **4. CLIENTE (cliente)**
**Permissões:**
- ✅ Resposta a pendências via link único
- ✅ Visualização de pendências próprias
- ✅ Upload de anexos
- ✅ Complemento de informações

---

## 🔄 **FLUXO DE TRABALHO COMPLETO**

### **1. Criação de Pendência**
```
Operador/Admin → Nova Pendência → Status: PENDENTE CLIENTE
```

### **2. Notificação ao Cliente**
```
Sistema → Email automático → Link único → Cliente responde
```

### **3. Processamento pelo Operador**
```
Cliente responde → Status: PENDENTE OPERADOR UP → Operador informa Natureza de Operação
```

### **4. Aprovação pelo Supervisor**
```
Operador informa natureza → Status: PENDENTE SUPERVISOR UP → Supervisor aprova
```

### **5. Resolução**
```
Supervisor aprova → Status: RESOLVIDA → Pendência arquivada
```

---

## 📊 **FUNCIONALIDADES PRINCIPAIS**

### **🎯 Gestão de Pendências**
- **Criação:** Formulário completo com upload de anexos
- **Edição:** Modificação de pendências não respondidas
- **Visualização:** Dashboard com filtros avançados
- **Resolução:** Aprovação em etapas (operador → supervisor)
- **Arquivamento:** Pendências resolvidas com histórico

### **📈 Dashboard e Relatórios**
- **Painel Principal:** Visão geral por empresa e tipo
- **Indicadores:** Contadores de pendências por status
- **Filtros:** Empresa, tipo, data, valor, busca textual
- **Gráficos:** Status coloridos e organizados
- **Exportação:** Logs em CSV

### **📧 Comunicação**
- **Email Automático:** Notificação aos clientes
- **Teams Integration:** Webhook para notificações
- **Links Únicos:** Acesso seguro sem login
- **Upload de Anexos:** Suporte a múltiplos formatos

### **📋 Importação e Exportação**
- **Planilhas Excel:** Importação em lote
- **Modelo Padrão:** Template para download
- **Validação:** Verificação de dados obrigatórios
- **Preview:** Visualização antes da importação
- **Histórico:** Registro de todas as importações

### **🔍 Auditoria e Logs**
- **Logs Completos:** Todas as alterações registradas
- **Rastreabilidade:** Quem fez o quê e quando
- **Exportação:** Logs em formato CSV
- **Visualização:** Interface amigável para logs

---

## 🏢 **EMPRESAS SUPORTADAS**

O sistema gerencia pendências para **17 empresas**:
1. **ALIANZE**
2. **AUTOBRAS**
3. **BRTRUCK**
4. **CANAÂ**
5. **COOPERATRUCK**
6. **ELEVAMAIS**
7. **SPEED**
8. **RAIO**
9. **EXODO**
10. **GTA**
11. **MOVIDAS**
12. **MASTER**
13. **PROTEGE ASSOCIAÇÕES**
14. **TECH PROTEGE**
15. **UNIK**
16. **ARX**
17. **VALLE**

---

## 🏷️ **TIPOS DE PENDÊNCIA**

### **Categorias Principais:**
1. **Cartão de Crédito Não Identificado**
2. **Pagamento Não Identificado**
3. **Recebimento Não Identificado**
4. **Nota Fiscal Não Anexada**

---

## 🗄️ **ESTRUTURA DO BANCO DE DADOS**

### **Tabelas Principais:**

#### **Pendencia**
```sql
- id (Primary Key)
- empresa (String)
- tipo_pendencia (String)
- banco (String)
- data (Date)
- fornecedor_cliente (String)
- valor (Float)
- observacao (String)
- resposta_cliente (String)
- email_cliente (String)
- status (String)
- token_acesso (String, Unique)
- data_resposta (DateTime)
- modificado_por (String)
- nota_fiscal_arquivo (String)
- natureza_operacao (String)
- motivo_recusa (String)
- motivo_recusa_supervisor (String)
```

#### **Usuario**
```sql
- id (Primary Key)
- email (String, Unique)
- senha_hash (String)
- tipo (String: 'adm', 'supervisor', 'operador', 'cliente')
```

#### **Empresa**
```sql
- id (Primary Key)
- nome (String)
```

#### **LogAlteracao**
```sql
- id (Primary Key)
- pendencia_id (Foreign Key)
- usuario (String)
- tipo_usuario (String)
- data_hora (DateTime)
- acao (String)
- campo_alterado (String)
- valor_anterior (String)
- valor_novo (String)
```

#### **Importacao**
```sql
- id (Primary Key)
- nome_arquivo (String)
- usuario (String)
- data_hora (DateTime)
- status (String)
- mensagem_erro (String)
```

---

## 🔒 **SISTEMA DE SEGURANÇA**

### **Autenticação:**
- **Hash de Senhas:** Werkzeug Security
- **Sessões Protegidas:** SECRET_KEY
- **Tokens Únicos:** Para acesso de clientes
- **Controle de Acesso:** Decorators de permissão

### **Proteção de Dados:**
- **Validação de Entrada:** Sanitização de dados
- **SQL Injection:** Prevenção via SQLAlchemy
- **XSS Protection:** Headers de segurança
- **CSRF Protection:** Tokens de formulário

### **Infraestrutura:**
- **HTTPS:** SSL/TLS obrigatório
- **Rate Limiting:** Proteção contra ataques
- **Headers de Segurança:** Configurados no Nginx
- **Isolamento:** Containers Docker

---

## 🎨 **INTERFACE E USABILIDADE**

### **Design System:**
- **Paleta UP380:** Azul (#1B365D), Verde (#008c6a)
- **Tipografia:** Inter (Google Fonts)
- **Responsividade:** Mobile-first design
- **Acessibilidade:** ARIA labels e navegação por teclado

### **Componentes:**
- **Navbar Moderna:** Logo interativo e navegação clara
- **Cards Informativos:** Status coloridos e organizados
- **Tabelas Responsivas:** Scroll horizontal em mobile
- **Formulários Intuitivos:** Validação em tempo real
- **Notificações:** Toast messages e alerts

### **Funcionalidades UX:**
- **Filtros Sticky:** Permanecem visíveis durante scroll
- **Busca Avançada:** Múltiplos campos de busca
- **Ajuste de Fonte:** Controles de acessibilidade
- **Loading States:** Feedback visual de ações
- **Confirmações:** Modais para ações críticas

---

## 📱 **RESPONSIVIDADE**

### **Breakpoints:**
- **Desktop:** > 768px
- **Tablet:** 768px - 480px
- **Mobile:** < 480px

### **Adaptações Mobile:**
- **Tabelas:** Stack vertical em mobile
- **Formulários:** Campos empilhados
- **Botões:** Tamanho otimizado para touch
- **Navegação:** Menu hambúrguer

---

## 🚀 **INSTALAÇÃO E CONFIGURAÇÃO**

### **Requisitos**
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Docker e Docker Compose (para deploy)

### **Instalação Local**

1. **Clone este repositório:**
```bash
git clone https://github.com/UP-380/sistema_pendencia.git
cd sistema_pendencia
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
Crie um arquivo `.env` na raiz do projeto:
```bash
SECRET_KEY=sua_chave_secreta_aqui
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=seu_email@gmail.com
TEAMS_WEBHOOK_URL=sua_url_webhook
```

5. **Execute a aplicação:**
```bash
python app.py
```

6. **Acesse o sistema:**
```
http://localhost:5000
```

### **Deploy em Produção (VPS)**

1. **Execute o script de deploy:**
```bash
chmod +x deploy.sh
./deploy.sh
```

2. **Configure SSL (opcional):**
```bash
chmod +x setup_ssl.sh
./setup_ssl.sh
```

3. **Acesse via Docker:**
```bash
docker-compose up -d
```

---

## 📧 **CONFIGURAÇÃO DE EMAIL**

Para usar as funcionalidades de email, você precisa:

1. **Ativar autenticação de 2 fatores no Gmail**
2. **Gerar uma senha de app:**
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Mail" e "Outro (nome personalizado)"
   - Use essa senha no campo `MAIL_PASSWORD`

---

## 🔧 **CONFIGURAÇÃO E DEPLOY**

### **Variáveis de Ambiente (.env):**
```bash
SECRET_KEY=sua_chave_secreta
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=seu_email@gmail.com
TEAMS_WEBHOOK_URL=sua_url_webhook
```

### **Dependências (requirements.txt):**
- Flask 3.0.2
- Flask-SQLAlchemy 3.0.5
- Flask-Mail 0.9.1
- pandas
- openpyxl
- python-dotenv
- pytz
- gunicorn
- requests

### **Deploy Docker:**
```bash
docker-compose up -d
```

---

## 📊 **MÉTRICAS E MONITORAMENTO**

### **Logs de Sistema:**
- **Acesso:** Nginx access logs
- **Erros:** Nginx error logs
- **Aplicação:** Flask logs
- **Docker:** Container logs

### **Métricas de Uso:**
- **Pendências por Status:** Contadores em tempo real
- **Tempo de Resolução:** Média por operador
- **Taxa de Resolução:** Percentual de sucesso
- **Atividade por Usuário:** Logs de auditoria

---

## 🔄 **INTEGRAÇÕES EXTERNAS**

### **Microsoft Teams:**
- **Webhook URL:** Configurável via variável de ambiente
- **Notificações Automáticas:**
  - Nova pendência criada
  - Cliente respondeu
  - Pendência aguardando operador
  - Pendência aguardando supervisor
  - Resposta recusada
  - Nova empresa cadastrada

### **Email (Gmail):**
- **SMTP:** Configuração automática
- **Templates:** Mensagens personalizadas
- **Anexos:** Suporte a arquivos
- **Tracking:** Confirmação de envio

---

## 📁 **ESTRUTURA DE ARQUIVOS**

```
PLANILHA DE PENDENCIAS/
├── app.py                          # Aplicação principal Flask
├── requirements.txt                # Dependências Python
├── Dockerfile                      # Configuração Docker
├── docker-compose.yml              # Orquestração containers
├── nginx.conf                      # Configuração Nginx
├── deploy.sh                       # Script de deploy
├── setup_ssl.sh                    # Configuração SSL
├── migrate_*.py                    # Scripts de migração
├── .env                            # Variáveis de ambiente
├── instance/
│   └── pendencias.db              # Banco SQLite
├── static/
│   ├── up380.css                  # Estilos customizados
│   ├── logoUP.png                 # Logo da empresa
│   └── notas_fiscais/             # Uploads de anexos
├── templates/
│   ├── base.html                  # Template base
│   ├── dashboard.html             # Painel principal
│   ├── pre_dashboard.html         # Painel de empresas
│   ├── operador_pendencias.html   # Dashboard operador
│   ├── supervisor_pendencias.html # Dashboard supervisor
│   ├── admin/                     # Templates administrativos
│   └── [outros templates...]
└── [documentação...]
```

---

## 🚀 **FUNCIONALIDADES AVANÇADAS**

### **Sistema de Permissões Granular:**
- **Permissões por Tipo:** Configuráveis por categoria de usuário
- **Permissões Personalizadas:** Override individual por usuário
- **Controle de Empresas:** Acesso limitado por empresa
- **Funcionalidades Categorizadas:** Gestão, Importação, Relatórios

### **Fluxo de Aprovação em Etapas:**
- **Validação Automática:** Verificação de dados obrigatórios
- **Notificações Inteligentes:** Baseadas no status da pendência
- **Logs Detalhados:** Rastreabilidade completa do fluxo
- **Rollback:** Possibilidade de devolver pendências

### **Importação Inteligente:**
- **Preview:** Visualização antes da importação
- **Validação:** Verificação de dados obrigatórios
- **Tratamento de Erros:** Mensagens específicas por problema
- **Histórico:** Registro de todas as importações

---

## 📈 **RELATÓRIOS E ANALYTICS**

### **Dashboard Executivo:**
- **Pendências por Empresa:** Contadores em tempo real
- **Status Distribution:** Gráficos por status
- **Performance por Operador:** Métricas de produtividade
- **Tempo Médio de Resolução:** Análise de eficiência

### **Relatórios Detalhados:**
- **Pendências Resolvidas:** Histórico completo
- **Logs de Auditoria:** Rastreabilidade total
- **Importações:** Estatísticas de upload
- **Atividade por Usuário:** Relatórios de uso

---

## 🛠️ **USO DO SISTEMA**

### **1. Registrando uma Pendência:**
- Acesse o painel principal
- Clique em "Nova Pendência"
- Preencha o formulário com os dados da pendência
- O sistema enviará automaticamente um e-mail para o cliente

### **2. Respondendo uma Pendência:**
- O cliente recebe um e-mail com um link único
- Ao clicar no link, ele acessa a página da pendência
- Pode responder diretamente pelo formulário
- O operador será notificado da resposta

### **3. Gerenciando Pendências:**
- No painel principal, visualize todas as pendências
- Use filtros por empresa, tipo e status
- Marque pendências como resolvidas quando necessário
- Acompanhe o status de cada pendência

### **4. Importação em Lote:**
- Acesse "Importar Planilha"
- Faça upload do arquivo Excel
- Visualize o preview dos dados
- Confirme a importação

---

## 🔍 **TROUBLESHOOTING**

### **Se a aplicação não subir:**
```bash
# Ver logs detalhados
docker-compose logs web

# Verificar se as portas estão livres
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000
```

### **Se o email não funcionar:**
- Verifique se a senha de app está correta
- Teste com um email simples primeiro
- Verifique os logs: `docker-compose logs web`

### **Se o SSL não funcionar:**
1. Verifique se o DNS está propagado: `nslookup seu-dominio.com`
2. Verifique se a porta 80 está aberta: `netstat -tlnp | grep :80`
3. Verifique logs do Nginx: `docker-compose logs nginx`

---

## 📞 **SUPORTE**

Para suporte ou dúvidas:
1. Verifique os logs: `docker-compose logs web`
2. Confirme se todas as variáveis de ambiente estão configuradas
3. Teste a conectividade: `curl http://localhost:5000/health`
4. Entre em contato com a equipe de desenvolvimento UP380

---

## 🎯 **ROADMAP E MELHORIAS FUTURAS**

### **Funcionalidades Planejadas:**
- **API REST:** Integração com sistemas externos
- **Notificações Push:** Alertas em tempo real
- **Dashboard Mobile:** App nativo
- **Integração ERP:** Conexão com sistemas contábeis
- **Machine Learning:** Classificação automática de pendências

### **Melhorias Técnicas:**
- **Cache Redis:** Performance otimizada
- **PostgreSQL:** Banco de dados mais robusto
- **Microserviços:** Arquitetura escalável
- **CI/CD:** Deploy automatizado

---

## ✅ **CONCLUSÃO**

O **Sistema de Gestão de Pendências UP380** é uma solução completa e robusta para gerenciamento de pendências financeiras. Com arquitetura moderna, segurança avançada, interface intuitiva e funcionalidades abrangentes, o sistema atende às necessidades de empresas de diversos portes.

### **Pontos Fortes:**
- ✅ **Arquitetura Escalável:** Docker + Nginx
- ✅ **Segurança Robusta:** HTTPS, autenticação, auditoria
- ✅ **Interface Moderna:** Responsiva e acessível
- ✅ **Funcionalidades Completas:** Fluxo end-to-end
- ✅ **Integrações:** Teams, Email, Importação
- ✅ **Documentação:** Completa e atualizada

### **Status do Sistema:**
🚀 **PRODUÇÃO ESTÁVEL** - Sistema em operação na VPS Hostinger com domínio up380.com.br

---

## 📄 **LICENÇA**

Este projeto é desenvolvido e mantido pela **UP380**.

---

**Desenvolvido por UP380 - Sistema de Gestão de Pendências Financeiras** 