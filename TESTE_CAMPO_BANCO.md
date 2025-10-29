# 🔍 TESTE DO CAMPO BANCO - NOVA PENDÊNCIA

## 🎯 COMO TESTAR

### **1. Acessar Formulário**
```
http://localhost:5000/nova
```

### **2. Abrir Console do Navegador**
Pressione `F12` e vá na aba "Console"

### **3. Selecionar Tipo de Pendência**
Escolha: **"Pagamento Não Identificado"**

### **4. Verificar no Console**
Você deve ver:
```
Tipo selecionado: Pagamento Não Identificado
```

### **5. Verificar se o Campo Banco Aparece**
O campo "Banco" deve aparecer na tela.

---

## ✅ **O QUE DEVE ACONTECER**

Quando você seleciona **"Pagamento Não Identificado"**, devem aparecer:

1. ✅ **Banco** (obrigatório)
2. ✅ **Data da Pendência** (obrigatório)
3. ✅ **Fornecedor/Cliente** (obrigatório)
4. ✅ **Valor** (obrigatório)
5. ✅ **Observação** (opcional)

---

## ❌ **SE O CAMPO BANCO NÃO APARECER**

Execute este comando no Console do navegador (F12):

```javascript
// Forçar exibição do campo banco
document.getElementById('grp_banco').style.display = 'block';
document.getElementById('banco').required = true;
```

Depois me avise o que aconteceu!

---

## 🔧 **CORREÇÕES APLICADAS**

1. ✅ Adicionado console.log para debug
2. ✅ Fallback para mostrar campos básicos se nenhum tipo estiver selecionado
3. ✅ Campo banco configurado para aparecer em:
   - Cartão de Crédito Não Identificado
   - Pagamento Não Identificado
   - Recebimento Não Identificado
   - Lançamento Não Encontrado em Extrato
   - Data da Baixa Errada

---

## 📋 **PRÓXIMOS PASSOS**

1. Reinicie o servidor (Ctrl+C e `python app.py`)
2. Acesse `/nova`
3. Abra F12 (Console)
4. Selecione "Pagamento Não Identificado"
5. Me diga o que aparece no console!

---

## 💡 **DICA RÁPIDA**

Se o campo banco não aparecer mesmo assim, pode ser cache do navegador.

**Solução:** Pressione `Ctrl+Shift+R` para dar um refresh forçado.


