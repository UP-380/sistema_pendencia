# GUIA PRÁTICO - QUANDO USAR CADA TIPO DE USUÁRIO
## Sistema UP380 - Gestão de Pendências

---

## 🎯 DECISÃO RÁPIDA: Qual tipo de usuário criar?

### Pergunte-se:

```
┌─────────────────────────────────────────────────┐
│ Esta pessoa vai GERENCIAR o sistema?            │
│ (criar usuários, empresas, configurações)       │
└─────────────────────┬───────────────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
          SIM                   NÃO
           │                     │
      ┌────▼─────┐              │
      │   ADM    │              │
      └──────────┘              │
                                │
      ┌─────────────────────────▼────────────────────┐
      │ Esta pessoa vai APROVAR/RECUSAR pendências?  │
      └─────────────────┬────────────────────────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
            SIM                   NÃO
             │                     │
      ┌──────▼──────┐             │
      │ SUPERVISOR  │             │
      └─────────────┘             │
                                  │
      ┌───────────────────────────▼──────────────────┐
      │ Esta pessoa vai CRIAR/PROCESSAR pendências?  │
      └─────────────────┬──────────────────────────-──┘
                        │
             ┌──────────┴──────────┐
             │                     │
            SIM                   NÃO
             │                     │
      ┌──────▼──────┐             │
      │  OPERADOR   │             │
      └─────────────┘             │
                                  │
      ┌───────────────────────────▼────────────────────┐
      │ Esta pessoa precisa ver RELATÓRIOS AVANÇADOS?  │
      └─────────────────┬────────────────────────────-──┘
                        │
             ┌──────────┴──────────┐
             │                     │
            SIM                   NÃO
             │                     │
   ┌─────────▼────────┐    ┌──────▼────────┐
   │ CLIENTE          │    │    CLIENTE    │
   │ SUPERVISOR       │    │               │
   └──────────────────┘    └───────────────┘
```

---

## 👥 CENÁRIOS PRÁTICOS

### Cenário 1: Equipe Interna (Empresa que Usa o Sistema)

**Situação:** Você é a empresa UP380 e vai usar o sistema internamente.

#### Criar:
- **1-2 ADM** → Proprietários/TI
  - Email: admin@up380.com.br
  - Função: Gerenciar tudo

- **2-3 SUPERVISORES** → Coordenadores/Gerentes
  - Email: coordenador1@up380.com.br
  - Função: Aprovar pendências e gerenciar equipe

- **5-10 OPERADORES** → Equipe operacional
  - Email: operador1@up380.com.br, operador2@up380.com.br
  - Função: Criar e processar pendências no dia a dia

---

### Cenário 2: Cliente Empresa Grande (Múltiplos Usuários)

**Situação:** Empresa ALIANZE vai acessar suas pendências.

#### Criar:
- **1 CLIENTE SUPERVISOR** → Gerente/Coordenador do cliente
  - Email: gerente@alianze.com.br
  - Empresas vinculadas: ALIANZE
  - Função: Ver todas pendências e gerar relatórios

- **2-3 CLIENTES** → Equipe do cliente
  - Email: financeiro@alianze.com.br, comercial@alianze.com.br
  - Empresas vinculadas: ALIANZE
  - Função: Ver e responder pendências

---

### Cenário 3: Cliente Empresa Pequena (1 Usuário)

**Situação:** Empresa BRTRUCK tem 1 pessoa responsável.

#### Criar:
- **1 CLIENTE SUPERVISOR** → Único responsável
  - Email: contato@brtruck.com.br
  - Empresas vinculadas: BRTRUCK
  - Função: Ver, responder e gerar relatórios
  - **Por quê Cliente Supervisor?** Mesmo com 1 usuário, terá acesso a relatórios

---

### Cenário 4: Auditor/Consultor Externo

**Situação:** Consultor precisa ver tudo mas não alterar nada.

#### Criar:
- **1 CLIENTE SUPERVISOR** (sem empresas vinculadas ou com todas)
  - Email: consultor@empresa.com.br
  - Empresas vinculadas: Todas que ele deve acessar
  - Função: Apenas visualização + relatórios
  - ⚠️ **Não dê permissão de responder se não for necessário**

---

### Cenário 5: Estagiário/Trainee

**Situação:** Pessoa em treinamento, vai apenas observar.

#### Criar:
- **1 CLIENTE** (vinculado a empresas de teste)
  - Email: estagiario@up380.com.br
  - Empresas vinculadas: Empresa de teste
  - Função: Ver pendências para aprender o sistema
  - **Depois promover para:** OPERADOR quando estiver pronto

---

## 🔧 QUANDO MUDAR O TIPO DE USUÁRIO

### Promover CLIENTE → CLIENTE SUPERVISOR
**Quando:**
- Cliente pede acesso a relatórios
- Precisa exportar dados
- É gerente/coordenador da empresa

**Como:**
```
1. Ir em: Gerenciar → Usuários
2. Clicar em "Editar" no usuário
3. Mudar tipo de: "Cliente" para "Cliente Supervisor"
4. Salvar
```

### Promover OPERADOR → SUPERVISOR
**Quando:**
- Operador vai coordenar equipe
- Precisa aprovar pendências
- Foi promovido a cargo de gestão

**Como:**
```
1. Gerenciar → Usuários → Editar
2. Mudar tipo para "Supervisor"
3. Salvar
```

### Rebaixar SUPERVISOR → OPERADOR
**Quando:**
- Mudança de função
- Redução de responsabilidades
- Temporariamente afastado da gestão

---

## ⚠️ ERROS COMUNS E COMO EVITAR

### ❌ Erro 1: Criar OPERADOR para Cliente
**Problema:**
```
Cliente da empresa ALIANZE pede acesso
→ Admin cria usuário tipo OPERADOR
→ Cliente pode CRIAR pendências (errado!)
→ Cliente pode IMPORTAR planilhas (errado!)
```

**Solução:** ✅ Criar como CLIENTE ou CLIENTE SUPERVISOR

---

### ❌ Erro 2: Criar CLIENTE SUPERVISOR para Operador Interno
**Problema:**
```
Novo funcionário operacional
→ Admin cria como CLIENTE SUPERVISOR
→ Não consegue CRIAR pendências (frustração!)
→ Não consegue IMPORTAR (não faz o trabalho!)
```

**Solução:** ✅ Criar como OPERADOR

---

### ❌ Erro 3: Dar ADM para Todo Mundo
**Problema:**
```
Admin cria vários usuários ADM "para facilitar"
→ Múltiplas pessoas com acesso total
→ Risco de alterações indevidas
→ Impossível rastrear quem fez o quê
```

**Solução:** ✅ Apenas 1-2 ADM, resto com permissões específicas

---

### ❌ Erro 4: Não Vincular Empresas
**Problema:**
```
Cria usuário OPERADOR
→ Não vincula nenhuma empresa
→ Usuário não vê nada no sistema
→ "O sistema não funciona!"
```

**Solução:** ✅ Sempre vincular empresas ao criar usuário

---

## 📋 CHECKLIST DE CRIAÇÃO DE USUÁRIO

Ao criar um novo usuário, sempre verificar:

```
□ Email correto e único
□ Senha segura gerada
□ Tipo de usuário adequado para a função
□ Empresas vinculadas (exceto ADM)
□ Testar login antes de entregar ao usuário
□ Enviar credenciais de forma segura
□ Instruir sobre as funcionalidades disponíveis
```

---

## 🎓 TREINAMENTO POR TIPO

### Para ADM
**O que treinar:**
- ✅ Criar usuários e atribuir empresas
- ✅ Criar segmentos e empresas
- ✅ Gerenciar permissões
- ✅ Gerar relatórios de desempenho
- ✅ Intervir em pendências se necessário

**Tempo estimado:** 2 horas

---

### Para SUPERVISOR
**O que treinar:**
- ✅ Dashboard supervisor
- ✅ Como aprovar pendências
- ✅ Como recusar com justificativa
- ✅ Relatório de operadores
- ✅ Monitorar tempo de resposta

**Tempo estimado:** 1 hora

---

### Para OPERADOR
**O que treinar:**
- ✅ Criar pendência manual
- ✅ Importar planilha UP380
- ✅ Preencher campos obrigatórios
- ✅ Enviar para aprovação
- ✅ Responder cliente
- ✅ Processar resposta

**Tempo estimado:** 1.5 horas

---

### Para CLIENTE SUPERVISOR
**O que treinar:**
- ✅ Ver pendências da empresa
- ✅ Responder quando solicitado
- ✅ Gerar relatório mensal
- ✅ Exportar dados
- ✅ Interpretar métricas

**Tempo estimado:** 30 minutos

---

### Para CLIENTE
**O que treinar:**
- ✅ Ver pendências
- ✅ Responder quando solicitado
- ✅ Anexar documentos
- ✅ Acompanhar status

**Tempo estimado:** 15 minutos

---

## 💰 SUGESTÃO DE ESTRUTURA POR TAMANHO

### Empresa Pequena (até 50 pendências/mês)
```
👤 1 ADM
👤 1 SUPERVISOR
👤 2 OPERADORES
```

### Empresa Média (50-200 pendências/mês)
```
👤 1 ADM
👤 2 SUPERVISORES
👤 5 OPERADORES
```

### Empresa Grande (200+ pendências/mês)
```
👤 2 ADM (backup)
👤 3 SUPERVISORES (turnos)
👤 10+ OPERADORES (equipes)
```

---

## 🔐 SEGURANÇA POR TIPO

### ADM
- ⚠️ **ALTO RISCO** - Acesso total
- 🔒 Senha forte obrigatória
- 🔒 Troca de senha a cada 90 dias
- 🔒 2FA recomendado
- 🔒 Não compartilhar credenciais

### Supervisor
- ⚠️ **MÉDIO RISCO** - Pode aprovar
- 🔒 Senha forte recomendada
- 🔒 Revisar acessos mensalmente

### Operador
- ⚠️ **BAIXO RISCO** - Apenas execução
- 🔒 Senha padrão aceitável
- 🔒 Trocar senha inicial

### Cliente Supervisor / Cliente
- ⚠️ **RISCO MÍNIMO** - Apenas visualização
- 🔒 Senha simples aceitável
- 🔒 Trocar senha inicial

---

## 📞 SUPORTE

**Dúvidas sobre qual tipo criar?**
1. Leia este guia novamente
2. Use o fluxograma no início
3. Em dúvida, crie com menos permissão
4. É mais fácil promover depois do que revogar

---

**Data:** 27/10/2025  
**Sistema:** UP380 - Gestão de Pendências  
**Versão:** Produção


