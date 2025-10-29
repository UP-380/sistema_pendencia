# 🚀 GUIA RÁPIDO - EXECUTAR SISTEMA DE SEGMENTOS

## ⚡ 3 Passos Simples

### **Passo 1: Executar Migração**
```powershell
python migrate_add_segmento.py
```

Quando perguntar "Deseja continuar?", digite: **sim**

O script irá:
- ✅ Criar estrutura de segmentos no banco
- ✅ Vincular 37 empresas aos 3 segmentos
- ✅ Exibir resumo completo

---

### **Passo 2: Iniciar Servidor**
```powershell
python app.py
```

O servidor iniciará em: `http://localhost:5000`

---

### **Passo 3: Fazer Login**
Use as credenciais do administrador:

**Email:** `adm.pendencia@up380.com.br`  
**Senha:** `Finance.@2`

---

## ✅ PRONTO!

Após o login, você será redirecionado automaticamente para a **tela de Segmentos**.

### **O que você verá:**

1. **3 Cards de Segmentos:**
   - 🏥 FUNERÁRIA (8 empresas)
   - 🛡️ PROTEÇÃO VEICULAR (28 empresas)
   - 💊 FARMÁCIA (1 empresa)

2. **Navegação:**
   - Clique em um segmento → Ver empresas
   - Clique em uma empresa → Ver pendências
   - Use os breadcrumbs para voltar

3. **Menu Superior:**
   - Link "Segmentos" adicionado
   - Gerenciar → Segmentos (admin/supervisor)

---

## 🎨 FUNCIONALIDADES DISPONÍVEIS

### **Para Todos os Usuários:**
- ✅ Visualizar segmentos permitidos
- ✅ Navegar por empresas do segmento
- ✅ Ver pendências das empresas
- ✅ Breadcrumbs para navegação fácil

### **Para Admin/Supervisor:**
- ✅ Ver todos os segmentos
- ✅ Gerenciar segmentos (CRUD)
- ✅ Criar novos segmentos
- ✅ Editar segmentos existentes
- ✅ Deletar segmentos vazios

---

## 📱 RESPONSIVIDADE

O sistema funciona perfeitamente em:
- 💻 Desktop
- 📱 Tablet
- 📱 Mobile

---

## 🔧 TROUBLESHOOTING

### **Erro: "ModuleNotFoundError: No module named 'X'"**
```powershell
pip install -r requirements.txt
```

### **Erro: "Table already exists"**
Não se preocupe! O script detecta isso e continua normalmente.

### **Erro: "Permission denied"**
Execute como administrador:
```powershell
python migrate_add_segmento.py
```

### **Nenhum segmento aparece após login:**
1. Verifique se a migração foi executada com sucesso
2. Verifique se o usuário tem permissão
3. Consulte o console para mensagens de erro

---

## 📊 ESTRUTURA FINAL

### **Banco de Dados:**
- ✅ Tabela `segmento` criada
- ✅ Coluna `segmento_id` adicionada em `empresa`
- ✅ 3 segmentos cadastrados
- ✅ 37 empresas vinculadas

### **Arquivos Novos:**
- ✅ `templates/segmentos.html`
- ✅ `templates/empresas_por_segmento.html`
- ✅ `templates/admin/gerenciar_segmentos.html`
- ✅ `templates/admin/form_segmento.html`
- ✅ `migrate_add_segmento.py`
- ✅ `IMPLEMENTACAO_SEGMENTOS_COMPLETA.md`

### **Arquivos Modificados:**
- ✅ `app.py` (modelos, rotas, funções)
- ✅ `templates/base.html` (menu)
- ✅ `templates/dashboard.html` (breadcrumb)
- ✅ `static/up380.css` (estilos)
- ✅ `templates/admin/novo_usuario.html` (correção)
- ✅ `templates/admin/editar_usuario.html` (correção)

---

## 🎯 ROTAS PRINCIPAIS

| Rota | Descrição |
|------|-----------|
| `/` | Redireciona para segmentos |
| `/segmentos` | Tela principal de segmentos |
| `/segmento/<id>` | Empresas do segmento |
| `/empresa/<id>` | Redireciona para dashboard |
| `/gerenciar_segmentos` | Gerenciar segmentos (admin) |

---

## 💡 DICAS DE USO

### **Navegação Rápida:**
1. Login → Segmentos
2. Clique no segmento → Empresas
3. Clique na empresa → Pendências
4. Use breadcrumb para voltar

### **Adicionar Novo Segmento:**
1. Menu → Gerenciar → Segmentos
2. Botão "Novo Segmento"
3. Digite o nome (será convertido para maiúsculas)
4. Salvar

### **Vincular Empresa a Segmento:**
1. Menu → Gerenciar → Empresas
2. Editar empresa
3. Selecionar segmento no dropdown
4. Salvar

---

## 🎉 TUDO PRONTO!

O sistema está **100% funcional** e pronto para uso.

Qualquer dúvida, consulte:
- `IMPLEMENTACAO_SEGMENTOS_COMPLETA.md` (documentação completa)
- Código-fonte em `app.py` (bem comentado)

**Aproveite o novo sistema de navegação hierárquica!** 🚀

---

**Versão:** 1.0  
**Status:** ✅ Operacional  
**Suporte:** Sistema UP380


