# TABELA RÁPIDA DE PERMISSÕES - UP380

## 📊 Comparativo Visual de Permissões

### ✅ = Pode Fazer | ❌ = Não Pode | ⚠️ = Limitado

| FUNCIONALIDADE | ADM | SUPERVISOR | OPERADOR | CLIENTE SUP. | CLIENTE |
|----------------|:---:|:----------:|:--------:|:------------:|:-------:|
| **USUÁRIOS** |
| Criar usuários | ✅ | ❌ | ❌ | ❌ | ❌ |
| Editar usuários | ✅ | ❌ | ❌ | ❌ | ❌ |
| Deletar usuários | ✅ | ❌ | ❌ | ❌ | ❌ |
| **EMPRESAS** |
| Criar empresas | ✅ | ✅ | ❌ | ❌ | ❌ |
| Editar empresas | ✅ | ✅ | ❌ | ❌ | ❌ |
| Deletar empresas | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver empresas | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **SEGMENTOS** |
| Criar segmentos | ✅ | ✅ | ❌ | ❌ | ❌ |
| Editar segmentos | ✅ | ✅ | ❌ | ❌ | ❌ |
| Deletar segmentos | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver segmentos | ✅ | ✅ | ✅ | ✅ | ✅ |
| **PENDÊNCIAS** |
| Criar pendências | ✅ | ❌ | ✅ | ❌ | ❌ |
| Editar pendências | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ver pendências | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Responder pendências | ✅ | ✅ | ✅ | ✅ | ✅ |
| Aprovar pendências | ✅ | ✅ | ❌ | ❌ | ❌ |
| Recusar pendências | ✅ | ✅ | ❌ | ❌ | ❌ |
| Marcar como resolvida | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ver resolvidas | ✅ | ✅ | ❌ | ❌ | ❌ |
| **IMPORTAÇÃO** |
| Importar planilhas | ✅ | ❌ | ✅ | ❌ | ❌ |
| Ver histórico importação | ✅ | ❌ | ✅ | ❌ | ❌ |
| **RELATÓRIOS** |
| Relatório mensal | ✅ | ✅ | ✅ | ✅ | ❌ |
| Relatório operadores | ✅ | ✅ | ❌ | ⚠️ | ❌ |
| Exportar dados | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| **VISUALIZAÇÃO** |
| Dashboard geral | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard operador | ✅ | ✅ | ✅ | ❌ | ❌ |
| Dashboard supervisor | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ver logs completos | ✅ | ✅ | ✅ | ✅ | ❌ |
| Ver logs recentes | ✅ | ✅ | ✅ | ✅ | ❌ |
| **NAVEGAÇÃO** |
| Menu "Gerenciar" | ✅ | ✅ | ❌ | ❌ | ❌ |
| Botão "Nova Pendência" | ✅ | ❌ | ✅ | ❌ | ❌ |
| Botão "Importar" | ✅ | ❌ | ✅ | ❌ | ❌ |
| Acessar segmentos | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ver por segmento | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 📝 Legenda

- **✅ Pode Fazer:** Acesso completo à funcionalidade
- **❌ Não Pode:** Sem acesso
- **⚠️ Limitado:** Acesso apenas às empresas vinculadas ao usuário

---

## 🎯 Perfil de Cada Usuário

### ADM - Administrador
```
Nível: ⭐⭐⭐⭐⭐
Função: Gerenciar todo o sistema
Acesso: 100% de todas as funcionalidades
```

### Supervisor
```
Nível: ⭐⭐⭐⭐
Função: Aprovar/recusar pendências e gerenciar estrutura
Acesso: 80% (sem gerenciar usuários)
```

### Operador
```
Nível: ⭐⭐⭐
Função: Criar e processar pendências
Acesso: 60% (sem aprovar)
```

### Cliente Supervisor
```
Nível: ⭐⭐
Função: Visualizar e responder + relatórios avançados
Acesso: 30% (visualização avançada)
```

### Cliente
```
Nível: ⭐
Função: Visualizar e responder pendências
Acesso: 10% (apenas visualização básica)
```

---

## 🔄 Fluxo de Trabalho Simplificado

```
┌──────────────┐
│   OPERADOR   │ → Cria pendência
└──────┬───────┘
       ↓
┌──────────────┐
│  SUPERVISOR  │ → Aprova ou recusa
└──────┬───────┘
       ↓ (se aprovado)
┌──────────────┐
│   CLIENTE    │ → Responde informações
└──────┬───────┘
       ↓
┌──────────────┐
│   OPERADOR   │ → Processa resposta
└──────┬───────┘
       ↓
┌──────────────┐
│  SUPERVISOR  │ → Marca como resolvida
└──────────────┘
```

---

## 💡 Dicas de Uso

### Para ADM
- ✅ Crie usuários com o mínimo de permissão necessária
- ✅ Vincule empresas específicas aos usuários
- ✅ Use relatórios para monitorar desempenho
- ✅ Intervenha apenas quando necessário

### Para Supervisor
- ✅ Revise pendências diariamente
- ✅ Dê feedback claro nas recusas
- ✅ Monitore tempo de resposta da equipe
- ✅ Use relatório de operadores

### Para Operador
- ✅ Preencha todos os campos obrigatórios
- ✅ Envie para aprovação apenas quando completo
- ✅ Responda clientes rapidamente
- ✅ Use importação para lotes grandes

### Para Cliente Supervisor
- ✅ Acompanhe pendências semanalmente
- ✅ Gere relatórios mensais
- ✅ Responda pendências dentro do prazo
- ✅ Exporte dados para análises

### Para Cliente
- ✅ Responda quando solicitado
- ✅ Anexe documentos claros
- ✅ Acompanhe o status
- ✅ Contate operador se dúvidas

---

**Data:** 27/10/2025  
**Sistema:** UP380 - Gestão de Pendências


