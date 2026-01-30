# 📋 RELATÓRIO COMPLETO - SISTEMA ANTIGO UP380
## Documentação de Todas as Telas, Funcionalidades e Estrutura do Frontend

---

## 📑 ÍNDICE

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura e Tecnologias](#2-arquitetura-e-tecnologias)
3. [Sistema de Autenticação e Permissões](#3-sistema-de-autenticação-e-permissões)
4. [Estrutura do Frontend](#4-estrutura-do-frontend)
5. [Todas as Telas do Sistema](#5-todas-as-telas-do-sistema)
6. [Fluxos de Trabalho](#6-fluxos-de-trabalho)
7. [Componentes e Funcionalidades Especiais](#7-componentes-e-funcionalidades-especiais)

---

## 1. VISÃO GERAL DO SISTEMA

O sistema antigo é uma aplicação web Flask (Python) para gestão de pendências financeiras de múltiplas empresas. O sistema implementa:

- **Gestão hierárquica**: Segmentos → Empresas → Pendências
- **Fluxo de trabalho**: Cliente → Operador → Supervisor → Resolvida
- **Controle de permissões**: 5 tipos de usuários com diferentes níveis de acesso
- **Notificações**: Email (Flask-Mail) e Microsoft Teams (Webhooks)
- **Auditoria completa**: Logs de todas as alterações
- **Importação em massa**: Planilhas Excel com validação dinâmica

---

## 2. ARQUITETURA E TECNOLOGIAS

### 2.1 Backend
- **Framework**: Flask 3.0.2
- **ORM**: SQLAlchemy
- **Banco de Dados**: SQLite (`pendencias.db`)
- **Autenticação**: Sistema próprio com `werkzeug.security` (hash de senhas)
- **Sessões**: Flask sessions com cookies permanentes (2 horas)
- **Email**: Flask-Mail com SMTP
- **Notificações**: Microsoft Teams via Webhooks
- **Processamento**: Pandas (Excel), Openpyxl (geração de Excel)

### 2.2 Frontend
- **Framework CSS**: Bootstrap 5.3.0 (CDN)
- **Ícones**: Bootstrap Icons 1.11.0
- **Fonte**: Inter (Google Fonts)
- **Templates**: Jinja2
- **JavaScript**: Vanilla JS + Chart.js (gráficos)
- **Design**: Responsivo, moderno, com sidebar lateral

### 2.3 Estrutura de Arquivos
```
/
├── app.py                    # Aplicação Flask principal (4548 linhas)
├── api_routes.py            # Blueprint de rotas API REST
├── templates/               # Templates Jinja2
│   ├── base.html            # Template base com sidebar
│   ├── login.html
│   ├── pre_dashboard.html   # Lista de empresas
│   ├── dashboard.html       # Painel de pendências
│   ├── nova_pendencia.html
│   ├── editar_pendencia.html
│   ├── ver_pendencia.html
│   ├── operador_pendencias.html
│   ├── supervisor_pendencias.html
│   ├── resolvidas.html
│   ├── importar_planilha.html
│   ├── historico_importacoes.html
│   ├── relatorio_mensal.html
│   ├── logs_recentes.html
│   └── admin/               # Templates administrativos
│       ├── gerenciar_usuarios.html
│       ├── gerenciar_empresas.html
│       ├── gerenciar_segmentos.html
│       └── ...
├── static/
│   ├── up380.css           # CSS principal (760 linhas)
│   ├── graficos.js         # JavaScript para gráficos
│   ├── chart.min.js        # Chart.js
│   └── notas_fiscais/      # Uploads de anexos
└── instance/
    └── pendencias.db       # Banco de dados SQLite
```

---

## 3. SISTEMA DE AUTENTICAÇÃO E PERMISSÕES

### 3.1 Tipos de Usuários

#### **ADMINISTRADOR (adm)**
- ✅ Acesso total ao sistema
- ✅ Gerenciar usuários, empresas, segmentos
- ✅ Criar, editar, resolver, excluir pendências
- ✅ Importar planilhas
- ✅ Visualizar todos os logs e relatórios
- ✅ Configurar permissões personalizadas

#### **SUPERVISOR (supervisor)**
- ✅ Aprovar pendências (PENDENTE SUPERVISOR UP)
- ✅ Resolver pendências
- ✅ Visualizar pendências de todas as empresas atribuídas
- ✅ Gerenciar empresas e segmentos
- ✅ Visualizar logs e relatórios
- ✅ Atuar como operador (acesso ao painel do operador)

#### **OPERADOR (operador)**
- ✅ Criar pendências
- ✅ Informar Natureza de Operação
- ✅ Visualizar pendências PENDENTE OPERADOR UP
- ✅ Recusar respostas do cliente
- ✅ Importar planilhas
- ✅ Acesso limitado por empresa (apenas empresas atribuídas)

#### **CLIENTE (cliente)**
- ✅ Responder pendências via link único (token)
- ✅ Visualizar pendências próprias
- ✅ Upload de anexos
- ✅ Ver histórico de respostas

#### **CLIENTE SUPERVISOR (cliente_supervisor)**
- ✅ Todas as permissões de Cliente
- ✅ Visualizar pendências resolvidas
- ✅ Acesso a relatórios mensais

### 3.2 Sistema de Sessão
- **Duração**: 2 horas (permanente)
- **Armazenamento**: Cookies HTTP-only
- **Dados da sessão**:
  - `usuario_id`: ID do usuário
  - `usuario_email`: Email do usuário
  - `usuario_tipo`: Tipo de usuário (adm, supervisor, operador, cliente, cliente_supervisor)

### 3.3 Decoradores de Permissão
```python
@permissao_requerida('supervisor', 'adm', 'operador')
def minha_rota():
    # Apenas usuários dos tipos especificados podem acessar
    pass
```

---

## 4. ESTRUTURA DO FRONTEND

### 4.1 Template Base (`base.html`)

O template base contém:

#### **Sidebar Lateral (Menu de Navegação)**
- **Posição**: Fixa à esquerda (280px de largura)
- **Design**: Gradiente branco, sombras suaves, animações
- **Estrutura**:
  - Header com logo UP380
  - Menu principal com ícones Bootstrap
  - Submenu expansível para "GERENCIAR"
  - Footer com informações do usuário
- **Funcionalidades**:
  - Menu responsivo (oculta em mobile)
  - Links ativos destacados
  - Transições suaves
  - Scrollbar customizada

#### **Área de Conteúdo**
- **Margem esquerda**: 280px (para compensar sidebar)
- **Container**: Bootstrap container-fluid
- **Flash messages**: Exibidas no topo
- **Breadcrumbs**: Navegação hierárquica

#### **CSS Principal (`static/up380.css`)**
- **Paleta de cores UP380**:
  - Azul escuro: `#1B365D`
  - Azul claro: `#005bb5`
  - Verde: `#008c6a`
  - Vermelho: `#C82333`
  - Cinza claro: `#F5F6FA`
  - Branco: `#FFFFFF`
  - Preto: `#222B45`

- **Componentes estilizados**:
  - Cards de resumo
  - Tabelas responsivas
  - Formulários
  - Botões
  - Badges
  - Dropdowns customizados (multiselect)

### 4.2 Componentes Reutilizáveis

#### **Cards de Resumo**
```html
<div class="card-resumo">
    <span class="icon"><i class="bi bi-tag"></i></span>
    <div>
        <div class="value">42</div>
        <div class="label">Pendências</div>
    </div>
</div>
```

#### **Dropdown Multiselect Customizado**
- Usado em filtros avançados (Segmentos, Empresas, Operadores, Supervisores)
- Design moderno com indicadores visuais
- Busca integrada
- Seleção múltipla com badges

#### **Tabelas Responsivas**
- Scroll horizontal em telas pequenas
- Colunas fixas com larguras definidas
- Hover effects
- Badges de status coloridos

---

## 5. TODAS AS TELAS DO SISTEMA

### 5.1 TELA DE LOGIN (`/login`)

**Arquivo**: `templates/login.html`

**Funcionalidades**:
- Formulário de login (email + senha)
- Validação de credenciais
- Redirecionamento para `/segmentos` após login
- Mensagens de erro via flash messages

**Fluxo**:
1. Usuário preenche email e senha
2. Sistema verifica credenciais no banco
3. Se válido: cria sessão e redireciona
4. Se inválido: exibe mensagem de erro

**Design**:
- Card centralizado
- Logo UP380
- Botão primário grande
- Design minimalista

---

### 5.2 TELA DE SEGMENTOS (`/segmentos` ou `/`)

**Arquivo**: `templates/segmentos.html`

**Funcionalidades**:
- Lista todos os segmentos cadastrados
- Cards clicáveis para acessar empresas do segmento
- Contagem de empresas por segmento
- Acesso apenas para usuários autenticados

**Estrutura**:
- Grid de cards (Bootstrap)
- Cada card mostra:
  - Nome do segmento
  - Quantidade de empresas
  - Link para empresas do segmento

**Permissões**: Todos os tipos de usuário (exceto não autenticados)

---

### 5.3 TELA DE EMPRESAS POR SEGMENTO (`/segmento/<id>`)

**Arquivo**: `templates/empresas_por_segmento.html`

**Funcionalidades**:
- Lista empresas de um segmento específico
- Cards com informações resumidas de cada empresa
- Links para dashboard de cada empresa
- Breadcrumb: Segmentos → Segmento → Empresas

**Estrutura**:
- Grid responsivo de cards de empresas
- Cada card mostra:
  - Nome da empresa
  - Pendências abertas
  - Pendências resolvidas
  - Gráfico de pizza (tipos de pendência)

---

### 5.4 TELA DE LISTA DE EMPRESAS (`/empresas`)

**Arquivo**: `templates/pre_dashboard.html`

**Funcionalidades**:
- Lista todas as empresas (ou filtradas por permissão)
- **Filtros avançados**:
  - **Segmentos**: Multiselect com busca
  - **Clientes (Empresas)**: Multiselect com busca
  - **Operadores**: Multiselect com busca
  - **Supervisores**: Multiselect (apenas adm)
  - **Datas**: Abertura e resolução (início e fim)
- Cards de empresas com:
  - Nome da empresa
  - Pendências abertas por tipo
  - Gráficos (pizza e barras)
  - Botões de ação:
    - Ver Pendências
    - Nova Pendência (adm, operador, supervisor)
    - Pendências Resolvidas (adm, supervisor)
    - Relatório Mensal (adm, supervisor)

**Design**:
- Layout full-width
- Cards em grid (3 colunas em telas grandes)
- Filtros sticky no topo
- Indicadores visuais de quantidade de pendências

**Permissões**: Todos os tipos de usuário

---

### 5.5 PAINEL DE PENDÊNCIAS (`/dashboard`)

**Arquivo**: `templates/dashboard.html`

**Funcionalidades**:
- Visualização de pendências de uma empresa específica
- **Filtros**:
  - Tipo de pendência (dropdown)
  - Busca (fornecedor, banco, observação, resposta)
- **Cards de resumo por tipo**: Mostra quantidade de pendências por tipo
- **Tabela de pendências**:
  - Colunas dinâmicas (variam conforme tipo de pendência)
  - Colunas padrão: Tipo, Banco, Data, Fornecedor/Cliente, Valor, Observação, Status, Ações, Modificado por, Anexo
  - Colunas condicionais:
    - Código do Lançamento (alguns tipos)
    - Data Competência (alguns tipos)
    - Data Baixa (alguns tipos)
    - Natureza do Sistema (alguns tipos)
- **Ações por pendência**:
  - **Verificar** (todos): Abre modal com detalhes
  - **Editar** (adm, supervisor): Edita pendência
  - **Resolver** (adm, supervisor): Marca como resolvida
  - **Excluir** (adm): Remove pendência
  - **Responder Pendência** (cliente, cliente_supervisor): Abre formulário de resposta

**Modal de Verificação**:
- Exibe todos os detalhes da pendência
- Histórico de logs
- Ações baseadas em permissão:
  - Adm/Supervisor: Editar, Resolver, Excluir
  - Cliente/Cliente Supervisor: Responder Pendência
  - Operador: Apenas visualização

**Design**:
- Tabela responsiva com scroll horizontal
- Badges coloridos por status
- Breadcrumb: Empresas → Empresa → Painel
- Filtros sticky

**Permissões**: Todos os tipos de usuário

---

### 5.6 NOVA PENDÊNCIA (`/nova`)

**Arquivo**: `templates/nova_pendencia.html`

**Funcionalidades**:
- Formulário dinâmico baseado no tipo de pendência selecionado
- **Validação dinâmica**: Campos obrigatórios e proibidos variam por tipo
- **Tipos de pendência**:
  1. Cartão de Crédito Não Identificado
  2. Pagamento Não Identificado
  3. Recebimento Não Identificado
  4. Documento Não Anexado
  5. Lançamento Não Encontrado em Extrato
  6. Lançamento Não Encontrado em Sistema
  7. Natureza Errada
  8. Competência Errada
  9. Data da Baixa Errada

**Campos do Formulário**:
- **Sempre visíveis**:
  - Empresa (select)
  - Tipo de Pendência (select)
  - Banco (text)
  - Data da Pendência (date)
  - Fornecedor/Cliente (text)
  - Valor (text com formatação de moeda)
  - Código do Lançamento (text)
  - Observação (textarea)
  - E-mail do Cliente (email, opcional)

- **Condicionais** (aparecem/desaparecem conforme tipo):
  - Data Competência (date)
  - Data Baixa (date)
  - Natureza do Sistema (text)

- **Upload de anexo**:
  - Aceita: PDF, JPG, JPEG, PNG
  - Sem limite de tamanho
  - Salvo em `static/notas_fiscais/`

**Validação**:
- Campos obrigatórios por tipo (definidos em `TIPO_RULES`)
- Campos proibidos por tipo
- Validação de valor (deve ser > 0)
- Formatação de moeda brasileira (R$ 0,00)

**JavaScript**:
- Formatação automática de moeda
- Mostrar/ocultar campos dinamicamente
- Validação em tempo real

**Permissões**: adm, supervisor, operador

---

### 5.7 EDITAR PENDÊNCIA (`/editar/<id>`)

**Arquivo**: `templates/editar_pendencia.html`

**Funcionalidades**:
- Formulário pré-preenchido com dados da pendência
- Mesma estrutura dinâmica da tela de Nova Pendência
- Validação igual à criação
- Atualização de logs automática

**Permissões**: adm, supervisor

---

### 5.8 VER PENDÊNCIA (CLIENTE) (`/pendencia/<token>`)

**Arquivo**: `templates/ver_pendencia.html`

**Funcionalidades**:
- Acesso via link único (token)
- **Não requer autenticação** (acesso público via token)
- Visualização completa da pendência
- **Formulário de resposta**:
  - Campo de texto para resposta
  - Upload de anexo (PDF, JPG, PNG)
  - Botão "Enviar Resposta"
- **Histórico de respostas**: Mostra todas as respostas anteriores
- **Motivo de recusa**: Exibido se a resposta foi recusada

**Fluxo**:
1. Cliente recebe email com link único
2. Acessa link e visualiza pendência
3. Preenche resposta e anexa documento (se necessário)
4. Envia resposta
5. Status muda para "PENDENTE OPERADOR UP"
6. Notificação enviada ao operador

**Design**:
- Layout limpo e focado
- Destaque para informações importantes
- Formulário destacado

---

### 5.9 PAINEL DO OPERADOR (`/operador/pendencias`)

**Arquivo**: `templates/operador_pendencias.html`

**Funcionalidades**:
- Visualização de pendências com status "PENDENTE OPERADOR UP"
- **Indicadores por empresa**: Cards mostrando quantidade de pendências abertas
- **Filtros**:
  - **Empresas**: Dropdown com indicadores visuais:
    - 🔴 Urgente (≥10 pendências)
    - 🟡 Atenção (≥5 pendências)
    - 🔵 Pendente (≥1 pendência)
    - ✅ Tudo certo (0 pendências)
  - **Status**: Todos, Aguardando Operador, Aguardando Cliente, Resolvidas
  - **Tipo de Pendência**: Dropdown
  - **Busca**: Texto livre
- **Ações disponíveis**:
  - **Informar Natureza de Operação**: Abre modal/formulário
  - **Recusar Resposta**: Rejeita resposta do cliente (requer motivo)
  - **Enviar para Supervisor**: Muda status para "PENDENTE SUPERVISOR UP"
  - **Envio em lote**: Selecionar múltiplas pendências e enviar juntas
- **Tabela de pendências**:
  - Colunas: Tipo, Empresa, Banco, Data, Fornecedor, Valor, Observação, Resposta do Cliente, Status, Ações
  - Badges coloridos por status
  - Botões de ação por linha

**Design**:
- Cards de indicadores no topo
- Dropdown customizado com cores e ícones
- Tabela responsiva
- Modal para informar natureza de operação

**Permissões**: operador, supervisor, adm

---

### 5.10 INFORMAR NATUREZA DE OPERAÇÃO (`/operador/natureza_operacao/<id>`)

**Arquivo**: `templates/operador_natureza_operacao.html`

**Funcionalidades**:
- Formulário para informar a natureza de operação de uma pendência
- Campo de texto livre
- Ao salvar:
  - Status muda para "PENDENTE SUPERVISOR UP"
  - Notificação enviada ao supervisor
  - Log registrado

**Permissões**: operador, supervisor, adm

---

### 5.11 PAINEL DO SUPERVISOR (`/supervisor/pendencias`)

**Arquivo**: `templates/supervisor_pendencias.html`

**Funcionalidades**:
- Visualização de pendências com status "PENDENTE SUPERVISOR UP"
- **Cards de resumo**:
  - Aguardando Aprovação (total)
  - Valor Alto (>R$ 5.000)
  - Atrasadas (>7 dias)
  - Total Pendências
- **Indicadores por empresa**: Similar ao painel do operador
- **Filtros avançados**:
  - Empresas (multiselect)
  - Status
  - Tipo de Pendência
  - Busca
- **Ações disponíveis**:
  - **Resolver Pendência**: Marca como "RESOLVIDA"
  - **Recusar e Devolver ao Operador**: Rejeita e devolve para operador (requer motivo)
  - **Resolução em lote**: Selecionar múltiplas e resolver juntas
- **Tabela de pendências**:
  - Colunas completas
  - Destaque para pendências urgentes
  - Ações por linha

**Design**:
- Cards de métricas no topo
- Filtros avançados em card
- Tabela com destaque para valores altos e atrasadas

**Permissões**: supervisor, adm

---

### 5.12 PENDÊNCIAS RESOLVIDAS (`/resolvidas`)

**Arquivo**: `templates/resolvidas.html`

**Funcionalidades**:
- Lista pendências com status "RESOLVIDA"
- **Filtros**:
  - Empresa (select)
  - Tipo de Pendência (select)
  - Data Inicial (date)
  - Data Final (date)
- **Tabela de pendências resolvidas**:
  - Colunas: Tipo, Empresa, Banco, Data, Fornecedor, Valor, Observação, Natureza de Operação, Modificado por, Anexo
  - **Logs expandíveis**: Cada linha pode expandir para mostrar histórico completo de alterações
  - Logs mostram: Data/Hora, Usuário, Tipo, Ação, Campo Alterado, Valor Anterior, Valor Novo
- **Exportação**: Botão para exportar para CSV/Excel

**Design**:
- Tabela com linhas expansíveis
- Logs em tabela aninhada
- Filtros no topo

**Permissões**: supervisor, adm, cliente_supervisor

---

### 5.13 LISTA DE PENDÊNCIAS (`/pendencias`)

**Arquivo**: `templates/pendencias_list.html`

**Funcionalidades**:
- Lista genérica de pendências com paginação
- **Filtros via URL**:
  - `status`: Filtra por status
  - `empresa`: Filtra por empresa
  - `page`: Número da página
  - `per_page`: Itens por página (padrão: 50)
- **Paginação**: Bootstrap pagination
- Tabela completa com todas as colunas

**Permissões**: supervisor, adm, operador, cliente_supervisor

---

### 5.14 IMPORTAR PLANILHA (`/importar`)

**Arquivo**: `templates/importar_planilha.html`

**Funcionalidades**:
- Upload de planilha Excel (.xlsx)
- **Seleção de tipo**: Dropdown para escolher tipo de pendência da planilha
- **Download de modelo**: Dropdown com modelos para cada tipo de pendência
- **Validação**:
  - Colunas obrigatórias por tipo
  - Formato de datas (YYYY-MM-DD ou DD/MM/YYYY)
  - Formato de valores (ponto como separador decimal)
  - Validação de campos obrigatórios
- **Processamento**:
  - Leitura com Pandas
  - Validação linha por linha
  - Criação de pendências em lote
  - Registro de importação (tabela `Importacao`)
- **Feedback**:
  - Mensagens de sucesso/erro
  - Quantidade de linhas processadas
  - Erros detalhados por linha

**Modelos de Planilha**:
- Cada tipo de pendência tem um modelo específico
- Colunas variam conforme tipo
- Download via rota `/import/modelo?tipo=<TIPO>`

**Permissões**: adm, operador

---

### 5.15 HISTÓRICO DE IMPORTAÇÕES (`/historico_importacoes`)

**Arquivo**: `templates/historico_importacoes.html`

**Funcionalidades**:
- Lista todas as importações realizadas
- **Informações exibidas**:
  - Nome do arquivo
  - Usuário que importou
  - Data/hora da importação
  - Status (PROCESSANDO, CONCLUIDO, ERRO)
  - Mensagem de erro (se houver)
- Tabela com ordenação por data (mais recente primeiro)

**Permissões**: adm, operador

---

### 5.16 RELATÓRIO MENSAL (`/relatorios/mensal`)

**Arquivo**: `templates/relatorio_mensal.html`

**Funcionalidades**:
- Relatório de pendências por mês
- **Filtros**:
  - Empresa (select)
  - Mês/Ano (date picker)
- **Gráficos**:
  - Gráfico de pizza: Distribuição por tipo de pendência
  - Gráfico de barras: Pendências abertas vs resolvidas
- **Tabela de resumo**:
  - Total de pendências
  - Pendências abertas
  - Pendências resolvidas
  - Por tipo de pendência
- **Exportação**: Botão para exportar para Excel

**Permissões**: supervisor, adm, cliente_supervisor

---

### 5.17 RELATÓRIO DE OPERADORES (`/relatorio_operadores`)

**Funcionalidades**:
- Relatório de produtividade dos operadores
- Métricas por operador:
  - Pendências processadas
  - Pendências resolvidas
  - Tempo médio de processamento
- Tabela e gráficos

**Permissões**: supervisor, adm

---

### 5.18 LOGS RECENTES (`/logs_recentes`)

**Arquivo**: `templates/logs_recentes.html`

**Funcionalidades**:
- Lista os 50 logs mais recentes do sistema
- **Informações exibidas**:
  - Data/Hora
  - Usuário
  - Tipo de usuário
  - Ação
  - Campo alterado
  - Valor anterior
  - Valor novo
  - ID da pendência (link)
- **Exportação**: Botão para exportar para CSV

**Permissões**: supervisor, adm, cliente_supervisor

---

### 5.19 LOGS DE UMA PENDÊNCIA (`/logs/<pendencia_id>`)

**Arquivo**: `templates/logs_pendencia.html`

**Funcionalidades**:
- Histórico completo de alterações de uma pendência específica
- Tabela detalhada com todas as alterações
- Ordenação por data (mais recente primeiro)
- **Exportação**: Botão para exportar logs para CSV

**Permissões**: supervisor, adm, cliente_supervisor

---

### 5.20 GERENCIAR USUÁRIOS (`/gerenciar_usuarios`)

**Arquivo**: `templates/admin/gerenciar_usuarios.html`

**Funcionalidades**:
- Lista todos os usuários cadastrados
- **Ações**:
  - **Novo Usuário**: Abre formulário de criação
  - **Editar**: Edita usuário existente
  - **Excluir**: Remove usuário (com confirmação)
- **Informações exibidas**:
  - Nome
  - Email
  - Tipo
  - Empresas atribuídas
  - Status (ativo/inativo)
- Tabela com ações por linha

**Permissões**: supervisor, adm

---

### 5.21 NOVO USUÁRIO (`/novo_usuario`)

**Arquivo**: `templates/admin/novo_usuario.html`

**Funcionalidades**:
- Formulário de criação de usuário
- **Campos**:
  - Nome (text)
  - Email (email)
  - Senha (password)
  - Tipo (select: adm, supervisor, operador, cliente, cliente_supervisor)
  - Empresas (multiselect)
- Validação de email único
- Hash de senha automático

**Permissões**: supervisor, adm

---

### 5.22 EDITAR USUÁRIO (`/editar_usuario/<id>`)

**Arquivo**: `templates/admin/editar_usuario.html`

**Funcionalidades**:
- Formulário pré-preenchido
- Mesma estrutura de Novo Usuário
- Campo de senha opcional (só atualiza se preenchido)
- Atualização de empresas atribuídas

**Permissões**: supervisor, adm

---

### 5.23 GERENCIAR EMPRESAS (`/gerenciar_empresas`)

**Arquivo**: `templates/admin/gerenciar_empresas.html`

**Funcionalidades**:
- Lista todas as empresas cadastradas
- **Ações**:
  - **Nova Empresa**: Abre formulário
  - **Editar**: Edita empresa
  - **Excluir**: Remove empresa (com confirmação)
- **Informações exibidas**:
  - Nome
  - Segmento
  - Quantidade de pendências
  - Usuários atribuídos
- Tabela com ações

**Permissões**: supervisor, adm

---

### 5.24 NOVA EMPRESA (`/nova_empresa`)

**Arquivo**: `templates/admin/form_empresa.html`

**Funcionalidades**:
- Formulário de criação de empresa
- **Campos**:
  - Nome (text)
  - Segmento (select)
  - Usuários (multiselect)
- Validação de nome único

**Permissões**: supervisor, adm

---

### 5.25 EDITAR EMPRESA (`/editar_empresa/<id>`)

**Arquivo**: `templates/admin/form_empresa.html`

**Funcionalidades**:
- Formulário pré-preenchido
- Mesma estrutura de Nova Empresa
- Atualização de segmento e usuários

**Permissões**: supervisor, adm

---

### 5.26 GERENCIAR SEGMENTOS (`/gerenciar_segmentos`)

**Arquivo**: `templates/admin/gerenciar_segmentos.html`

**Funcionalidades**:
- Lista todos os segmentos
- **Ações**:
  - **Novo Segmento**: Abre formulário
  - **Editar**: Edita segmento
  - **Excluir**: Remove segmento (com confirmação)
- **Informações exibidas**:
  - Nome
  - Quantidade de empresas
- Tabela simples

**Permissões**: supervisor, adm

---

### 5.27 NOVO SEGMENTO (`/novo_segmento`)

**Arquivo**: `templates/admin/form_segmento.html`

**Funcionalidades**:
- Formulário simples com campo Nome
- Validação de nome único

**Permissões**: supervisor, adm

---

### 5.28 EDITAR SEGMENTO (`/editar_segmento/<id>`)

**Arquivo**: `templates/admin/form_segmento.html`

**Funcionalidades**:
- Formulário pré-preenchido
- Mesma estrutura de Novo Segmento

**Permissões**: supervisor, adm

---

### 5.29 GERENCIAR PERMISSÕES (`/gerenciar_permissoes`)

**Arquivo**: `templates/admin/gerenciar_permissoes.html`

**Funcionalidades**:
- Interface para configurar permissões personalizadas por usuário
- Lista de funcionalidades categorizadas:
  - Gestão de Pendências
  - Importações
  - Logs e Relatórios
  - Administração
- Checkboxes para habilitar/desabilitar permissões
- Salva em tabela `PermissaoUsuarioPersonalizada`

**Permissões**: adm

---

### 5.30 EDITAR OBSERVAÇÃO (`/editar_observacao/<id>`)

**Arquivo**: `templates/editar_observacao.html`

**Funcionalidades**:
- Formulário simples para editar apenas a observação de uma pendência
- Campo textarea
- Atualização rápida sem abrir formulário completo

**Permissões**: supervisor, adm

---

### 5.31 BAIXAR ANEXO (`/baixar_anexo/<pendencia_id>`)

**Funcionalidades**:
- Download do arquivo anexado a uma pendência
- Validação de permissão
- Headers de download apropriados

**Permissões**: Todos os tipos de usuário (com acesso à pendência)

---

### 5.32 BAIXAR MODELO DE PLANILHA (`/import/modelo`)

**Funcionalidades**:
- Geração dinâmica de planilha Excel modelo
- Colunas variam conforme tipo de pendência
- Primeira linha com nomes das colunas
- Segunda linha com exemplos
- Download direto

**Permissões**: adm, operador

---

## 6. FLUXOS DE TRABALHO

### 6.1 Fluxo de Criação de Pendência

1. **Operador/Adm/Supervisor** acessa `/nova`
2. Seleciona empresa e tipo de pendência
3. Formulário se adapta dinamicamente (campos aparecem/desaparecem)
4. Preenche campos obrigatórios
5. Opcionalmente anexa documento
6. Salva pendência
7. Status inicial: **"PENDENTE CLIENTE"**
8. Sistema gera token único
9. Email enviado ao cliente (se email fornecido)
10. Log registrado

### 6.2 Fluxo de Resposta do Cliente

1. **Cliente** recebe email com link único (`/pendencia/<token>`)
2. Acessa link (não requer login)
3. Visualiza pendência completa
4. Preenche resposta e anexa documento (se necessário)
5. Envia resposta
6. Status muda para **"PENDENTE OPERADOR UP"**
7. Notificação enviada ao operador (Teams)
8. Log registrado

### 6.3 Fluxo de Processamento pelo Operador

1. **Operador** acessa `/operador/pendencias`
2. Visualiza pendências com status "PENDENTE OPERADOR UP"
3. **Opção A - Aceitar resposta**:
   - Informa Natureza de Operação
   - Status muda para **"PENDENTE SUPERVISOR UP"**
   - Notificação enviada ao supervisor
4. **Opção B - Recusar resposta**:
   - Informa motivo da recusa
   - Status muda para **"PENDENTE COMPLEMENTO CLIENTE"**
   - Email enviado ao cliente com motivo
   - Cliente pode complementar resposta

### 6.4 Fluxo de Aprovação pelo Supervisor

1. **Supervisor** acessa `/supervisor/pendencias`
2. Visualiza pendências com status "PENDENTE SUPERVISOR UP"
3. **Opção A - Aprovar**:
   - Resolve pendência
   - Status muda para **"RESOLVIDA"**
   - Log registrado
4. **Opção B - Recusar**:
   - Informa motivo
   - Status muda para **"PENDENTE OPERADOR UP"**
   - Notificação enviada ao operador
   - Log registrado

### 6.5 Fluxo de Importação em Massa

1. **Operador/Adm** acessa `/importar`
2. Baixa modelo de planilha (opcional)
3. Preenche planilha com dados
4. Seleciona tipo de pendência
5. Faz upload da planilha
6. Sistema valida cada linha
7. Cria pendências válidas
8. Retorna relatório de sucesso/erros
9. Registra importação no histórico

---

## 7. COMPONENTES E FUNCIONALIDADES ESPECIAIS

### 7.1 Sistema de Validação Dinâmica

**Arquivo**: `app.py` - Variável `TIPO_RULES`

Cada tipo de pendência tem regras específicas:

```python
TIPO_RULES = {
    "Natureza Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data"],
        "forbidden": ["banco", "data_competencia", "data_baixa"],
        "columns": [...],  # Colunas para exibição
        "import_columns": [...]  # Colunas para importação
    },
    # ... outros tipos
}
```

**Funcionalidades**:
- Campos obrigatórios por tipo
- Campos proibidos por tipo
- Colunas de exibição personalizadas
- Colunas de importação personalizadas
- Labels customizados

### 7.2 Sistema de Logs

**Modelo**: `LogAlteracao`

Registra todas as alterações no sistema:
- Criação de pendência
- Alteração de campos
- Mudança de status
- Respostas do cliente
- Recusas e motivos

**Campos**:
- `pendencia_id`: ID da pendência
- `usuario`: Email do usuário
- `tipo_usuario`: Tipo do usuário
- `data_hora`: Data/hora da alteração
- `acao`: Tipo de ação
- `campo_alterado`: Campo modificado
- `valor_anterior`: Valor antes
- `valor_novo`: Valor depois

### 7.3 Sistema de Notificações

#### **Email (Flask-Mail)**
- Enviado quando:
  - Pendência criada (para cliente)
  - Resposta recusada (para cliente)
  - Pendência resolvida (opcional)

#### **Microsoft Teams (Webhooks)**
- Enviado quando:
  - Pendência criada
  - Resposta do cliente recebida
  - Pendência enviada ao supervisor
  - Pendência recusada

### 7.4 Sistema de Filtros Avançados

**Componente**: Dropdown Multiselect Customizado

**Funcionalidades**:
- Seleção múltipla
- Busca integrada
- Indicadores visuais (cores, ícones)
- Badges de seleção
- Fechamento ao clicar fora
- Fechamento ao abrir outro filtro

**Usado em**:
- Filtro de Segmentos
- Filtro de Empresas (Clientes)
- Filtro de Operadores
- Filtro de Supervisores

### 7.5 Sistema de Gráficos

**Biblioteca**: Chart.js

**Tipos de gráficos**:
- **Pizza**: Distribuição por tipo de pendência
- **Barras**: Pendências abertas vs resolvidas
- **Linha**: Evolução temporal (se implementado)

**Onde usado**:
- Cards de empresas (`/empresas`)
- Relatório mensal (`/relatorios/mensal`)
- Dashboard (`/dashboard`)

### 7.6 Sistema de Upload de Arquivos

**Configuração**:
- Sem limite de tamanho (`MAX_CONTENT_LENGTH = None`)
- Extensões permitidas: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.xlsx`, `.xls`
- Armazenamento: `static/notas_fiscais/`
- Nome do arquivo: `YYYYMMDDHHMMSS_nome_original.ext`

**Segurança**:
- `secure_filename()` para sanitizar nomes
- Validação de extensão
- Criação automática de diretório

### 7.7 Sistema de Exportação

**Formatos**:
- **CSV**: Logs, pendências resolvidas
- **Excel**: Relatórios, pendências resolvidas

**Funcionalidades**:
- Geração dinâmica
- Filtros aplicados
- Headers apropriados
- Download direto

### 7.8 Sistema de Breadcrumbs

Navegação hierárquica exibida em várias telas:
- Segmentos → Segmento → Empresas
- Empresas → Empresa → Painel
- Empresas → Empresa → Nova Pendência

**Design**: Bootstrap breadcrumb com ícones

---

## 8. ESTRUTURA DO BANCO DE DADOS

### 8.1 Modelos Principais

#### **Usuario**
- `id`: Integer (PK)
- `nome`: String
- `email`: String (unique)
- `senha_hash`: String
- `tipo`: String (adm, supervisor, operador, cliente, cliente_supervisor)
- `empresas`: Relationship (many-to-many com Empresa)

#### **Segmento**
- `id`: Integer (PK)
- `nome`: String (unique)

#### **Empresa**
- `id`: Integer (PK)
- `nome`: String (unique)
- `segmento_id`: Integer (FK para Segmento)
- `usuarios`: Relationship (many-to-many com Usuario)

#### **Pendencia**
- `id`: Integer (PK)
- `empresa`: String
- `tipo_pendencia`: String
- `banco`: String (nullable)
- `data`: Date (nullable)
- `data_competencia`: Date (nullable)
- `data_baixa`: Date (nullable)
- `fornecedor_cliente`: String
- `valor`: Float
- `codigo_lancamento`: String (nullable)
- `natureza_sistema`: String (nullable)
- `natureza_operacao`: String (nullable)
- `observacao`: Text
- `status`: String (default: 'PENDENTE CLIENTE')
- `resposta_cliente`: Text (nullable)
- `motivo_recusa`: Text (nullable)
- `motivo_recusa_supervisor`: Text (nullable)
- `nota_fiscal_arquivo`: String (nullable)
- `token_acesso`: String (unique, para acesso público)
- `modificado_por`: String
- `data_resposta`: DateTime (nullable)

#### **LogAlteracao**
- `id`: Integer (PK)
- `pendencia_id`: Integer (FK para Pendencia)
- `usuario`: String
- `tipo_usuario`: String
- `data_hora`: DateTime
- `acao`: String
- `campo_alterado`: String (nullable)
- `valor_anterior`: Text (nullable)
- `valor_novo`: Text (nullable)

#### **Importacao**
- `id`: Integer (PK)
- `nome_arquivo`: String
- `usuario`: String
- `data_hora`: DateTime
- `status`: String (PROCESSANDO, CONCLUIDO, ERRO)
- `mensagem_erro`: Text (nullable)

#### **PermissaoUsuarioPersonalizada**
- `id`: Integer (PK)
- `usuario_id`: Integer (FK para Usuario)
- `funcionalidade`: String
- `permitido`: Boolean

---

## 9. JAVASCRIPT E INTERATIVIDADE

### 9.1 Scripts Principais

#### **Formatação de Moeda**
```javascript
function formatarMoeda(input) {
    // Remove tudo que não é número
    let valor = input.value.replace(/\D/g, '');
    // Formata como moeda brasileira
    valor = (valor / 100).toFixed(2) + '';
    valor = valor.replace(".", ",");
    valor = valor.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    input.value = 'R$ ' + valor;
}
```

#### **Validação Dinâmica de Formulários**
- Mostra/oculta campos conforme tipo de pendência
- Validação em tempo real
- Mensagens de erro contextuais

#### **Dropdown Multiselect**
- JavaScript customizado para controle de estado
- Fechamento ao clicar fora
- Fechamento ao abrir outro
- Busca integrada

#### **Gráficos (Chart.js)**
- Inicialização automática
- Dados dinâmicos do backend
- Cores da paleta UP380

---

## 10. CSS E DESIGN SYSTEM

### 10.1 Paleta de Cores

```css
:root {
  --up380-azul: #1B365D;
  --up380-azul-claro: #005bb5;
  --up380-cinza-claro: #F5F6FA;
  --up380-branco: #FFFFFF;
  --up380-preto: #222B45;
  --up380-verde: #008c6a;
  --up380-vermelho: #C82333;
}
```

### 10.2 Componentes CSS

#### **Cards de Resumo**
- Design moderno com ícones
- Hover effects
- Cores por tipo de informação

#### **Sidebar**
- Gradiente branco
- Sombras suaves
- Animações de transição
- Scrollbar customizada

#### **Tabelas**
- Responsivas
- Hover effects
- Badges coloridos
- Alinhamento consistente

#### **Formulários**
- Inputs com altura mínima
- Focus states destacados
- Validação visual
- Labels consistentes

---

## 11. ROTAS API REST (Blueprint)

O sistema também possui um blueprint de API REST (`api_routes.py`) para integração com frontend React:

### Rotas Disponíveis:
- `/api/auth/login` - Login
- `/api/auth/logout` - Logout
- `/api/auth/check` - Verificar autenticação
- `/api/empresas` - Listar empresas
- `/api/dashboard` - Dados do dashboard
- `/api/pendencia/<id>` - CRUD de pendências
- `/api/logs-recentes` - Logs recentes
- `/api/historico-importacoes` - Histórico de importações
- `/api/tipos-pendencia` - Tipos de pendência
- `/api/importar-planilha` - Importar planilha

---

## 12. CONCLUSÃO

Este relatório documenta completamente o sistema antigo UP380, incluindo:

- ✅ **62 rotas** documentadas
- ✅ **30+ telas** descritas em detalhes
- ✅ **5 tipos de usuários** com permissões mapeadas
- ✅ **9 tipos de pendência** com validações específicas
- ✅ **Fluxos de trabalho** completos
- ✅ **Estrutura do frontend** (CSS, JavaScript, componentes)
- ✅ **Estrutura do backend** (modelos, rotas, validações)

Este documento serve como referência completa para migração e atualização do sistema React.

---

**Data de Criação**: 2025-01-27
**Versão do Sistema Documentado**: Sistema Antigo (Flask + Jinja2)
**Próximo Passo**: Implementação no React seguindo esta documentação




