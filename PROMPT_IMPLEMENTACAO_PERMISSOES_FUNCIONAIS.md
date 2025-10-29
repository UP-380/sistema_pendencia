# PROMPT: IMPLEMENTAÇÃO DO SISTEMA DE PERMISSÕES FUNCIONAIS
## Sistema UP380 - Gestão de Pendências

**Data:** 27/10/2025  
**Objetivo:** Tornar as permissões personalizadas totalmente funcionais  
**Prioridade:** Alta

---

## 🎯 OBJETIVO

Implementar um sistema de permissões **100% funcional** onde:
1. ✅ Quando uma permissão é **MARCADA** → Funcionalidade **APARECE** e está **ACESSÍVEL**
2. ✅ Quando uma permissão é **DESMARCADA** → Funcionalidade **DESAPARECE** ou **BLOQUEIA ACESSO**
3. ✅ Apenas **ADM** e **SUPERVISOR** podem gerenciar permissões
4. ✅ Permissões personalizadas **SOBREPÕEM** permissões do tipo padrão

---

## 📋 PERMISSÕES DISPONÍVEIS

### **Gestão de Pendências**
| Código | Nome | Impacto no Sistema |
|--------|------|-------------------|
| `cadastrar_pendencia` | Cadastrar Pendência | Botão "Nova Pendência" + Rota `/nova` |
| `editar_pendencia` | Editar Pendência | Botão "Editar" + Rota `/editar/<id>` |
| `aprovar_pendencia` | Aprovar Pendência | Dashboard Supervisor + Rota `/supervisor/aprovar/<id>` |
| `recusar_pendencia` | Recusar Pendência | Botão "Recusar" + Rota `/supervisor/recusar/<id>` |
| `baixar_anexo` | Baixar Anexo | Links de download de PDF + Rota `/nota_fiscal/<filename>` |

### **Importações**
| Código | Nome | Impacto no Sistema |
|--------|------|-------------------|
| `importar_planilha` | Importar Planilha | Link "Importar" + Rota `/importar` |

### **Logs e Relatórios**
| Código | Nome | Impacto no Sistema |
|--------|------|-------------------|
| `exportar_logs` | Exportar Logs | Botão "Exportar" em logs + Funcionalidade de export |
| `visualizar_relatorios` | Visualizar Relatórios | Rotas `/relatorio_mensal` e `/relatorio_operadores` |

### **Administração**
| Código | Nome | Impacto no Sistema |
|--------|------|-------------------|
| `gerenciar_usuarios` | Gerenciar Usuários | Menu "Gerenciar → Usuários" + Rota `/gerenciar_usuarios` |
| `gerenciar_empresas` | Gerenciar Empresas | Menu "Gerenciar → Empresas" + Rota `/gerenciar_empresas` |

---

## 🏗️ ESTRUTURA ATUAL (JÁ EXISTE)

### **Models (Banco de Dados)**
```python
class PermissaoUsuarioTipo(db.Model):
    """Permissões padrão por tipo de usuário"""
    id = db.Column(db.Integer, primary_key=True)
    tipo_usuario = db.Column(db.String(20), nullable=False)  # 'adm', 'supervisor', etc.
    funcionalidade = db.Column(db.String(50), nullable=False)  # 'cadastrar_pendencia', etc.
    permitido = db.Column(db.Boolean, default=True)

class PermissaoUsuarioPersonalizada(db.Model):
    """Permissões personalizadas por usuário (sobrepõe o tipo)"""
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    funcionalidade = db.Column(db.String(50), nullable=False)
    permitido = db.Column(db.Boolean, default=True)
```

### **Funções Helper (Já Existem)**
```python
def checar_permissao(tipo_usuario, funcionalidade):
    """Checa permissão padrão do tipo"""
    permissao = PermissaoUsuarioTipo.query.filter_by(tipo_usuario=tipo_usuario, funcionalidade=funcionalidade).first()
    if permissao:
        return permissao.permitido
    return True  # Padrão: permite

def checar_permissao_usuario(usuario_id, tipo_usuario, funcionalidade):
    """Checa permissão personalizada do usuário (sobrepõe tipo)"""
    p = PermissaoUsuarioPersonalizada.query.filter_by(usuario_id=usuario_id, funcionalidade=funcionalidade).first()
    if p:
        return p.permitido
    return checar_permissao(tipo_usuario, funcionalidade)

def atualizar_permissao(tipo_usuario, funcionalidade, permitido):
    """Atualiza permissão de um tipo de usuário"""
    permissao = PermissaoUsuarioTipo.query.filter_by(tipo_usuario=tipo_usuario, funcionalidade=funcionalidade).first()
    if permissao:
        permissao.permitido = permitido
    else:
        permissao = PermissaoUsuarioTipo(tipo_usuario=tipo_usuario, funcionalidade=funcionalidade, permitido=permitido)
        db.session.add(permissao)
    db.session.commit()
```

### **Constante (Já Existe)**
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

---

## 🔧 O QUE PRECISA SER IMPLEMENTADO

### **ETAPA 1: Criar Decorator de Verificação de Permissões**

#### Criar novo decorator `@permissao_funcionalidade_requerida`

**Localização:** `app.py` (após o decorator `@permissao_requerida` existente)

**Função:**
```python
def permissao_funcionalidade_requerida(funcionalidade):
    """
    Decorator que verifica se o usuário tem permissão para uma funcionalidade específica
    Usa permissões personalizadas se existirem, senão usa permissões do tipo
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                flash('Faça login para acessar esta página.', 'warning')
                return redirect(url_for('login'))
            
            usuario_id = session['usuario_id']
            tipo_usuario = session.get('usuario_tipo')
            
            # ADM sempre tem acesso total
            if tipo_usuario == 'adm':
                return f(*args, **kwargs)
            
            # Verifica permissão personalizada do usuário
            tem_permissao = checar_permissao_usuario(usuario_id, tipo_usuario, funcionalidade)
            
            if not tem_permissao:
                flash(f'Você não tem permissão para acessar esta funcionalidade.', 'danger')
                return redirect(url_for('acesso_negado'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

### **ETAPA 2: Aplicar Decorator nas Rotas Existentes**

#### 2.1. Cadastrar Pendência
```python
@app.route('/nova', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
@permissao_funcionalidade_requerida('cadastrar_pendencia')  # ← ADICIONAR
def nova():
    # ... código existente
```

#### 2.2. Editar Pendência
```python
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
@permissao_funcionalidade_requerida('editar_pendencia')  # ← ADICIONAR
def editar(id):
    # ... código existente
```

#### 2.3. Aprovar Pendência
```python
@app.route('/supervisor/aprovar/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
@permissao_funcionalidade_requerida('aprovar_pendencia')  # ← ADICIONAR
def supervisor_aprovar(id):
    # ... código existente
```

#### 2.4. Recusar Pendência
```python
@app.route('/supervisor/recusar/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
@permissao_funcionalidade_requerida('recusar_pendencia')  # ← ADICIONAR
def supervisor_recusar(id):
    # ... código existente
```

#### 2.5. Baixar Anexo
```python
@app.route('/nota_fiscal/<filename>')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
@permissao_funcionalidade_requerida('baixar_anexo')  # ← ADICIONAR
def nota_fiscal(filename):
    # ... código existente
```

#### 2.6. Importar Planilha
```python
@app.route('/importar', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
@permissao_funcionalidade_requerida('importar_planilha')  # ← ADICIONAR
def importar():
    # ... código existente
```

#### 2.7. Visualizar Relatórios
```python
@app.route('/relatorio_mensal')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente_supervisor')
@permissao_funcionalidade_requerida('visualizar_relatorios')  # ← ADICIONAR
def relatorio_mensal():
    # ... código existente

@app.route('/relatorio_operadores')
@permissao_requerida('adm', 'supervisor', 'cliente_supervisor')
@permissao_funcionalidade_requerida('visualizar_relatorios')  # ← ADICIONAR
def relatorio_operadores():
    # ... código existente
```

#### 2.8. Gerenciar Usuários
```python
@app.route('/gerenciar_usuarios')
@permissao_requerida('adm')
@permissao_funcionalidade_requerida('gerenciar_usuarios')  # ← ADICIONAR
def gerenciar_usuarios():
    # ... código existente
```

#### 2.9. Gerenciar Empresas
```python
@app.route('/gerenciar_empresas')
@permissao_requerida('supervisor', 'adm')
@permissao_funcionalidade_requerida('gerenciar_empresas')  # ← ADICIONAR
def gerenciar_empresas():
    # ... código existente
```

---

### **ETAPA 3: Passar Permissões para Templates (Controle Visual)**

#### 3.1. Criar Context Processor

**Localização:** `app.py` (após as funções helper)

```python
@app.context_processor
def inject_permissoes():
    """
    Injeta permissões do usuário atual em todos os templates
    Permite controlar visibilidade de botões/links no frontend
    """
    permissoes = {}
    
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        tipo_usuario = session.get('usuario_tipo')
        
        # ADM tem todas as permissões
        if tipo_usuario == 'adm':
            for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
                for func, _ in funcionalidades:
                    permissoes[func] = True
        else:
            # Verifica cada permissão
            for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
                for func, _ in funcionalidades:
                    permissoes[func] = checar_permissao_usuario(usuario_id, tipo_usuario, func)
    
    return dict(permissoes_usuario=permissoes)
```

---

### **ETAPA 4: Atualizar Templates (Controle de Visibilidade)**

#### 4.1. `templates/base.html` - Navbar

**ANTES:**
```html
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('nova') }}">
        <i class="bi bi-plus-circle me-1"></i> Nova Pendência
    </a>
</li>
```

**DEPOIS:**
```html
{% if permissoes_usuario.get('cadastrar_pendencia', False) %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('nova') }}">
        <i class="bi bi-plus-circle me-1"></i> Nova Pendência
    </a>
</li>
{% endif %}
```

**ANTES:**
```html
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('importar') }}">
        <i class="bi bi-upload me-1"></i> Importar
    </a>
</li>
```

**DEPOIS:**
```html
{% if permissoes_usuario.get('importar_planilha', False) %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('importar') }}">
        <i class="bi bi-upload me-1"></i> Importar
    </a>
</li>
{% endif %}
```

**ANTES:**
```html
<li class="dropdown-item">
    <a href="{{ url_for('gerenciar_usuarios') }}">Usuários</a>
</li>
<li class="dropdown-item">
    <a href="{{ url_for('gerenciar_empresas') }}">Empresas</a>
</li>
```

**DEPOIS:**
```html
{% if permissoes_usuario.get('gerenciar_usuarios', False) %}
<li><a class="dropdown-item" href="{{ url_for('gerenciar_usuarios') }}">Usuários</a></li>
{% endif %}
{% if permissoes_usuario.get('gerenciar_empresas', False) %}
<li><a class="dropdown-item" href="{{ url_for('gerenciar_empresas') }}">Empresas</a></li>
{% endif %}
```

#### 4.2. `templates/dashboard.html` - Botões de Ação

**Adicionar ao topo do arquivo:**
```html
{% set pode_editar = permissoes_usuario.get('editar_pendencia', False) %}
{% set pode_baixar_anexo = permissoes_usuario.get('baixar_anexo', False) %}
```

**Botão Editar:**
```html
{% if pode_editar %}
<a href="{{ url_for('editar', id=p.id) }}" class="btn btn-sm btn-warning">
    <i class="bi bi-pencil me-1"></i>Editar
</a>
{% endif %}
```

**Link de Download de Nota Fiscal:**
```html
{% if pode_baixar_anexo and p.nota_fiscal %}
<a href="{{ url_for('nota_fiscal', filename=p.nota_fiscal) }}" target="_blank">
    <i class="bi bi-file-pdf me-1"></i>Ver Nota
</a>
{% endif %}
```

#### 4.3. `templates/supervisor_pendencias.html` - Botões Supervisor

**Adicionar ao topo:**
```html
{% set pode_aprovar = permissoes_usuario.get('aprovar_pendencia', False) %}
{% set pode_recusar = permissoes_usuario.get('recusar_pendencia', False) %}
```

**Botões de Ação:**
```html
{% if pode_aprovar %}
<button onclick="aprovarPendencia({{ p.id }})" class="btn btn-success btn-sm">
    <i class="bi bi-check-circle me-1"></i>Aprovar
</button>
{% endif %}

{% if pode_recusar %}
<button onclick="recusarPendencia({{ p.id }})" class="btn btn-danger btn-sm">
    <i class="bi bi-x-circle me-1"></i>Recusar
</button>
{% endif %}
```

#### 4.4. `templates/relatorio_mensal.html` - Links de Relatórios

**Remover do navbar se não tiver permissão:**
```html
{% if permissoes_usuario.get('visualizar_relatorios', False) %}
<!-- Conteúdo do relatório -->
{% else %}
<div class="alert alert-warning">
    <i class="bi bi-exclamation-triangle me-2"></i>
    Você não tem permissão para visualizar relatórios.
</div>
{% endif %}
```

---

### **ETAPA 5: Adicionar Rota de Acesso Negado**

**Localização:** `app.py`

```python
@app.route('/acesso_negado')
def acesso_negado():
    """Página exibida quando usuário tenta acessar funcionalidade sem permissão"""
    return render_template('acesso_negado.html'), 403
```

**Template:** `templates/acesso_negado.html` (já existe, mas verificar)

---

### **ETAPA 6: Inicializar Permissões Padrão no Startup**

**Localização:** `app.py` - No bloco `if __name__ == '__main__':`

```python
def inicializar_permissoes_padrao():
    """
    Define permissões padrão para cada tipo de usuário
    Executado na inicialização do sistema
    """
    # Mapeamento: tipo_usuario → [funcionalidades_permitidas]
    permissoes_padrao = {
        'adm': [
            'cadastrar_pendencia', 'editar_pendencia', 'aprovar_pendencia', 'recusar_pendencia',
            'baixar_anexo', 'importar_planilha', 'exportar_logs', 'visualizar_relatorios',
            'gerenciar_usuarios', 'gerenciar_empresas'
        ],
        'supervisor': [
            'editar_pendencia', 'aprovar_pendencia', 'recusar_pendencia',
            'baixar_anexo', 'exportar_logs', 'visualizar_relatorios', 'gerenciar_empresas'
        ],
        'operador': [
            'cadastrar_pendencia', 'editar_pendencia', 'baixar_anexo',
            'importar_planilha', 'visualizar_relatorios'
        ],
        'cliente_supervisor': [
            'baixar_anexo', 'visualizar_relatorios'
        ],
        'cliente': [
            'baixar_anexo'
        ]
    }
    
    with app.app_context():
        # Para cada tipo de usuário
        for tipo, funcionalidades_permitidas in permissoes_padrao.items():
            # Para cada funcionalidade no sistema
            for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
                for func, _ in funcionalidades:
                    # Verifica se já existe registro
                    permissao_existente = PermissaoUsuarioTipo.query.filter_by(
                        tipo_usuario=tipo,
                        funcionalidade=func
                    ).first()
                    
                    if not permissao_existente:
                        # Cria novo registro
                        permitido = func in funcionalidades_permitidas
                        nova_permissao = PermissaoUsuarioTipo(
                            tipo_usuario=tipo,
                            funcionalidade=func,
                            permitido=permitido
                        )
                        db.session.add(nova_permissao)
        
        db.session.commit()
        print("✅ Permissões padrão inicializadas com sucesso!")

# Adicionar no bloco if __name__ == '__main__':
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuarios_iniciais()
        ensure_segmento_schema()
        migrar_empresas_existentes()
        inicializar_permissoes_padrao()  # ← ADICIONAR ESTA LINHA
    app.run(debug=True, host='0.0.0.0')
```

---

## 🧪 TESTES NECESSÁRIOS

### **Teste 1: Permissões de Operador**
1. Login como operador
2. Verificar navbar:
   - ✅ "Nova Pendência" deve aparecer
   - ✅ "Importar" deve aparecer
   - ❌ "Gerenciar" NÃO deve aparecer
3. Tentar acessar `/gerenciar_usuarios` diretamente
   - ❌ Deve redirecionar para "Acesso Negado"

### **Teste 2: Permissões de Cliente**
1. Login como cliente
2. Verificar navbar:
   - ❌ "Nova Pendência" NÃO deve aparecer
   - ❌ "Importar" NÃO deve aparecer
   - ✅ Links de anexos devem funcionar
3. Tentar acessar `/nova` diretamente
   - ❌ Deve redirecionar para "Acesso Negado"

### **Teste 3: Permissões Personalizadas**
1. ADM edita um operador
2. Desmarca "Cadastrar Pendência"
3. Salva
4. Login como esse operador
5. Verificar:
   - ❌ "Nova Pendência" NÃO deve aparecer
   - ❌ Rota `/nova` deve ser bloqueada

### **Teste 4: Permissões de Supervisor**
1. Login como supervisor
2. Verificar:
   - ✅ Dashboard Supervisor funciona
   - ✅ Botões "Aprovar" e "Recusar" aparecem
   - ❌ "Nova Pendência" NÃO aparece (supervisores não criam)
   - ✅ "Gerenciar Empresas" aparece

### **Teste 5: ADM Sempre Tem Tudo**
1. Login como ADM
2. Verificar:
   - ✅ Todos os botões/links aparecem
   - ✅ Todas as rotas são acessíveis
   - ✅ Mesmo que desmarcado na edição, ADM ignora restrições

---

## 📊 RESUMO DE IMPLEMENTAÇÃO

### Arquivos a Modificar:
1. **`app.py`**
   - Criar decorator `@permissao_funcionalidade_requerida`
   - Criar context processor `inject_permissoes()`
   - Criar função `inicializar_permissoes_padrao()`
   - Adicionar decorator em ~15 rotas
   - Adicionar inicialização no startup

2. **`templates/base.html`**
   - Adicionar `{% if permissoes_usuario.get(...) %}` em 5+ links

3. **`templates/dashboard.html`**
   - Adicionar controle de visibilidade em botões

4. **`templates/supervisor_pendencias.html`**
   - Adicionar controle de visibilidade em botões de aprovação

5. **`templates/relatorio_mensal.html`**
   - Adicionar verificação de permissão

6. **`templates/relatorio_operadores.html`**
   - Adicionar verificação de permissão

7. **`templates/operador_pendencias.html`**
   - Adicionar controle de visibilidade se necessário

---

## ⚠️ OBSERVAÇÕES IMPORTANTES

### 1. **ADM Sempre Tem Acesso Total**
- Mesmo que permissões sejam desmarcadas, ADM bypassa tudo
- Implementado no decorator com `if tipo_usuario == 'adm': return f(*args, **kwargs)`

### 2. **Permissões Personalizadas Sobrepõem Tipo**
- Se houver `PermissaoUsuarioPersonalizada` → Usa ela
- Se NÃO houver → Usa `PermissaoUsuarioTipo` (padrão do tipo)

### 3. **Dois Níveis de Controle**
- **Backend (Decorator):** Bloqueia acesso à rota (segurança)
- **Frontend (Template):** Esconde botão/link (UX)
- **Ambos são necessários!**

### 4. **Supervisores e ADM Gerenciam Permissões**
- Rota `/editar_usuario` já tem `@permissao_requerida('supervisor', 'adm')`
- Apenas eles veem checkboxes de permissões

### 5. **Permissões São Dinâmicas**
- Mudança de permissão é imediata
- Próximo login ou refresh da página já aplica nova configuração

---

## 🎯 RESULTADO ESPERADO

### Antes da Implementação:
- ❌ Checkboxes de permissões não fazem nada
- ❌ Todos os botões aparecem para todos
- ❌ Qualquer usuário pode acessar qualquer rota (se souber a URL)

### Depois da Implementação:
- ✅ Checkboxes controlam acesso real
- ✅ Botões aparecem/desaparecem conforme permissão
- ✅ Rotas bloqueadas com mensagem clara
- ✅ Segurança no backend + UX no frontend
- ✅ Sistema de permissões 100% funcional

---

## 📝 CHECKLIST DE IMPLEMENTAÇÃO

- [ ] **ETAPA 1:** Criar decorator `@permissao_funcionalidade_requerida`
- [ ] **ETAPA 2:** Aplicar decorator em todas as rotas (15+ rotas)
- [ ] **ETAPA 3:** Criar context processor `inject_permissoes()`
- [ ] **ETAPA 4:** Atualizar templates (base.html, dashboard, supervisor, etc)
- [ ] **ETAPA 5:** Verificar rota `/acesso_negado` existe
- [ ] **ETAPA 6:** Criar e executar `inicializar_permissoes_padrao()`
- [ ] **TESTE 1:** Testar como operador (deve ter acesso limitado)
- [ ] **TESTE 2:** Testar como cliente (deve ter acesso mínimo)
- [ ] **TESTE 3:** Editar permissões e verificar mudança
- [ ] **TESTE 4:** Testar como supervisor (acesso médio)
- [ ] **TESTE 5:** Testar como ADM (acesso total sempre)

---

**Prioridade:** 🔴 ALTA  
**Complexidade:** 🟡 MÉDIA  
**Tempo Estimado:** 2-3 horas  
**Impacto:** 🟢 MUITO POSITIVO - Controle fino de acesso

---

**Criado em:** 27/10/2025  
**Sistema:** UP380 - Gestão de Pendências  
**Versão:** Prompt Completo para Implementação


