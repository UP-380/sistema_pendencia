# RELATÓRIO COMPLETO - TIPOS DE USUÁRIOS E PERMISSÕES
## Sistema UP380 - Gestão de Pendências

**Data:** 27/10/2025  
**Versão do Sistema:** Produção  
**Total de Tipos de Usuários:** 5

---

## ÍNDICE
1. [Visão Geral dos Tipos de Usuários](#visão-geral)
2. [ADM - Administrador](#adm---administrador)
3. [Supervisor](#supervisor)
4. [Operador](#operador)
5. [Cliente Supervisor](#cliente-supervisor)
6. [Cliente](#cliente)
7. [Comparativo de Permissões](#comparativo-de-permissões)
8. [Fluxo de Trabalho por Usuário](#fluxo-de-trabalho)

---

## VISÃO GERAL

### Hierarquia de Permissões
```
┌─────────────────────────────────────────┐
│              ADM                        │ ← Acesso Total
│         (Administrador)                 │
└─────────────────────────────────────────┘
              │
              ├─────────────────────────────┐
              │                             │
┌─────────────▼──────────┐   ┌────────────▼────────────┐
│      SUPERVISOR        │   │   CLIENTE SUPERVISOR    │
│   (Aprovar/Recusar)    │   │  (Ver + Relatórios)     │
└────────────────────────┘   └─────────────────────────┘
              │
┌─────────────▼──────────┐
│       OPERADOR         │
│  (Criar/Responder)     │
└────────────────────────┘
              │
┌─────────────▼──────────┐
│        CLIENTE         │ ← Apenas Visualização
│      (Visualizar)      │
└────────────────────────┘
```

### Resumo Rápido

| Tipo | Nome Completo | Nível | Principal Função |
|------|---------------|-------|------------------|
| **adm** | Administrador | 5 | Gerenciar todo o sistema |
| **supervisor** | Supervisor | 4 | Aprovar/recusar pendências |
| **operador** | Operador | 3 | Criar e responder pendências |
| **cliente_supervisor** | Cliente Supervisor | 2 | Visualizar + relatórios avançados |
| **cliente** | Cliente | 1 | Apenas visualizar pendências |

---

## ADM - ADMINISTRADOR

### 🎯 Perfil
**Nível de Acesso:** ⭐⭐⭐⭐⭐ (Máximo)  
**Nome no Sistema:** Administrador  
**Código:** `adm`

### ✅ PODE FAZER (Acesso Total)

#### 1. Gerenciamento de Usuários
- ✅ **Criar usuários** (todos os tipos)
- ✅ **Editar usuários** (email, senha, tipo, empresas)
- ✅ **Deletar usuários**
- ✅ **Visualizar lista de usuários**
- ✅ **Atribuir empresas a usuários**
- ✅ **Gerenciar permissões** personalizadas

**Rotas:**
- `/gerenciar_usuarios` - Listar usuários
- `/novo_usuario` - Criar usuário
- `/editar_usuario/<id>` - Editar usuário
- `/deletar_usuario/<id>` - Excluir usuário
- `/gerenciar_permissoes` - Configurar permissões

#### 2. Gerenciamento de Segmentos
- ✅ **Criar segmentos** (Funerária, Proteção Veicular, etc.)
- ✅ **Editar segmentos**
- ✅ **Deletar segmentos**
- ✅ **Visualizar segmentos**

**Rotas:**
- `/gerenciar_segmentos` - Listar segmentos
- `/novo_segmento` - Criar segmento
- `/editar_segmento/<id>` - Editar segmento
- `/deletar_segmento/<id>` - Excluir segmento

#### 3. Gerenciamento de Empresas
- ✅ **Criar empresas**
- ✅ **Editar empresas**
- ✅ **Deletar empresas**
- ✅ **Vincular/desvincular segmentos**
- ✅ **Visualizar todas as empresas**

**Rotas:**
- `/gerenciar_empresas` - Listar empresas
- `/nova_empresa` - Criar empresa
- `/editar_empresa/<id>` - Editar empresa
- `/deletar_empresa/<id>` - Excluir empresa

#### 4. Pendências (Acesso Completo)
- ✅ **Visualizar todas as pendências** (qualquer empresa)
- ✅ **Criar pendências**
- ✅ **Editar pendências**
- ✅ **Responder pendências** (como operador)
- ✅ **Aprovar pendências** (como supervisor)
- ✅ **Recusar pendências** (como supervisor)
- ✅ **Ver histórico completo**
- ✅ **Ver logs de alterações**
- ✅ **Deletar pendências** (se necessário)

**Rotas:**
- `/dashboard` - Dashboard de pendências
- `/empresas` - Visão por empresas
- `/segmentos` - Visão por segmentos
- `/nova` - Criar pendência
- `/editar/<id>` - Editar pendência
- `/operador/pendencias` - Dashboard operador
- `/supervisor/pendencias` - Dashboard supervisor

#### 5. Importação de Dados
- ✅ **Importar planilhas** UP380
- ✅ **Ver histórico de importações**
- ✅ **Processar importações em lote**

**Rotas:**
- `/importar` - Importar planilha
- `/historico_importacoes` - Ver histórico

#### 6. Relatórios e Análises
- ✅ **Relatório mensal** (todas as empresas)
- ✅ **Relatório de operadores** (desempenho)
- ✅ **Relatório customizado** por período
- ✅ **Exportar dados**
- ✅ **Ver métricas do sistema**

**Rotas:**
- `/relatorio_mensal` - Relatório mensal
- `/relatorio_operadores` - Desempenho operadores

#### 7. Navegação e Visualização
- ✅ **Acessar segmentos**
- ✅ **Acessar empresas por segmento**
- ✅ **Ver pendências resolvidas**
- ✅ **Ver logs recentes**
- ✅ **Buscar em todas as pendências**

#### 8. Configurações do Sistema
- ✅ **Alterar configurações globais**
- ✅ **Gerenciar permissões personalizadas**
- ✅ **Ver logs do sistema**
- ✅ **Backup e restore** (se implementado)

### ❌ NÃO PODE FAZER
**Nenhuma restrição** - Administrador tem acesso total ao sistema.

---

## SUPERVISOR

### 🎯 Perfil
**Nível de Acesso:** ⭐⭐⭐⭐ (Alto)  
**Nome no Sistema:** Supervisor  
**Código:** `supervisor`

### ✅ PODE FAZER

#### 1. Gerenciamento de Empresas
- ✅ **Criar empresas**
- ✅ **Editar empresas**
- ✅ **Vincular segmentos a empresas**

**Rotas:**
- `/gerenciar_empresas`
- `/nova_empresa`
- `/editar_empresa/<id>`

#### 2. Gerenciamento de Segmentos
- ✅ **Visualizar segmentos**
- ✅ **Criar segmentos**
- ✅ **Editar segmentos**

**Rotas:**
- `/gerenciar_segmentos`
- `/novo_segmento`
- `/editar_segmento/<id>`

#### 3. Fluxo de Aprovação (Principal Função)
- ✅ **Dashboard Supervisor** - Ver pendências para aprovação
- ✅ **Aprovar pendências** com justificativa
- ✅ **Recusar pendências** com motivo
- ✅ **Devolver ao operador** para correção
- ✅ **Ver histórico de aprovações**

**Rotas:**
- `/supervisor/pendencias` - Dashboard supervisor
- `/supervisor/aprovar/<id>` - Aprovar pendência
- `/supervisor/recusar/<id>` - Recusar pendência

#### 4. Pendências (Visualização e Edição)
- ✅ **Ver todas as pendências** das empresas vinculadas
- ✅ **Editar pendências**
- ✅ **Adicionar observações**
- ✅ **Ver logs de alterações**
- ✅ **Ver pendências resolvidas**

**Rotas:**
- `/dashboard` - Dashboard
- `/empresas` - Visão por empresas
- `/segmentos` - Visão por segmentos
- `/editar/<id>` - Editar pendência
- `/resolvidas` - Pendências resolvidas

#### 5. Relatórios Avançados
- ✅ **Relatório mensal** (empresas vinculadas)
- ✅ **Relatório de operadores** (desempenho da equipe)
- ✅ **Exportar dados**
- ✅ **Ver métricas**

**Rotas:**
- `/relatorio_mensal` - Relatório mensal
- `/relatorio_operadores` - Desempenho operadores

#### 6. Navegação
- ✅ **Acessar segmentos**
- ✅ **Ver empresas por segmento**
- ✅ **Ver logs recentes**
- ✅ **Buscar pendências**

### ❌ NÃO PODE FAZER

#### 1. Gerenciamento de Usuários
- ❌ **Criar usuários**
- ❌ **Editar usuários**
- ❌ **Deletar usuários**
- ❌ **Gerenciar permissões**

#### 2. Limitações em Empresas
- ❌ **Deletar empresas**
- ⚠️ **Ver empresas** - apenas as vinculadas ao seu usuário

#### 3. Limitações em Segmentos
- ❌ **Deletar segmentos**

#### 4. Importação
- ❌ **Importar planilhas** (reservado para operadores/adm)

---

## OPERADOR

### 🎯 Perfil
**Nível de Acesso:** ⭐⭐⭐ (Médio)  
**Nome no Sistema:** Operador  
**Código:** `operador`

### ✅ PODE FAZER

#### 1. Criar e Gerenciar Pendências (Principal Função)
- ✅ **Criar novas pendências**
- ✅ **Editar pendências** (antes de enviar ao supervisor)
- ✅ **Responder pendências** do cliente
- ✅ **Adicionar observações**
- ✅ **Anexar documentos/notas fiscais**
- ✅ **Enviar para aprovação** do supervisor

**Rotas:**
- `/nova` - Criar pendência
- `/editar/<id>` - Editar pendência
- `/operador/responder/<id>` - Responder cliente

#### 2. Dashboard do Operador
- ✅ **Dashboard Operador** - Ver pendências sob sua responsabilidade
- ✅ **Filtrar pendências** por status
- ✅ **Buscar pendências**
- ✅ **Ver pendências aguardando resposta**
- ✅ **Ver pendências devolvidas** pelo supervisor

**Rotas:**
- `/operador/pendencias` - Dashboard operador
- `/dashboard` - Dashboard geral

#### 3. Visualização
- ✅ **Ver pendências** das empresas vinculadas
- ✅ **Ver detalhes** de pendências
- ✅ **Ver histórico** de alterações
- ✅ **Ver logs**

**Rotas:**
- `/empresas` - Visão por empresas
- `/segmentos` - Visão por segmentos
- `/ver/<id>` - Ver detalhes

#### 4. Importação de Dados
- ✅ **Importar planilhas** UP380
- ✅ **Ver histórico** de importações

**Rotas:**
- `/importar` - Importar planilha
- `/historico_importacoes` - Ver histórico

#### 5. Relatórios Básicos
- ✅ **Relatório mensal** (empresas vinculadas)
- ✅ **Ver métricas básicas**

**Rotas:**
- `/relatorio_mensal` - Relatório mensal

#### 6. Natureza de Operação
- ✅ **Adicionar natureza de operação** às pendências
- ✅ **Editar natureza de operação**

**Rotas:**
- `/operador/natureza_operacao/<id>` - Adicionar natureza

### ❌ NÃO PODE FAZER

#### 1. Aprovação
- ❌ **Aprovar pendências** (apenas supervisor)
- ❌ **Recusar pendências**
- ❌ **Marcar como resolvida** (apenas supervisor)

#### 2. Gerenciamento Administrativo
- ❌ **Criar usuários**
- ❌ **Editar usuários**
- ❌ **Criar empresas**
- ❌ **Editar empresas**
- ❌ **Criar segmentos**
- ❌ **Editar segmentos**

#### 3. Relatórios Avançados
- ❌ **Relatório de operadores** (ver desempenho da equipe)
- ❌ **Relatórios customizados avançados**

#### 4. Visualização Completa
- ❌ **Ver pendências resolvidas** (apenas supervisor/adm)
- ⚠️ **Ver empresas** - apenas as vinculadas

---

## CLIENTE SUPERVISOR

### 🎯 Perfil
**Nível de Acesso:** ⭐⭐ (Médio-Baixo)  
**Nome no Sistema:** Cliente Supervisor  
**Código:** `cliente_supervisor`

### ✅ PODE FAZER

#### 1. Visualização Completa
- ✅ **Ver todas as pendências** das empresas vinculadas
- ✅ **Ver detalhes** completos de pendências
- ✅ **Ver histórico** de alterações
- ✅ **Ver logs** de ações
- ✅ **Buscar pendências**

**Rotas:**
- `/dashboard` - Dashboard
- `/empresas` - Visão por empresas
- `/segmentos` - Visão por segmentos
- `/ver/<id>` - Ver detalhes

#### 2. Relatórios Avançados (Diferencial)
- ✅ **Relatório mensal** detalhado
- ✅ **Exportar dados**
- ✅ **Ver métricas avançadas**
- ✅ **Análises por período**

**Rotas:**
- `/relatorio_mensal` - Relatório mensal
- `/relatorio_operadores` - Ver desempenho (leitura)

#### 3. Responder Pendências (Limitado)
- ✅ **Responder pendências** do próprio cliente
- ✅ **Adicionar informações** solicitadas
- ✅ **Anexar documentos**

**Rotas:**
- `/responder_cliente/<id>` - Responder pendência

#### 4. Navegação
- ✅ **Acessar segmentos**
- ✅ **Ver empresas por segmento**
- ✅ **Ver logs recentes**

### ❌ NÃO PODE FAZER

#### 1. Criação e Edição
- ❌ **Criar pendências**
- ❌ **Editar pendências**
- ❌ **Deletar pendências**

#### 2. Fluxo de Aprovação
- ❌ **Aprovar pendências**
- ❌ **Recusar pendências**
- ❌ **Enviar para aprovação**

#### 3. Gerenciamento
- ❌ **Criar usuários/empresas/segmentos**
- ❌ **Editar configurações**
- ❌ **Importar planilhas**

#### 4. Visualização Limitada
- ⚠️ **Ver empresas** - apenas as vinculadas ao seu usuário
- ❌ **Ver pendências de outras empresas**

---

## CLIENTE

### 🎯 Perfil
**Nível de Acesso:** ⭐ (Básico)  
**Nome no Sistema:** Cliente  
**Código:** `cliente`

### ✅ PODE FAZER

#### 1. Visualização Básica
- ✅ **Ver pendências** das empresas vinculadas
- ✅ **Ver detalhes** de pendências
- ✅ **Ver histórico básico**
- ✅ **Buscar pendências**

**Rotas:**
- `/dashboard` - Dashboard (visualização)
- `/empresas` - Ver empresas
- `/ver/<id>` - Ver detalhes

#### 2. Responder Pendências (Principal Função)
- ✅ **Responder pendências** quando solicitado
- ✅ **Adicionar informações** complementares
- ✅ **Anexar documentos** (se necessário)

**Rotas:**
- `/responder_cliente/<id>` - Responder pendência

#### 3. Navegação Limitada
- ✅ **Acessar segmentos** (visualização)
- ✅ **Ver empresas por segmento** (vinculadas)

### ❌ NÃO PODE FAZER (Maioria das Funções)

#### 1. Criação e Edição
- ❌ **Criar pendências**
- ❌ **Editar pendências**
- ❌ **Deletar qualquer coisa**

#### 2. Gerenciamento
- ❌ **Gerenciar usuários**
- ❌ **Gerenciar empresas**
- ❌ **Gerenciar segmentos**

#### 3. Operações Avançadas
- ❌ **Importar planilhas**
- ❌ **Aprovar/recusar**
- ❌ **Ver relatórios avançados**
- ❌ **Ver logs completos**

#### 4. Visualização Limitada
- ❌ **Ver pendências resolvidas**
- ❌ **Ver relatório mensal**
- ❌ **Ver logs recentes**
- ⚠️ **Ver empresas** - apenas as vinculadas
- ❌ **Ver métricas do sistema**

#### 5. Navegação
- ❌ **Menu Gerenciar** não aparece
- ❌ **Botão "Nova Pendência"** não aparece
- ❌ **Botão "Importar"** não aparece

---

## COMPARATIVO DE PERMISSÕES

### Tabela Resumida

| Funcionalidade | ADM | Supervisor | Operador | Cliente Sup. | Cliente |
|----------------|-----|------------|----------|--------------|---------|
| **Gerenciar Usuários** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Gerenciar Empresas** | ✅ | ✅ Criar/Editar | ❌ | ❌ | ❌ |
| **Gerenciar Segmentos** | ✅ | ✅ Criar/Editar | ❌ | ❌ | ❌ |
| **Criar Pendências** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Editar Pendências** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Aprovar Pendências** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Responder Pendências** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Ver Pendências** | ✅ Todas | ✅ Vinculadas | ✅ Vinculadas | ✅ Vinculadas | ✅ Vinculadas |
| **Importar Planilhas** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Relatório Mensal** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Relatório Operadores** | ✅ | ✅ | ❌ | ✅ Ver | ❌ |
| **Ver Logs Completos** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Ver Resolvidas** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Dashboard Operador** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Dashboard Supervisor** | ✅ | ✅ | ❌ | ❌ | ❌ |

### Matriz Detalhada de Rotas

| Rota | ADM | Supervisor | Operador | Cliente Sup. | Cliente |
|------|-----|------------|----------|--------------|---------|
| `/gerenciar_usuarios` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/novo_usuario` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/gerenciar_empresas` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/nova_empresa` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/gerenciar_segmentos` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/novo_segmento` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/segmentos` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/empresas` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/dashboard` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/nova` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `/editar/<id>` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/importar` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `/operador/pendencias` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/supervisor/pendencias` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/supervisor/aprovar/<id>` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/responder_cliente/<id>` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/relatorio_mensal` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `/relatorio_operadores` | ✅ | ✅ | ❌ | ✅ Ver | ❌ |
| `/resolvidas` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/logs_recentes` | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## FLUXO DE TRABALHO

### Ciclo Completo de uma Pendência

```
1. [OPERADOR] Cria pendência
         ↓
2. [OPERADOR] Envia para aprovação
         ↓
3. [SUPERVISOR] Revisa pendência
         ↓
    ┌────┴────┐
    ↓         ↓
[APROVADO] [RECUSADO/DEVOLVIDO]
    ↓         ↓
4. [CLIENTE] Responde (se aprovado)
    ↓         ↓
5. [OPERADOR] Processa resposta
    ↓         ↓ (volta para 2)
6. [SUPERVISOR] Marca como RESOLVIDA
```

### Responsabilidades por Fase

| Fase | Responsável | Ação |
|------|-------------|------|
| **Cadastro** | Operador | Criar pendência com todos os dados |
| **Primeira Aprovação** | Supervisor | Validar dados e aprovar |
| **Envio ao Cliente** | Sistema | Notificação automática |
| **Resposta do Cliente** | Cliente / Cliente Supervisor | Fornecer informações |
| **Processamento** | Operador | Analisar resposta e processar |
| **Segunda Aprovação** | Supervisor | Validar solução e marcar como resolvida |
| **Arquivamento** | Sistema | Mover para "Resolvidas" |

---

## CASOS DE USO POR TIPO DE USUÁRIO

### ADM - Administrador
**Cenário:** Gerenciar todo o sistema
1. Criar novos usuários operadores
2. Criar segmentos de negócio
3. Criar empresas e vincular a segmentos
4. Atribuir empresas a operadores
5. Monitorar todos os dashboards
6. Gerar relatórios de desempenho
7. Intervir em qualquer pendência se necessário

### Supervisor
**Cenário:** Controle de qualidade e aprovação
1. Receber pendências no dashboard supervisor
2. Revisar dados preenchidos pelo operador
3. Aprovar ou recusar com justificativa
4. Monitorar tempo de resposta dos operadores
5. Gerar relatórios de desempenho da equipe
6. Marcar pendências como resolvidas após confirmação

### Operador
**Cenário:** Processamento diário de pendências
1. Importar planilha UP380 com pendências
2. Criar pendências manualmente quando necessário
3. Preencher todos os dados obrigatórios
4. Enviar para aprovação do supervisor
5. Responder dúvidas dos clientes
6. Processar respostas recebidas
7. Reenviar para aprovação após processamento

### Cliente Supervisor
**Cenário:** Gestão e acompanhamento do cliente
1. Visualizar todas as pendências da empresa
2. Responder pendências quando solicitado
3. Gerar relatórios mensais para análise interna
4. Monitorar tempo de resolução
5. Acompanhar histórico de pendências
6. Exportar dados para análises

### Cliente
**Cenário:** Responder solicitações
1. Ver pendências da própria empresa
2. Responder quando for solicitado complemento
3. Anexar documentos necessários
4. Acompanhar status das pendências

---

## RESUMO FINAL

### Hierarquia de Poder
```
ADM (100%) > Supervisor (80%) > Operador (60%) > Cliente Sup. (30%) > Cliente (10%)
```

### Principais Diferenças

| Aspecto | ADM | Supervisor | Operador |
|---------|-----|------------|----------|
| **Foco** | Gestão Total | Aprovação | Execução |
| **Criar Pendências** | Sim | Não | Sim |
| **Aprovar** | Sim | Sim | Não |
| **Gerenciar Usuários** | Sim | Não | Não |
| **Empresas** | Todas | Vinculadas | Vinculadas |

### Recomendações de Uso

1. **ADM:** 1-2 pessoas máximo (proprietário + TI)
2. **Supervisor:** Gerentes/coordenadores (1 por área)
3. **Operador:** Equipe operacional (múltiplos)
4. **Cliente Supervisor:** Gerente do cliente
5. **Cliente:** Usuário final do cliente

---

**Documento gerado em:** 27/10/2025  
**Versão do Sistema:** Produção - UP380  
**Total de Páginas:** 15  
**Status:** ✅ Completo e Atualizado



