# 📋 RELATÓRIO COMPLETO - ÁREAS DE CONFIGURAÇÃO
## Sistema Antigo: Gerenciar Usuários, Empresas e Segmentos

---

## 📑 ÍNDICE

1. [Visão Geral](#1-visão-geral)
2. [Gerenciar Usuários](#2-gerenciar-usuários)
3. [Gerenciar Empresas](#3-gerenciar-empresas)
4. [Gerenciar Segmentos](#4-gerenciar-segmentos)
5. [Sistema de Permissões](#5-sistema-de-permissões)
6. [Estrutura do Frontend](#6-estrutura-do-frontend)

---

## 1. VISÃO GERAL

As áreas de configuração do sistema antigo permitem gerenciar os elementos fundamentais:
- **Usuários**: Criação, edição, exclusão e atribuição de permissões
- **Empresas**: Criação, edição, exclusão e vinculação a segmentos
- **Segmentos**: Criação, edição, exclusão de grupos de empresas

**Permissões**: Apenas `adm` e `supervisor` podem acessar essas áreas.

---

## 2. GERENCIAR USUÁRIOS

### 2.1 Tela de Listagem (`/gerenciar_usuarios`)

**Arquivo**: `templates/admin/gerenciar_usuarios.html`

**Funcionalidades**:
- Lista todos os usuários cadastrados
- Exibe informações: Email, Tipo, Empresas Permitidas, Status
- Botões de ação: Editar, Excluir

**Estrutura da Tabela**:
- **Email**: Email do usuário
- **Tipo**: Tipo de usuário (adm, supervisor, operador, cliente, cliente_supervisor)
- **Empresas Permitidas**:
  - `adm`: Badge verde "Todas as empresas"
  - Outros: Lista de badges com nomes das empresas
  - Se nenhuma: Badge amarelo "Nenhuma empresa"
- **Status**: Ativo/Inativo
- **Ações**: Botões Editar e Excluir

**Design**:
- Tabela Bootstrap simples
- Badges coloridos para status
- Botão "Novo Usuário" no topo

---

### 2.2 Criar Novo Usuário (`/novo_usuario`)

**Arquivo**: `templates/admin/novo_usuario.html`

**Campos do Formulário**:
1. **Email** (obrigatório, tipo email)
2. **Senha** (obrigatório, tipo password)
3. **Tipo de Usuário** (obrigatório, select):
   - Administrador
   - Supervisor
   - Operador
   - Cliente
   - Cliente Supervisor
4. **Empresas Permitidas** (condicional):
   - Aparece apenas para: Operador, Cliente, Cliente Supervisor
   - Checkboxes com todas as empresas cadastradas
   - Múltipla seleção

**Validações**:
- Email único (não pode existir outro usuário com mesmo email)
- Senha obrigatória
- Tipo obrigatório

**JavaScript**:
- Função `toggleEmpresas()`: Mostra/oculta campo de empresas baseado no tipo
- Executada no `onchange` do select de tipo
- Executada no `DOMContentLoaded` para estado inicial

**Fluxo Backend**:
1. Valida email único
2. Cria usuário com hash de senha (`generate_password_hash`)
3. Vincula empresas selecionadas (se houver)
4. Salva permissões personalizadas (se diferentes do padrão do tipo)
5. Redireciona para listagem com mensagem de sucesso

**Permissões Personalizadas**:
- Sistema permite criar permissões individuais por usuário
- Se permissão marcada for diferente do padrão do tipo, salva como exceção
- Armazenado em `PermissaoUsuarioPersonalizada`

---

### 2.3 Editar Usuário (`/editar_usuario/<id>`)

**Arquivo**: `templates/admin/editar_usuario.html`

**Campos do Formulário**:
1. **Email** (pré-preenchido, obrigatório)
2. **Nova Senha** (opcional, tipo password)
   - Se deixado em branco, mantém senha atual
   - Se preenchido, atualiza senha
3. **Tipo de Usuário** (pré-selecionado, obrigatório)
4. **Empresas Permitidas** (checkboxes pré-marcadas):
   - Aparece para todos os tipos exceto `adm`
   - Mostra todas as empresas
   - Empresas já vinculadas vêm marcadas
5. **Permissões do Usuário** (seção expandida):
   - Organizadas por categorias:
     - **Gestão de Pendências**: Cadastrar, Editar, Aprovar, Recusar, Baixar Anexo
     - **Importações**: Importar Planilha
     - **Logs e Relatórios**: Exportar Logs, Visualizar Relatórios
     - **Administração**: Gerenciar Usuários, Gerenciar Empresas
   - Checkboxes pré-marcadas com permissões atuais
   - Permissões diferentes do padrão do tipo são salvas como exceção
6. **Usuário Ativo** (checkbox):
   - Marca se usuário está ativo ou inativo

**JavaScript**:
- Função `toggleEmpresas()`: Oculta empresas apenas para `adm`

**Fluxo Backend**:
1. Atualiza email
2. Atualiza senha (se fornecida)
3. Atualiza tipo
4. Atualiza empresas vinculadas
5. Remove permissões personalizadas antigas
6. Salva novas permissões personalizadas (se diferentes do padrão)
7. Atualiza status ativo/inativo
8. Redireciona com mensagem de sucesso

---

### 2.4 Excluir Usuário (`/deletar_usuario/<id>`)

**Método**: POST

**Validações**:
- Confirmação via JavaScript (`confirm()`)
- Remove usuário do banco
- Remove permissões personalizadas (cascata)

**Redirecionamento**: Volta para listagem com mensagem de sucesso

---

## 3. GERENCIAR EMPRESAS

### 3.1 Tela de Listagem (`/gerenciar_empresas`)

**Arquivo**: `templates/admin/gerenciar_empresas.html`

**Funcionalidades**:
- Lista todas as empresas cadastradas
- Exibe informações: ID, Nome, Segmento, Usuários, Pendências, Ações
- Resumo por segmento (cards coloridos)
- Validação antes de excluir

**Estrutura da Tabela**:
- **ID**: Badge cinza com ID numérico
- **Nome**: Nome da empresa em negrito
- **Segmento**: 
  - Badge azul com nome do segmento (se vinculado)
  - Badge cinza "Sem Segmento" (se não vinculado)
- **Usuários**: Badge com quantidade de usuários vinculados
- **Pendências**: Badge amarelo (se > 0) ou verde (se = 0)
- **Ações**: 
  - Botão Editar (sempre)
  - Botão Excluir:
    - Desabilitado se tiver pendências ou usuários vinculados
    - Habilitado se não tiver vínculos

**Resumo por Segmento**:
- Cards coloridos mostrando quantidade de empresas por segmento
- Card cinza para empresas sem segmento
- Layout em grid responsivo

**Modais**:
1. **Modal de Confirmação de Exclusão**:
   - Exibe nome da empresa
   - Alerta de ação irreversível
   - Botões: Cancelar, Sim Excluir

2. **Modal de Impedimento de Exclusão**:
   - Exibe motivos (pendências vinculadas, usuários vinculados)
   - Instruções de como proceder
   - Botão: Entendi

**JavaScript**:
- `confirmarDelecaoEmpresa(button)`: Abre modal de confirmação
- `mostrarMotivoNaoPodeExcluir(button)`: Abre modal de impedimento

---

### 3.2 Criar Nova Empresa (`/nova_empresa`)

**Arquivo**: `templates/admin/form_empresa.html`

**Campos do Formulário**:
1. **Nome da Empresa** (obrigatório, texto):
   - Placeholder: "Ex: ALIANZE, AUTOBRAS, PLANO PAI, etc."
   - Validação: Nome único no sistema
2. **Segmento** (opcional, select):
   - Opção "-- Sem Segmento --" (valor vazio)
   - Lista de segmentos cadastrados
   - Validação: Segmento deve existir (se fornecido)

**Layout**:
- Formulário principal à esquerda (col-lg-8)
- Card de ajuda à direita (col-lg-4):
  - Informações sobre segmentos
  - Dicas de uso

**Validações Backend**:
- Nome obrigatório e não vazio
- Nome único (não pode existir outra empresa com mesmo nome)
- Segmento válido (se fornecido)

**Integração Automática**:
- Função `integrar_nova_empresa()`:
  - Adiciona empresa à lista `EMPRESAS`
  - Registra log de integração
  - Notifica Teams (se configurado)
  - Retorna True se sucesso

**Fluxo Backend**:
1. Valida nome
2. Valida segmento (se fornecido)
3. Cria empresa
4. Integra automaticamente no sistema
5. Redireciona com mensagem de sucesso

---

### 3.3 Editar Empresa (`/editar_empresa/<id>`)

**Arquivo**: `templates/admin/form_empresa.html` (mesmo template, com `empresa` preenchido)

**Campos do Formulário**:
- Mesmos campos de criar, mas pré-preenchidos
- **Nome**: Valor atual da empresa
- **Segmento**: Segmento atual selecionado

**Card de Informações** (lateral):
- ID da empresa
- Segmento atual
- Quantidade de usuários vinculados

**Validações Backend**:
- Nome obrigatório
- Nome único (exceto a própria empresa)
- Segmento válido (se fornecido)

**Fluxo Backend**:
1. Valida nome (pode ser o mesmo da empresa atual)
2. Valida segmento
3. Atualiza empresa
4. Redireciona com mensagem de sucesso

---

### 3.4 Excluir Empresa (`/deletar_empresa/<id>`)

**Método**: POST

**Validações**:
- Não pode excluir se tiver pendências vinculadas
- Não pode excluir se tiver usuários vinculados
- Confirmação via modal JavaScript

**Fluxo Backend**:
1. Verifica pendências vinculadas
2. Verifica usuários vinculados
3. Se houver vínculos, retorna erro
4. Se não houver vínculos, exclui empresa
5. Redireciona com mensagem

---

## 4. GERENCIAR SEGMENTOS

### 4.1 Tela de Listagem (`/gerenciar_segmentos`)

**Arquivo**: `templates/admin/gerenciar_segmentos.html`

**Funcionalidades**:
- Lista todos os segmentos cadastrados
- Exibe: Nome, Total de Empresas, Ações

**Estrutura da Tabela**:
- **Nome do Segmento**: Nome em negrito com ícone contextual:
  - FUNERÁRIA: ❤️ (heart-pulse)
  - PROTEÇÃO VEICULAR: 🛡️ (shield-check)
  - FARMÁCIA: 💊 (capsule)
- **Total de Empresas**: Badge azul arredondado com quantidade
- **Ações**:
  - Ver Empresas (ícone olho)
  - Editar (ícone lápis)
  - Excluir (ícone lixeira):
    - Desabilitado se tiver empresas vinculadas
    - Habilitado apenas se não tiver empresas

**Design**:
- Tabela Bootstrap com hover
- Ícones Bootstrap contextualizados
- Botão "Novo Segmento" no topo

---

### 4.2 Criar Novo Segmento (`/novo_segmento`)

**Arquivo**: `templates/admin/form_segmento.html`

**Campos do Formulário**:
1. **Nome do Segmento** (obrigatório, texto):
   - Placeholder: "Ex: PROTEÇÃO VEICULAR, FUNERÁRIA, FARMÁCIA"
   - Auto-conversão para MAIÚSCULAS no backend
   - Validação: Nome único

**Layout**:
- Card centralizado (col-md-8 col-lg-6)
- Header azul com título
- Card de dicas abaixo do formulário

**Validações Backend**:
- Nome obrigatório e não vazio
- Nome único (não pode existir outro segmento com mesmo nome)
- Conversão automática para maiúsculas

**Fluxo Backend**:
1. Valida nome
2. Converte para maiúsculas
3. Verifica duplicata
4. Cria segmento
5. Redireciona com mensagem de sucesso

---

### 4.3 Editar Segmento (`/editar_segmento/<id>`)

**Arquivo**: `templates/admin/form_segmento.html` (mesmo template)

**Campos do Formulário**:
- Mesmo campo de criar, pré-preenchido
- **Nome**: Valor atual do segmento

**Alert Info**:
- Mostra quantidade de empresas vinculadas ao segmento

**Validações Backend**:
- Nome obrigatório
- Nome único (exceto o próprio segmento)
- Conversão para maiúsculas

**Fluxo Backend**:
1. Valida nome
2. Converte para maiúsculas
3. Atualiza segmento
4. Redireciona com mensagem

---

### 4.4 Excluir Segmento (`/deletar_segmento/<id>`)

**Método**: POST

**Permissão**: Apenas `adm` (supervisor não pode excluir)

**Validações**:
- Não pode excluir se tiver empresas vinculadas
- Confirmação via JavaScript (`confirm()`)

**Fluxo Backend**:
1. Verifica empresas vinculadas
2. Se houver empresas, retorna erro
3. Se não houver, exclui segmento
4. Redireciona com mensagem

---

## 5. SISTEMA DE PERMISSÕES

### 5.1 Estrutura de Permissões

**Modelos**:
1. **PermissaoUsuarioTipo**: Permissões padrão por tipo de usuário
2. **PermissaoUsuarioPersonalizada**: Exceções individuais por usuário

**Funcionalidades Categorizadas**:
```python
FUNCIONALIDADES_CATEGORIZADAS = [
    ('Gestão de Pendências', [
        ('cadastrar_pendencia', 'Cadastrar Pendência'),
        ('editar_pendencia', 'Editar Pendência'),
        ('aprovar_pendencia', 'Aprovar Pendência'),
        ('recusar_pendencia', 'Recusar Pendência'),
        ('baixar_anexo', 'Baixar Anexo'),
    ]),
    ('Importações', [
        ('importar_planilha', 'Importar Planilha'),
    ]),
    ('Logs e Relatórios', [
        ('exportar_logs', 'Exportar Logs'),
        ('visualizar_relatorios', 'Visualizar Relatórios'),
    ]),
    ('Administração', [
        ('gerenciar_usuarios', 'Gerenciar Usuários'),
        ('gerenciar_empresas', 'Gerenciar Empresas'),
    ]),
]
```

### 5.2 Funções de Verificação

**`checar_permissao(tipo_usuario, funcionalidade)`**:
- Verifica permissão padrão do tipo
- Retorna True/False

**`checar_permissao_usuario(usuario_id, tipo_usuario, funcionalidade)`**:
- Primeiro verifica permissão personalizada
- Se não houver personalizada, usa padrão do tipo
- Retorna True/False

**`atualizar_permissao(tipo_usuario, funcionalidade, permitido)`**:
- Atualiza ou cria permissão padrão do tipo

### 5.3 Permissões Padrão

**Operador**:
- ✅ Importar Planilha
- ✅ Cadastrar Pendência
- ✅ Editar Pendência
- ✅ Baixar Anexo
- ✅ Aprovar Pendência
- ✅ Recusar Pendência
- ✅ Visualizar Relatórios

**Supervisor**:
- ✅ Todas as permissões de Operador
- ✅ Gerenciar Usuários
- ✅ Gerenciar Empresas

**Administrador**:
- ✅ Todas as permissões (acesso total)

**Cliente / Cliente Supervisor**:
- ✅ Apenas visualização e resposta de pendências

---

## 6. ESTRUTURA DO FRONTEND

### 6.1 Templates HTML

**Localização**: `templates/admin/`

**Arquivos**:
- `gerenciar_usuarios.html`
- `novo_usuario.html`
- `editar_usuario.html`
- `gerenciar_empresas.html`
- `form_empresa.html`
- `gerenciar_segmentos.html`
- `form_segmento.html`

### 6.2 Design e Estilo

**Framework**: Bootstrap 5.3.0

**Componentes Utilizados**:
- Cards (`card`, `card-header`, `card-body`)
- Tabelas (`table`, `table-hover`, `table-striped`)
- Badges (`badge`, `bg-primary`, `bg-success`, etc.)
- Formulários (`form-control`, `form-select`, `form-check`)
- Modais (`modal`, `modal-dialog`, `modal-content`)
- Breadcrumbs (`breadcrumb`)
- Botões (`btn`, `btn-primary`, `btn-danger`, etc.)

**Ícones**: Bootstrap Icons 1.11.0

**Cores**:
- Azul primário: `#1976d2` / `bg-primary`
- Verde sucesso: `bg-success`
- Amarelo atenção: `bg-warning`
- Vermelho perigo: `bg-danger`
- Cinza secundário: `bg-secondary`

### 6.3 JavaScript

**Funções Principais**:
1. **`toggleEmpresas()`**: Mostra/oculta campo de empresas baseado no tipo de usuário
2. **`confirmarDelecaoEmpresa(button)`**: Abre modal de confirmação de exclusão
3. **`mostrarMotivoNaoPodeExcluir(button)`**: Abre modal explicando por que não pode excluir

**Eventos**:
- `onchange` no select de tipo de usuário
- `onsubmit` nos formulários de exclusão (com `confirm()`)
- `DOMContentLoaded` para inicialização

### 6.4 Validações Frontend

**HTML5**:
- `required` em campos obrigatórios
- `type="email"` para email
- `type="password"` para senhas

**JavaScript**:
- Confirmação antes de excluir
- Validação de campos condicionais
- Feedback visual de estados

---

## 7. ROTAS BACKEND

### 7.1 Rotas de Usuários

| Rota | Método | Permissão | Descrição |
|------|--------|-----------|-----------|
| `/gerenciar_usuarios` | GET | supervisor, adm | Lista usuários |
| `/novo_usuario` | GET, POST | supervisor, adm | Cria usuário |
| `/editar_usuario/<id>` | GET, POST | supervisor, adm | Edita usuário |
| `/deletar_usuario/<id>` | POST | supervisor, adm | Exclui usuário |

### 7.2 Rotas de Empresas

| Rota | Método | Permissão | Descrição |
|------|--------|-----------|-----------|
| `/gerenciar_empresas` | GET | supervisor, adm | Lista empresas |
| `/nova_empresa` | GET, POST | supervisor, adm | Cria empresa |
| `/editar_empresa/<id>` | GET, POST | supervisor, adm | Edita empresa |
| `/deletar_empresa/<id>` | POST | supervisor, adm | Exclui empresa |

### 7.3 Rotas de Segmentos

| Rota | Método | Permissão | Descrição |
|------|--------|-----------|-----------|
| `/gerenciar_segmentos` | GET | supervisor, adm | Lista segmentos |
| `/novo_segmento` | GET, POST | supervisor, adm | Cria segmento |
| `/editar_segmento/<id>` | GET, POST | supervisor, adm | Edita segmento |
| `/deletar_segmento/<id>` | POST | adm | Exclui segmento |

---

## 8. FLUXOS DE TRABALHO

### 8.1 Criar Novo Usuário

1. Admin/Supervisor acessa `/gerenciar_usuarios`
2. Clica em "Novo Usuário"
3. Preenche email, senha, tipo
4. Se tipo for Operador/Cliente, seleciona empresas
5. Submete formulário
6. Sistema valida email único
7. Cria usuário com hash de senha
8. Vincula empresas
9. Salva permissões personalizadas (se houver)
10. Redireciona para listagem com mensagem de sucesso

### 8.2 Criar Nova Empresa

1. Admin/Supervisor acessa `/gerenciar_empresas`
2. Clica em "Nova Empresa"
3. Preenche nome e seleciona segmento (opcional)
4. Submete formulário
5. Sistema valida nome único
6. Cria empresa
7. Integra automaticamente no sistema (`integrar_nova_empresa()`)
8. Redireciona com mensagem de sucesso

### 8.3 Criar Novo Segmento

1. Admin/Supervisor acessa `/gerenciar_segmentos`
2. Clica em "Novo Segmento"
3. Preenche nome
4. Submete formulário
5. Sistema converte para maiúsculas
6. Valida nome único
7. Cria segmento
8. Redireciona com mensagem de sucesso

---

## 9. VALIDAÇÕES E REGRAS DE NEGÓCIO

### 9.1 Usuários

- ✅ Email deve ser único
- ✅ Senha obrigatória na criação
- ✅ Senha opcional na edição (mantém atual se vazio)
- ✅ Empresas obrigatórias para Operador/Cliente/Cliente Supervisor
- ✅ Empresas não aparecem para Administrador
- ✅ Permissões personalizadas são salvas apenas se diferentes do padrão

### 9.2 Empresas

- ✅ Nome deve ser único
- ✅ Nome obrigatório
- ✅ Segmento opcional
- ✅ Não pode excluir se tiver pendências vinculadas
- ✅ Não pode excluir se tiver usuários vinculados
- ✅ Integração automática ao criar

### 9.3 Segmentos

- ✅ Nome deve ser único
- ✅ Nome obrigatório
- ✅ Conversão automática para maiúsculas
- ✅ Não pode excluir se tiver empresas vinculadas
- ✅ Apenas Administrador pode excluir segmentos

---

## 10. INTEGRAÇÃO AUTOMÁTICA DE EMPRESAS

**Função**: `integrar_nova_empresa(empresa)`

**O que faz**:
1. Adiciona empresa à lista global `EMPRESAS`
2. Ordena lista alfabeticamente
3. Registra log de integração
4. Notifica Teams (se configurado)
5. Retorna True se sucesso

**Resultado**: Empresa fica disponível automaticamente em:
- Filtros de empresas
- Dropdowns de seleção
- Painéis e dashboards
- Relatórios

---

## 11. CONCLUSÃO

Este relatório documenta completamente as áreas de configuração do sistema antigo:

- ✅ **3 áreas principais**: Usuários, Empresas, Segmentos
- ✅ **12 rotas** documentadas
- ✅ **8 templates HTML** descritos
- ✅ **Sistema de permissões** detalhado
- ✅ **Validações e regras** mapeadas
- ✅ **Fluxos de trabalho** completos
- ✅ **Estrutura do frontend** documentada

Este documento serve como referência completa para implementação no React.

---

**Data de Criação**: 2025-01-27
**Versão do Sistema Documentado**: Sistema Antigo (Flask + Jinja2)
**Próximo Passo**: Implementação no React seguindo esta documentação




