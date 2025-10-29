# 🚀 PROMPT DE REPLICAÇÃO COMPLETA - Sistema UP380 (2025)

**COPIE E COLE ESTE PROMPT INTEIRO EM OUTRO CHAT/IA**

---

## 📋 CONTEXTO

Você é um desenvolvedor sênior Flask encarregado de atualizar um sistema de gestão de pendências. Implemente TODAS as funcionalidades descritas abaixo de forma completa e funcional.

**Stack Atual:**
- Flask 2.3+ / Flask-SQLAlchemy
- SQLite (pendencias.db)
- Bootstrap 5
- Jinja2
- Pandas (importação Excel)
- Python 3.8+

**Requisitos Críticos:**
- ✅ Preservar dados existentes
- ✅ Manter compatibilidade com rotas atuais
- ✅ Implementar TODAS as funcionalidades listadas
- ✅ Criar migrações seguras com rollback
- ✅ UI moderna (tema escuro, azul/verde UP380)

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO

Execute nesta ordem EXATA:

1. **Banco de Dados** → Estruturas e migrações
2. **Backend** → Rotas, validações, RBAC
3. **Frontend** → Templates e JavaScript
4. **Segurança** → CSRF, rate limiting, headers
5. **Testes** → Validação de cada funcionalidade

---

## 1️⃣ BANCO DE DADOS E MIGRAÇÕES

### 1.1 Nova Tabela: segmento

```sql
CREATE TABLE IF NOT EXISTS segmento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) UNIQUE NOT NULL
);
```

**Modelo ORM:**
```python
class Segmento(db.Model):
    __tablename__ = 'segmento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    empresas = db.relationship('Empresa', backref='segmento', lazy=True)
```

### 1.2 Alterar Tabela: empresa

```sql
ALTER TABLE empresa ADD COLUMN segmento_id INTEGER REFERENCES segmento(id);
```

**Atualizar modelo Empresa:**
```python
class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    segmento_id = db.Column(db.Integer, db.ForeignKey('segmento.id'), nullable=True)
```

### 1.3 Tabela de Permissões (se não existir)

```sql
CREATE TABLE IF NOT EXISTS permissao_usuario_tipo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_usuario VARCHAR(20) NOT NULL,
    funcionalidade VARCHAR(50) NOT NULL,
    permitido BOOLEAN DEFAULT TRUE
);
```

### 1.4 Migração de Dados - Tipos de Pendência

**Criar arquivo: `migrate_nota_fiscal_para_documento.py`**

```python
#!/usr/bin/env python3
"""
Migra tipos antigos 'Nota Fiscal Não Anexada' e 'Nota Fiscal Não Identificada'
para 'Documento Não Anexado'
"""
from app import app, db, Pendencia
from datetime import datetime

def migrar_notas_fiscais():
    with app.app_context():
        tipos_antigos = ['Nota Fiscal Não Anexada', 'Nota Fiscal Não Identificada']
        novo_tipo = 'Documento Não Anexado'
        
        pendencias = Pendencia.query.filter(
            Pendencia.tipo_pendencia.in_(tipos_antigos)
        ).all()
        
        if not pendencias:
            print("✅ Nenhuma pendência encontrada com tipos antigos.")
            return
        
        print(f"\n📊 Encontradas {len(pendencias)} pendências para migrar")
        resposta = input("Deseja continuar? (sim/não): ").strip().lower()
        
        if resposta not in ['sim', 's']:
            print("❌ Migração cancelada.")
            return
        
        contador = 0
        for pendencia in pendencias:
            pendencia.tipo_pendencia = novo_tipo
            contador += 1
        
        db.session.commit()
        print(f"\n✅ {contador} registro(s) migrado(s) com sucesso!")

if __name__ == '__main__':
    migrar_notas_fiscais()
```

**Criar arquivo: `migrate_cliente_supervisor.py`**

```python
#!/usr/bin/env python3
"""
Configura permissões padrão para o novo tipo 'cliente_supervisor'
"""
from app import app, db, configurar_permissoes_padrao

def migrar_permissoes():
    with app.app_context():
        print("🔄 Configurando permissões cliente_supervisor...")
        configurar_permissoes_padrao()
        db.session.commit()
        print("✅ Permissões configuradas com sucesso!")

if __name__ == '__main__':
    migrar_permissoes()
```

---

## 2️⃣ BACKEND (app.py)

### 2.1 Imports e Configurações de Segurança

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
# from flask_wtf.csrf import CSRFProtect  # Opcional
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import re
# ... outros imports

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pendencias.db'

# Segurança
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# csrf = CSRFProtect(app)  # Opcional
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "app-cdn.clickup.com"],
    'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
    'frame-src': ["forms.clickup.com"]
}
talisman = Talisman(app, force_https=False, content_security_policy=csp)

db = SQLAlchemy(app)
mail = Mail(app)
```

### 2.2 Função de Parsing de Moeda

```python
def parse_currency_to_float(valor_str):
    """
    Converte string de moeda BRL para float.
    Ex: 'R$ 1.234,56' → 1234.56
    """
    if not valor_str:
        return 0.0
    
    v = str(valor_str)
    # Remove R$
    v = re.sub(r'R\$', '', v)
    # Remove espaços (incluindo \xa0)
    v = re.sub(r'[\s\xa0\u00a0\u2000-\u200f\u2028-\u202f\u205f-\u206f]', '', v)
    # Remove pontos de milhar e troca vírgula por ponto
    v = v.replace('.', '').replace(',', '.')
    
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0
```

### 2.3 Tipos de Pendência Atualizados

```python
TIPOS_PENDENCIA = [
    'Cartão de Crédito Não Identificado',
    'Pagamento Não Identificado',
    'Recebimento Não Identificado',
    'Documento Não Anexado',
    'Lançamento Não Encontrado em Extrato',
    'Lançamento Não Encontrado em Sistema',
    'Natureza Errada',
    'Competência Errada',
    'Data da Baixa Errada'
]

TIPO_IMPORT_MAP = {
    "CARTAO_NAO_IDENTIFICADO": "Cartão de Crédito Não Identificado",
    "PAGAMENTO_NAO_IDENTIFICADO": "Pagamento Não Identificado",
    "RECEBIMENTO_NAO_IDENTIFICADO": "Recebimento Não Identificado",
    "DOCUMENTO_NAO_ANEXADO": "Documento Não Anexado",
    "LANCAMENTO_NAO_ENCONTRADO_EXTRATO": "Lançamento Não Encontrado em Extrato",
    "LANCAMENTO_NAO_ENCONTRADO_SISTEMA": "Lançamento Não Encontrado em Sistema",
    "NATUREZA_ERRADA": "Natureza Errada",
    "COMPETENCIA_ERRADA": "Competência Errada",
    "DATA_BAIXA_ERRADA": "Data da Baixa Errada",
    # Mapeamentos legados (compatibilidade)
    "NOTA_FISCAL_NAO_ANEXADA": "Documento Não Anexado",
    "NOTA_FISCAL_NAO_IDENTIFICADA": "Documento Não Anexado"
}

TIPO_RULES = {
    "Documento Não Anexado": {
        "required": ["fornecedor_cliente", "valor", "data"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status"],
        "import_columns": ["empresa", "fornecedor", "valor", "data", "observacao", "email_cliente"]
    },
    "Lançamento Não Encontrado em Extrato": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao"],
        "import_columns": ["empresa", "banco", "data", "fornecedor", "valor", "codigo_lancamento", "observacao"]
    },
    "Lançamento Não Encontrado em Sistema": {
        "required": ["fornecedor_cliente", "valor", "data"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao"],
        "import_columns": ["empresa", "fornecedor", "valor", "data", "codigo_lancamento", "observacao"]
    },
    # ... adicionar regras para outros tipos
}
```

### 2.4 Filtro Jinja - Nome Amigável de Tipo

```python
@app.template_filter('nome_tipo_usuario')
def nome_tipo_usuario_filter(tipo):
    tipos = {
        'adm': 'Administrador',
        'supervisor': 'Supervisor',
        'operador': 'Operador',
        'cliente': 'Cliente',
        'cliente_supervisor': 'Cliente Supervisor'
    }
    return tipos.get(tipo, tipo.title())
```

### 2.5 Integração ClickUp

```python
# Iframe do ClickUp
iframe_clickup = """
<iframe class="clickup-embed clickup-dynamic-height"
        src="https://forms.clickup.com/SEU_FORM_ID_AQUI"
        width="100%" height="100%"
        style="background: transparent; border: 1px solid #ccc;"></iframe>
<script async src="https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"></script>
"""
app.jinja_env.globals['iframe_clickup'] = iframe_clickup

@app.route('/log_suporte', methods=['POST'])
def log_suporte():
    """Registra log de abertura do modal de suporte"""
    if 'usuario_id' in session:
        log = LogAlteracao(
            pendencia_id=0,
            usuario=session.get('usuario_email', 'Sistema'),
            tipo_usuario=session.get('usuario_tipo', 'sistema'),
            data_hora=now_brazil(),
            acao='open_support_modal',
            campo_alterado='suporte',
            valor_anterior='',
            valor_novo='Modal de suporte aberto'
        )
        db.session.add(log)
        db.session.commit()
    return {'status': 'success'}
```

### 2.6 Rotas de Navegação Hierárquica

```python
@app.route('/segmentos')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def listar_segmentos():
    """Lista todos os segmentos"""
    segmentos = Segmento.query.order_by(Segmento.nome).all()
    
    segmentos_data = []
    for seg in segmentos:
        empresas_segmento = seg.empresas
        
        if session.get('usuario_tipo') != 'adm':
            empresas_usuario = obter_empresas_para_usuario()
            empresas_segmento = [e for e in empresas_segmento if e.nome in empresas_usuario]
        
        total_pendencias = sum(
            Pendencia.query.filter_by(empresa=e.nome).count() 
            for e in empresas_segmento
        )
        
        segmentos_data.append({
            'id': seg.id,
            'nome': seg.nome,
            'total_empresas': len(empresas_segmento),
            'total_pendencias': total_pendencias
        })
    
    return render_template('segmentos.html', segmentos=segmentos_data)

@app.route('/segmento/<int:segmento_id>')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def listar_empresas_segmento(segmento_id):
    """Lista empresas de um segmento"""
    segmento = Segmento.query.get_or_404(segmento_id)
    
    if session.get('usuario_tipo') == 'adm':
        empresas = segmento.empresas
    else:
        empresas_usuario = obter_empresas_para_usuario()
        empresas = [e for e in segmento.empresas if e.nome in empresas_usuario]
    
    empresas_data = []
    for empresa in empresas:
        total_pendencias = Pendencia.query.filter_by(empresa=empresa.nome).count()
        pendencias_abertas = Pendencia.query.filter_by(
            empresa=empresa.nome, status='PENDENTE CLIENTE'
        ).count()
        
        empresas_data.append({
            'id': empresa.id,
            'nome': empresa.nome,
            'total_pendencias': total_pendencias,
            'pendencias_abertas': pendencias_abertas
        })
    
    return render_template('empresas_por_segmento.html', 
                         segmento=segmento, 
                         empresas=empresas_data)

@app.route('/empresa/<int:empresa_id>')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def listar_pendencias_empresa(empresa_id):
    """Redireciona para dashboard com filtro de empresa"""
    empresa = Empresa.query.get_or_404(empresa_id)
    
    if session.get('usuario_tipo') != 'adm':
        empresas_usuario = obter_empresas_para_usuario()
        if empresa.nome not in empresas_usuario:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('pre_dashboard'))
    
    return redirect(url_for('dashboard', empresa=empresa.nome))
```

### 2.7 Atualizar Rotas Existentes - Uso de parse_currency_to_float

**Em `nova_pendencia()`:**
```python
valor = parse_currency_to_float(request.form['valor'])
```

**Em `editar_pendencia()`:**
```python
'valor': parse_currency_to_float(request.form['valor'])
```

**Em `importar_planilha()`:**
```python
valor=parse_currency_to_float(r.get("valor", "0"))
```

### 2.8 Permissões RBAC - Cliente Supervisor

```python
def configurar_permissoes_padrao():
    """Configura permissões padrão do sistema"""
    
    # Permissões para cliente_supervisor
    atualizar_permissao('cliente_supervisor', 'cadastrar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'editar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'importar_planilha', False)
    atualizar_permissao('cliente_supervisor', 'aprovar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'recusar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'gerenciar_usuarios', False)
    atualizar_permissao('cliente_supervisor', 'gerenciar_empresas', False)
    
    # Permissões TRUE
    atualizar_permissao('cliente_supervisor', 'baixar_anexo', True)
    atualizar_permissao('cliente_supervisor', 'exportar_logs', True)
    atualizar_permissao('cliente_supervisor', 'visualizar_relatorios', True)
    atualizar_permissao('cliente_supervisor', 'pre_dashboard', True)
    atualizar_permissao('cliente_supervisor', 'dashboard', True)
    atualizar_permissao('cliente_supervisor', 'dashboard_resolvidas', True)
    atualizar_permissao('cliente_supervisor', 'listar_pendencias', True)
    atualizar_permissao('cliente_supervisor', 'relatorio_mensal', True)
    atualizar_permissao('cliente_supervisor', 'relatorio_operadores', True)
    atualizar_permissao('cliente_supervisor', 'ver_logs_pendencia', True)
    atualizar_permissao('cliente_supervisor', 'logs_recentes', True)
    atualizar_permissao('cliente_supervisor', 'exportar_logs_csv', True)
    atualizar_permissao('cliente_supervisor', 'editar_observacao', True)
```

---

## 3️⃣ FRONTEND (Templates)

### 3.1 Template: segmentos.html

```html
{% extends "base.html" %}

{% block title %}Segmentos - UP380{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col-12">
            <h1 class="h3 mb-0 text-white">
                <i class="bi bi-diagram-3"></i> Segmentos
            </h1>
            <p class="text-muted">Selecione um segmento para visualizar suas empresas</p>
        </div>
    </div>

    <div class="row g-4">
        {% for segmento in segmentos %}
        <div class="col-md-6 col-lg-4">
            <a href="{{ url_for('listar_empresas_segmento', segmento_id=segmento.id) }}" class="text-decoration-none">
                <div class="card bg-dark border-primary h-100 shadow-sm hover-elevate">
                    <div class="card-body">
                        <h5 class="card-title text-white mb-3">
                            <i class="bi bi-diagram-3 text-primary me-2"></i>{{ segmento.nome }}
                        </h5>
                        <div class="d-flex justify-content-between text-muted">
                            <div>
                                <i class="bi bi-building me-1"></i>
                                <small>{{ segmento.total_empresas }} empresa(s)</small>
                            </div>
                            <div>
                                <i class="bi bi-exclamation-triangle me-1"></i>
                                <small>{{ segmento.total_pendencias }} pendência(s)</small>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-0">
                        <small class="text-primary">
                            <i class="bi bi-arrow-right-circle me-1"></i>Ver empresas
                        </small>
                    </div>
                </div>
            </a>
        </div>
        {% endfor %}
    </div>
</div>

<style>
.hover-elevate {
    transition: all 0.3s ease;
}
.hover-elevate:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 123, 255, 0.3) !important;
}
.bg-dark {
    background-color: #1a1d29 !important;
}
</style>
{% endblock %}
```

### 3.2 Template: empresas_por_segmento.html

```html
{% extends "base.html" %}

{% block title %}{{ segmento.nome }} - Empresas{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Breadcrumb -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb bg-dark p-3 rounded">
            <li class="breadcrumb-item">
                <a href="{{ url_for('listar_segmentos') }}" class="text-primary">
                    <i class="bi bi-diagram-3"></i> Segmentos
                </a>
            </li>
            <li class="breadcrumb-item active text-white">{{ segmento.nome }}</li>
        </ol>
    </nav>

    <div class="row mb-4">
        <div class="col-12">
            <h1 class="h3 text-white">
                <i class="bi bi-building"></i> Empresas - {{ segmento.nome }}
            </h1>
        </div>
    </div>

    <div class="row g-4">
        {% for empresa in empresas %}
        <div class="col-md-6 col-lg-4">
            <a href="{{ url_for('listar_pendencias_empresa', empresa_id=empresa.id) }}" class="text-decoration-none">
                <div class="card bg-dark border-success h-100 shadow-sm hover-elevate">
                    <div class="card-body">
                        <h5 class="card-title text-white mb-3">
                            <i class="bi bi-building text-success me-2"></i>{{ empresa.nome }}
                        </h5>
                        <div class="d-flex justify-content-between text-muted">
                            <div>
                                <i class="bi bi-list-task me-1"></i>
                                <small>{{ empresa.total_pendencias }} total</small>
                            </div>
                            <div>
                                <i class="bi bi-exclamation-circle me-1 text-warning"></i>
                                <small>{{ empresa.pendencias_abertas }} abertas</small>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-0">
                        <small class="text-success">
                            <i class="bi bi-arrow-right-circle me-1"></i>Ver pendências
                        </small>
                    </div>
                </div>
            </a>
        </div>
        {% endfor %}
    </div>

    <div class="mt-4">
        <a href="{{ url_for('listar_segmentos') }}" class="btn btn-outline-primary">
            <i class="bi bi-arrow-left me-2"></i>Voltar
        </a>
    </div>
</div>

<style>
.hover-elevate {
    transition: all 0.3s ease;
}
.hover-elevate:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(25, 135, 84, 0.3) !important;
}
</style>
{% endblock %}
```

### 3.3 Atualizar base.html - Modal de Suporte

Adicionar no menu (dentro do `<ul class="navbar-nav">`):

```html
<li class="nav-item">
    <a class="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#modalSuporte" onclick="logSuporte()">
        <i class="bi bi-life-preserver me-1"></i>Suporte
    </a>
</li>
```

Adicionar antes de `</body>`:

```html
<!-- Modal Suporte -->
<div class="modal fade" id="modalSuporte" tabindex="-1">
    <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-life-preserver me-2"></i>Abrir chamado de suporte
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-0" style="height:80vh;">
                {{ iframe_clickup|safe }}
            </div>
        </div>
    </div>
</div>

<script>
function logSuporte() {
    fetch('/log_suporte', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    }).catch(error => console.log('Erro ao registrar log:', error));
}
</script>
```

### 3.4 Formatação de Moeda - nova_pendencia.html e editar_pendencia.html

Substituir campo valor:

```html
<div class="mb-3">
    <label for="valor" class="form-label">Valor</label>
    <input type="text" class="form-control" id="valor" name="valor" 
           placeholder="R$ 0,00" oninput="formatarMoeda(this)" required>
</div>

<script>
function formatarMoeda(input){
    let v = input.value.replace(/\D/g,'');
    if(!v){ input.value='R$ 0,00'; return; }
    let n = parseInt(v)/100;
    input.value = n.toLocaleString('pt-BR',{
        style:'currency',
        currency:'BRL',
        minimumFractionDigits:2
    });
}
</script>
```

### 3.5 Atualizar importar_planilha.html - Novos Tipos

Substituir o `<select>` de tipos:

```html
<select class="form-select" name="tipo_import" required>
    <option value="">Selecione…</option>
    <optgroup label="Tipos Básicos">
        <option value="CARTAO_NAO_IDENTIFICADO">Cartão de Crédito Não Identificado</option>
        <option value="PAGAMENTO_NAO_IDENTIFICADO">Pagamento Não Identificado</option>
        <option value="RECEBIMENTO_NAO_IDENTIFICADO">Recebimento Não Identificado</option>
    </optgroup>
    <optgroup label="Novos Tipos Consolidados">
        <option value="DOCUMENTO_NAO_ANEXADO">Documento Não Anexado</option>
        <option value="LANCAMENTO_NAO_ENCONTRADO_EXTRATO">Lançamento Não Encontrado em Extrato</option>
        <option value="LANCAMENTO_NAO_ENCONTRADO_SISTEMA">Lançamento Não Encontrado em Sistema</option>
    </optgroup>
    <optgroup label="Tipos Especializados">
        <option value="NATUREZA_ERRADA">Natureza Errada</option>
        <option value="COMPETENCIA_ERRADA">Competência Errada</option>
        <option value="DATA_BAIXA_ERRADA">Data da Baixa Errada</option>
    </optgroup>
</select>
```

### 3.6 Atualizar admin/novo_usuario.html - Cliente Supervisor

```html
<select name="tipo" id="tipo" required class="form-select" onchange="toggleEmpresas()">
    <option value="adm">Administrador</option>
    <option value="supervisor">Supervisor</option>
    <option value="operador">Operador</option>
    <option value="cliente">Cliente</option>
    <option value="cliente_supervisor">Cliente Supervisor</option>
</select>

<script>
function toggleEmpresas() {
    var tipo = document.getElementById('tipo').value;
    var empresasDiv = document.getElementById('empresas_div');
    if (tipo === 'operador' || tipo === 'cliente' || tipo === 'cliente_supervisor') {
        empresasDiv.style.display = 'block';
    } else {
        empresasDiv.style.display = 'none';
    }
}
</script>
```

---

## 4️⃣ SEGURANÇA E DEPENDÊNCIAS

### 4.1 requirements.txt

Adicionar:

```
Flask>=3.0.2
Flask-SQLAlchemy>=3.1.1
Flask-Mail>=0.9.1
Flask-WTF>=1.2.1
Flask-Limiter>=3.5.0
Flask-Talisman>=1.1.0
python-dotenv>=1.0.1
pandas>=2.0.0
openpyxl>=3.1.0
```

### 4.2 Validação de Uploads

```python
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls'}

def allowed_file(filename):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS
```

---

## 5️⃣ CHECKLIST DE VALIDAÇÃO

Execute TODOS estes testes:

### ✅ Banco de Dados
- [ ] Tabela `segmento` criada
- [ ] Coluna `segmento_id` adicionada a `empresa`
- [ ] Permissões `cliente_supervisor` configuradas
- [ ] 2+ pendências migradas de "Nota Fiscal" → "Documento Não Anexado"

### ✅ Backend
- [ ] Função `parse_currency_to_float()` funciona
- [ ] Rotas `/segmentos`, `/segmento/<id>`, `/empresa/<id>` funcionam
- [ ] Rota `/log_suporte` registra logs
- [ ] Novos tipos aparecem em `TIPOS_PENDENCIA`
- [ ] Importação aceita novos tipos

### ✅ Frontend
- [ ] Template `segmentos.html` criado e funcionando
- [ ] Template `empresas_por_segmento.html` criado e funcionando
- [ ] Modal de suporte abre e exibe iframe ClickUp
- [ ] Campo valor formata como R$ 1.234,56 ao digitar
- [ ] Select de importação mostra novos tipos
- [ ] Admin pode criar usuário "Cliente Supervisor"

### ✅ RBAC
- [ ] Cliente Supervisor pode ver dashboards
- [ ] Cliente Supervisor pode baixar anexos
- [ ] Cliente Supervisor pode exportar logs
- [ ] Cliente Supervisor NÃO pode criar pendências
- [ ] Cliente Supervisor NÃO pode importar planilhas

### ✅ Segurança
- [ ] Rate limiting ativo (testar 60 requests rápidas)
- [ ] Headers CSP, HSTS presentes
- [ ] Uploads validam extensão e tamanho
- [ ] Sessões expiram após 2 horas

---

## 6️⃣ COMANDOS DE EXECUÇÃO

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Backup do banco
cp instance/pendencias.db instance/pendencias.db.backup

# 3. Executar migrações
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python -c "from app import app; import sqlite3; app.app_context().push(); conn = sqlite3.connect('instance/pendencias.db'); conn.execute('ALTER TABLE empresa ADD COLUMN segmento_id INTEGER'); conn.commit()"

# 4. Migrar dados
python migrar_nota_fiscal_automatico.py
python migrate_cliente_supervisor.py

# 5. Criar segmentos de exemplo
python -c "from app import app, db, Segmento; app.app_context().push(); [db.session.add(Segmento(nome=s)) for s in ['Financeiro', 'Operacional', 'Comercial']]; db.session.commit()"

# 6. Executar aplicação
python app.py
```

---

## 7️⃣ URLS PARA TESTAR

Após implementação, teste:

1. **Navegação Hierárquica**: http://127.0.0.1:5000/segmentos
2. **Nova Pendência**: http://127.0.0.1:5000/nova (teste formatação moeda)
3. **Importar**: http://127.0.0.1:5000/importar (verifique novos tipos)
4. **Modal Suporte**: Clique em "Suporte" no menu
5. **Cliente Supervisor**: Criar usuário e testar permissões

---

## 🎯 CRITÉRIOS DE SUCESSO

Implementação considerada COMPLETA quando:

1. ✅ Todas as 15 funcionalidades do checklist estão funcionando
2. ✅ Nenhum erro 500 em nenhuma rota
3. ✅ Navegação SEGMENTOS → EMPRESAS → PENDÊNCIAS funciona
4. ✅ Importação aceita novos tipos sem erro
5. ✅ Formatação de moeda funciona em todos os formulários
6. ✅ Cliente Supervisor tem permissões corretas
7. ✅ Modal de suporte abre e registra log
8. ✅ Sem tipos "Nota Fiscal *" no banco de dados

---

## 📞 SUPORTE

Se algo não funcionar:

1. Verifique logs do Flask no terminal
2. Inspecione console do navegador (F12)
3. Teste queries SQL manualmente no banco
4. Verifique se todas as dependências estão instaladas
5. Confirme que migrações foram executadas

---

**FIM DO PROMPT - IMPLEMENTAÇÃO COMPLETA**

**Data**: Outubro 2025  
**Versão**: 3.0 UP380

