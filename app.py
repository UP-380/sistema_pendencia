from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, Response, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
# from flask_wtf.csrf import CSRFProtect  # DESABILITADO TEMPORARIAMENTE
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv
import pandas as pd
import requests
import io
import openpyxl
import csv
import pytz
import re
from functools import wraps
from urllib.parse import quote

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pendencias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações de segurança de sessão
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'  # True em produção com HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Alterado de 'Strict' para permitir redirects de login
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Configurações de upload seguro - SEM LIMITES
app.config['MAX_CONTENT_LENGTH'] = None  # SEM LIMITE de tamanho
app.config['UPLOAD_EXTENSIONS'] = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls'}

# Inicializa extensões de segurança
# csrf = CSRFProtect(app)  # DESABILITADO TEMPORARIAMENTE
# Limiter removido para permitir acesso ilimitado

# Configuração do Talisman (segurança de headers)
# Nota: force_https=False para desenvolvimento local. Em produção, defina como True
csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "cdn.jsdelivr.net", "app-cdn.clickup.com"],
    'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
    'font-src': ["'self'", "cdn.jsdelivr.net", "fonts.gstatic.com"],
    'img-src': ["'self'", "data:"],
    'frame-src': ["forms.clickup.com"],
    'connect-src': ["'self'", "cdn.jsdelivr.net"]
}
talisman = Talisman(
    app,
    force_https=False,  # Alterar para True em produção
    strict_transport_security=False,  # Desabilitado para desenvolvimento
    content_security_policy=csp,
    content_security_policy_nonce_in=[]  # Removido para permitir inline scripts
)

# Iframe do ClickUp para formulário de suporte
iframe_clickup = """
<iframe class="clickup-embed clickup-dynamic-height"
        src="https://forms.clickup.com/9007138778/f/8cdw1yu-193593/AZ6310ZHFCSW9ANQGA"
        width="100%" height="100%"
        style="background: transparent; border: 1px solid #ccc;"></iframe>
<script async src="https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"></script>
"""

# Registra o iframe como variável global do Jinja2
app.jinja_env.globals['iframe_clickup'] = iframe_clickup

# Filtro personalizado para formatação de data/hora
@app.template_filter('datetime_local')
def datetime_local_filter(dt):
    """Formata datetime para exibição local"""
    if dt is None:
        return ""
    return dt.strftime('%d/%m/%Y %H:%M')

# Filtro personalizado para exibir nome do tipo de usuário
@app.template_filter('nome_tipo_usuario')
def nome_tipo_usuario_filter(tipo):
    """Retorna o nome amigável do tipo de usuário"""
    nomes = {
        'adm': 'Administrador',
        'supervisor': 'Supervisor',
        'operador': 'Operador',
        'cliente': 'Cliente',
        'cliente_supervisor': 'Cliente Supervisor'
    }
    return nomes.get(tipo, tipo.capitalize())


# Configuração de e-mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Inicializa extensões
db = SQLAlchemy(app)
mail = Mail(app)

EMPRESAS = [
    'ALIANZE', 'AUTOBRAS', 'BRTRUCK', 'CANAÂ', 'COOPERATRUCK', 'ELEVAMAIS',
    'SPEED', 'RAIO', 'EXODO', 'GTA', 'MOVIDAS', 'MASTER', 'PROTEGE ASSOCIAÇÕES',
    'TECH PROTEGE', 'UNIK', 'ARX', 'VALLE'
]

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

# Função utilitária para data/hora local
BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')
def now_brazil():
    return datetime.now(BRAZIL_TZ)

def parse_currency_to_float(valor_str):
    """
    Converte string de moeda brasileira (R$ 1.234,56) para float.
    Remove símbolos de moeda, espaços especiais e converte vírgula para ponto.
    """
    if not valor_str:
        return 0.0
    
    # Converte para string se não for
    v = str(valor_str)
    
    # Remove símbolo R$
    v = re.sub(r'R\$', '', v)
    
    # Remove todos os tipos de espaços (incluindo \xa0, \u00a0, etc.)
    v = re.sub(r'[\s\xa0\u00a0\u2000-\u200f\u2028-\u202f\u205f-\u206f]', '', v)
    
    # Remove pontos de milhar e substitui vírgula decimal por ponto
    v = v.replace('.', '').replace(',', '.')
    
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0

# Regras de validação por tipo de pendência
TIPO_RULES = {
    "Natureza Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data"],
        "forbidden": ["banco", "data_competencia", "data_baixa"],
        "labels": {"data": "Data do Lançamento ou Baixa"},
        "observacao_hint": "Natureza atual no ERP (obrigatório registrar)",
        "columns": ["tipo", "fornecedor_cliente", "valor", "codigo_lancamento", "data", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "codigo_lancamento", "data", "natureza_sistema", "observacao", "email_cliente"]
    },
    "Competência Errada": {
        "required": ["fornecedor_cliente", "valor", "codigo_lancamento", "data_competencia"],
        "forbidden": ["banco", "data_baixa"],
        "labels": {"data_competencia": "Data Competência"},
        "observacao_hint": "Informe: Data da competência errada",
        "columns": ["tipo", "fornecedor_cliente", "valor", "codigo_lancamento", "data_competencia", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "codigo_lancamento", "data_competencia", "observacao", "email_cliente"]
    },
    "Data da Baixa Errada": {
        "required": ["banco", "data_baixa", "fornecedor_cliente", "valor", "codigo_lancamento"],
        "forbidden": [],
        "labels": {"data_baixa": "Data da Baixa"},
        "observacao_hint": "Campo livre para contexto",
        "columns": ["tipo", "banco", "data_baixa", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data_baixa", "fornecedor", "valor", "codigo_lancamento", "observacao", "email_cliente"]
    },
    "Cartão de Crédito Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "valor", "observacao", "email_cliente"]
    },
    "Pagamento Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "fornecedor", "valor", "observacao", "email_cliente"]
    },
    "Recebimento Não Identificado": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "valor", "observacao", "email_cliente"]
    },
    "Documento Não Anexado": {
        "required": ["fornecedor_cliente", "valor", "data"],
    "forbidden": [],
    "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "data", "observacao", "email_cliente"]
    },
    "Lançamento Não Encontrado em Extrato": {
        "required": ["banco", "data", "fornecedor_cliente", "valor"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "banco", "data", "fornecedor", "valor", "codigo_lancamento", "observacao", "email_cliente"]
    },
    "Lançamento Não Encontrado em Sistema": {
        "required": ["fornecedor_cliente", "valor", "data"],
        "forbidden": [],
        "columns": ["tipo", "banco", "data", "fornecedor_cliente", "valor", "codigo_lancamento", "observacao", "status", "modificado_por"],
        "import_columns": ["empresa", "fornecedor", "valor", "data", "codigo_lancamento", "observacao", "email_cliente"]
    }
}

# Mapeamento de tipos para importação
TIPO_IMPORT_MAP = {
    "NATUREZA_ERRADA": "Natureza Errada",
    "COMPETENCIA_ERRADA": "Competência Errada", 
    "DATA_BAIXA_ERRADA": "Data da Baixa Errada",
    "CARTAO_NAO_IDENTIFICADO": "Cartão de Crédito Não Identificado",
    "PAGAMENTO_NAO_IDENTIFICADO": "Pagamento Não Identificado",
    "RECEBIMENTO_NAO_IDENTIFICADO": "Recebimento Não Identificado",
    "DOCUMENTO_NAO_ANEXADO": "Documento Não Anexado",
    "LANCAMENTO_NAO_ENCONTRADO_EXTRATO": "Lançamento Não Encontrado em Extrato",
    "LANCAMENTO_NAO_ENCONTRADO_SISTEMA": "Lançamento Não Encontrado em Sistema",
    # Mapeamentos legados (para compatibilidade com planilhas antigas)
    "NOTA_FISCAL_NAO_ANEXADA": "Documento Não Anexado",
    "NOTA_FISCAL_NAO_IDENTIFICADA": "Documento Não Anexado"
}

def validar_por_tipo(payload):
    """Valida campos obrigatórios e proibidos por tipo de pendência"""
    tipo = payload.get("tipo_pendencia")
    rule = TIPO_RULES.get(tipo)
    if not rule:
        return False, f"Tipo de pendência inválido: {tipo}"

    # Verificar campos obrigatórios (apenas se existir a chave "required")
    if "required" in rule:
        for field in rule["required"]:
            if not payload.get(field):
                return False, f"Campo obrigatório ausente: {field} (tipo {tipo})"

    # Verificar campos proibidos
    for field in rule.get("forbidden", []):
        if payload.get(field):
            return False, f"Campo não deve ser preenchido para {tipo}: {field}"

    # Coerência de valor (converte formato brasileiro)
    if payload.get("valor"):
        try:
            valor_convertido = parse_currency_to_float(payload["valor"])
            if valor_convertido <= 0:
                return False, "Valor deve ser maior que zero."
        except (ValueError, TypeError):
            return False, "Valor inválido. Use formato: R$ 0,00"

    return True, None

def obter_colunas_por_tipo(tipo_pendencia):
    """Retorna as colunas que devem ser exibidas para um tipo específico de pendência"""
    rule = TIPO_RULES.get(tipo_pendencia)
    if rule and "columns" in rule:
        return rule["columns"]
    # Fallback para tipos não configurados
    return ["tipo", "banco", "data", "fornecedor_cliente", "valor", "observacao", "status", "modificado_por"]

def obter_todas_colunas():
    """Retorna todas as colunas disponíveis para o painel"""
    return {
        "tipo": "Tipo",
        "banco": "Banco", 
        "data": "Data da Pendência",
        "data_abertura": "Data de Abertura",
        "fornecedor_cliente": "Fornecedor/Cliente",
        "valor": "Valor",
        "codigo_lancamento": "Código",
        "data_competencia": "Data Comp.",
        "data_baixa": "Data Baixa",
        "observacao": "Observação",
        "status": "Status",
        "modificado_por": "Modificado por"
    }

def pick(val_a, val_b):
    """Usa id se vier, senão usa nome"""
    return val_a or val_b

def parse_date_or_none(s):
    """Converte string para data ou retorna None - aceita múltiplos formatos"""
    if not s or str(s).strip() == "" or str(s).strip().lower() in ["nan", "none", "null"]:
        return None
    
    s = str(s).strip()
    
    # Lista de formatos de data aceitos
    date_formats = [
        "%Y-%m-%d",      # 2025-08-18
        "%d/%m/%Y",      # 18/08/2025
        "%d-%m-%Y",      # 18-08-2025
        "%Y/%m/%d",      # 2025/08/18
        "%d/%m/%y",      # 18/08/25
        "%d-%m-%y",      # 18-08-25
        "%d.%m.%Y",      # 18.08.2025
        "%d.%m.%y",      # 18.08.25
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    
    # Tentar converter se for um número (Excel às vezes retorna números)
    try:
        if s.replace('.', '').replace('-', '').isdigit():
            # Pode ser um timestamp do Excel
            if '.' in str(s):
                # Timestamp do Excel
                excel_date = datetime(1900, 1, 1) + timedelta(days=float(s) - 2)
                return excel_date.date()
    except (ValueError, TypeError):
        pass
    
    return None

def validar_row_por_tipo(tipo, row):
    """Valida uma linha da planilha conforme o tipo de pendência"""
    rule = TIPO_RULES.get(tipo)
    if not rule:
        return f"Tipo de pendência inválido: {tipo}"
    
    def has(field):
        """Verifica se o campo tem valor válido"""
        val = row.get(field, "")
        return val not in [None, "", "NaN", "nan", "None", "null", "NULL", "undefined", "N/A", "n/a"]
    
    def get_field_value(field):
        """Obtém valor do campo com fallbacks"""
        # Tentar campo original
        val = row.get(field, "")
        if val not in [None, "", "NaN", "nan", "None", "null", "NULL", "undefined", "N/A", "n/a"]:
            return val
        
        # Tentar variações do nome
        field_variations = [
            field.replace("_cliente", ""),
            field.replace("_or_id", ""),
            field + "_id"
        ]
        
        for variation in field_variations:
            val = row.get(variation, "")
            if val not in [None, "", "NaN", "nan", "None", "null", "NULL", "undefined", "N/A", "n/a"]:
                return val
        
        return ""
    
    # Verificar campos obrigatórios
    for field in rule.get("required", []):
        field_value = get_field_value(field)
        if not field_value:
            return f"Campo obrigatório ausente ou vazio: {field}"
    
    # Verificar campos proibidos
    for field in rule.get("forbidden", []):
        if has(field):
            return f"Campo proibido para {tipo}: {field}"
    
    # Validar valor
    if has("valor"):
        try:
            valor = float(row["valor"])
            if valor <= 0:
                return "Valor deve ser maior que zero."
        except (ValueError, TypeError):
            return "Valor deve ser um número válido."
    
    # Validar datas específicas
    if tipo == "Competência Errada" and has("data_competencia"):
        if not parse_date_or_none(row.get("data_competencia")):
            return "Data Competência inválida. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Data da Baixa Errada" and has("data_baixa"):
        if not parse_date_or_none(row.get("data_baixa")):
            return "Data da Baixa inválida. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Natureza Errada" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data do Lançamento ou Baixa inválida. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    # Validar campos de data obrigatórios para outros tipos
    if tipo == "Recebimento Não Identificado" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Recebimento Não Identificado. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Pagamento Não Identificado" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Pagamento Não Identificado. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Cartão de Crédito Não Identificado" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Cartão de Crédito Não Identificado. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    if tipo == "Nota Fiscal Não Anexada" and has("data"):
        if not parse_date_or_none(row.get("data")):
            return "Data inválida para Nota Fiscal Não Anexada. Use formato: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
    
    return None

def label_tipo_planilha(tipo_import):
    """Converte tipo de importação para rótulo humano"""
    return TIPO_IMPORT_MAP.get(tipo_import, tipo_import)

def usuario_tem_acesso(usuario_email, empresa_id):
    """Verifica se o usuário tem acesso à empresa"""
    # Implementação simplificada - você pode ajustar conforme sua lógica de permissões
    usuario = Usuario.query.filter_by(email=usuario_email).first()
    if not usuario:
        return False
    
    # Se for admin, tem acesso a todas
    if usuario.tipo == 'adm':
        return True
    
    # Verificar se a empresa está na lista de empresas do usuário
    empresas_usuario = obter_empresas_para_usuario()
    empresa = Empresa.query.get(empresa_id)
    if empresa and empresa.nome in empresas_usuario:
        return True
    
    return False

usuario_empresas = db.Table('usuario_empresas',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('empresa_id', db.Integer, db.ForeignKey('empresa.id'))
)

class Segmento(db.Model):
    """Modelo para segmentos de negócio (FUNERÁRIA, PROTEÇÃO VEICULAR, FARMÁCIA)"""
    __tablename__ = 'segmento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relacionamento com empresas (one-to-many)
    empresas = db.relationship('Empresa', backref='segmento', lazy=True)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    segmento_id = db.Column(db.Integer, db.ForeignKey('segmento.id'), nullable=True)

class Pendencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(50), nullable=False)
    tipo_pendencia = db.Column(db.String(30), nullable=False)
    banco = db.Column(db.String(50), nullable=True)
    data = db.Column(db.Date, nullable=True)  # Data da Pendência (informada pelo usuário)
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Data de Abertura (automática)
    fornecedor_cliente = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.String(300), default='DO QUE SE TRATA?')
    resposta_cliente = db.Column(db.String(300))
    email_cliente = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), default='PENDENTE CLIENTE')
    token_acesso = db.Column(db.String(100), unique=True, default=lambda: secrets.token_urlsafe(16))
    data_resposta = db.Column(db.DateTime)
    modificado_por = db.Column(db.String(50))
    nota_fiscal_arquivo = db.Column(db.String(300))  # Caminho do arquivo da nota fiscal
    natureza_operacao = db.Column(db.String(500))  # Campo para Natureza de Operação
    motivo_recusa = db.Column(db.String(500))  # Campo para motivo da recusa pelo operador
    motivo_recusa_supervisor = db.Column(db.String(500))  # Campo para motivo da recusa pelo supervisor
    # Novos campos para tipos especializados
    codigo_lancamento = db.Column(db.String(64), nullable=True)
    data_competencia = db.Column(db.Date, nullable=True)
    data_baixa = db.Column(db.Date, nullable=True)
    natureza_sistema = db.Column(db.String(120), nullable=True)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'adm', 'operador', 'cliente'
    empresas = db.relationship('Empresa', secondary=usuario_empresas, backref='usuarios')

class LogAlteracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pendencia_id = db.Column(db.Integer, db.ForeignKey('pendencia.id'), nullable=False)
    usuario = db.Column(db.String(120), nullable=False)
    tipo_usuario = db.Column(db.String(50), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    campo_alterado = db.Column(db.String(100))
    valor_anterior = db.Column(db.String(300))
    valor_novo = db.Column(db.String(300))

class Importacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(120), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    mensagem_erro = db.Column(db.String(500))

class PermissaoUsuarioTipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_usuario = db.Column(db.String(20), nullable=False)
    funcionalidade = db.Column(db.String(50), nullable=False)
    permitido = db.Column(db.Boolean, default=True)

class PermissaoUsuarioPersonalizada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    funcionalidade = db.Column(db.String(50), nullable=False)
    permitido = db.Column(db.Boolean, default=True)

def criar_usuarios_iniciais():
    if not Usuario.query.filter_by(email='adm.pendencia@up380.com.br').first():
        admin = Usuario(
            email='adm.pendencia@up380.com.br',
            senha_hash=generate_password_hash('Finance.@2'),
            tipo='adm'
        )
        db.session.add(admin)
    if not Usuario.query.filter_by(email='usuario.pendencia@up380.com.br').first():
        cliente = Usuario(
            email='usuario.pendencia@up380.com.br',
            senha_hash=generate_password_hash('Finance.@2'),
            tipo='adm'
        )
        db.session.add(admin)
    db.session.commit()

def ensure_segmento_schema():
    """Garante que a tabela segmento existe e a coluna segmento_id em empresa"""
    try:
        from sqlalchemy import text
        
        # Criar tabela segmento se não existir
        db.session.execute(text(
            """
            CREATE TABLE IF NOT EXISTS segmento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) UNIQUE NOT NULL
            )
            """
        ))

        # Verificar se coluna segmento_id existe em empresa
        info = db.session.execute(text("PRAGMA table_info(empresa)")).fetchall()
        has_segmento_id = any(row[1] == 'segmento_id' for row in info)
        
        if not has_segmento_id:
            db.session.execute(text("ALTER TABLE empresa ADD COLUMN segmento_id INTEGER"))
        
        db.session.commit()
    except Exception as e:
        print(f"[ensure_segmento_schema] Aviso: {e}")

def migrar_empresas_existentes():
    """Migra as empresas da lista EMPRESAS para o model Empresa e vincula aos segmentos"""
    
    # Estrutura completa de segmentos e empresas
    ESTRUTURA_SEGMENTOS = {
        'FUNERÁRIA': [
            'PLANO PAI', 'ECO MEMORIAL', 'PAXDOMINI', 'GRUPO COLINA', 
            'OFEBAS', 'FENIX FUNERÁRIA', 'PREDIGNA', 'ASFAP'
        ],
        'PROTEÇÃO VEICULAR': [
            'MASTER', 'ALIANZE', 'BRTRUCK', 'CANAÃ', 'COOPERATRUCK', 'ELEVAMAIS',
            'SPEED', 'RAIO', 'EXODO', 'GTA', 'MOVIDAS', 'PROTEGE ASSOCIAÇÕES',
            'TECH PROTEGE', 'UNIK', 'ARX', 'VALLE', 'CEL', 'ADMAS', 'INNOVARE',
            'AUTOBRAS', 'ANCORE', '7 MARES ASSOCIAÇÃO', 'AUTOALLIANCE',
            'ROYALE ASSOCIAÇÕES', 'ARX TRAINNING', 'ARX TECH', 'ARX ASSIST', 'YAP'
        ],
        'FARMÁCIA': ['LONGEVITÁ']
    }
    
    # Criar segmentos
    segmentos_map = {}
    for segmento_nome in ESTRUTURA_SEGMENTOS.keys():
        segmento = Segmento.query.filter_by(nome=segmento_nome).first()
        if not segmento:
            segmento = Segmento(nome=segmento_nome)
            db.session.add(segmento)
            db.session.flush()  # Para obter o ID
        segmentos_map[segmento_nome] = segmento.id
    
    # Criar e vincular empresas
    for segmento_nome, empresas_lista in ESTRUTURA_SEGMENTOS.items():
        segmento_id = segmentos_map[segmento_nome]
        for nome_empresa in empresas_lista:
            empresa = Empresa.query.filter_by(nome=nome_empresa).first()
            if not empresa:
                empresa = Empresa(nome=nome_empresa, segmento_id=segmento_id)
                db.session.add(empresa)
            elif empresa.segmento_id is None:
                empresa.segmento_id = segmento_id
    
    # Também migrar empresas da lista EMPRESAS antiga (se houver)
    for nome_empresa in EMPRESAS:
        if not Empresa.query.filter_by(nome=nome_empresa).first():
            nova_empresa = Empresa(nome=nome_empresa)
            db.session.add(nova_empresa)
    
    db.session.commit()

def obter_empresas_para_usuario():
    """
    Retorna a lista de empresas baseada no tipo de usuário e permissões.
    Para adm/supervisor: todas as empresas
    Para operador/cliente: apenas empresas permitidas
    """
    if session.get('usuario_tipo') in ['adm', 'supervisor']:
        # Admin e supervisor veem todas as empresas
        return [empresa.nome for empresa in Empresa.query.order_by(Empresa.nome).all()]
    else:
        # Operador e cliente veem apenas suas empresas permitidas
        usuario = Usuario.query.get(session.get('usuario_id'))
        if usuario and usuario.empresas:
            return [empresa.nome for empresa in usuario.empresas]
        else:
            return []

def integrar_nova_empresa(empresa):
    """
    Função automatizada para integrar uma nova empresa em todo o sistema.
    Esta função garante que a nova empresa seja automaticamente disponível
    em todos os filtros, painéis e funcionalidades do sistema.
    """
    try:
        # 1. Atualiza a lista EMPRESAS para incluir a nova empresa
        if empresa.nome not in EMPRESAS:
            EMPRESAS.append(empresa.nome)
            EMPRESAS.sort()  # Mantém a lista ordenada
        
        # 2. Registra log da integração
        log = LogAlteracao(
            pendencia_id=0,  # 0 indica que é uma alteração de sistema
            usuario=session.get('usuario_email', 'sistema'),
            tipo_usuario=session.get('usuario_tipo', 'sistema'),
            data_hora=now_brazil(),
            acao='INTEGRAR_EMPRESA',
            campo_alterado='empresa',
            valor_anterior='',
            valor_novo=empresa.nome
        )
        db.session.add(log)
        
        # 3. Notifica via Teams sobre a nova empresa
        try:
            notificar_teams_nova_empresa(empresa)
        except Exception as e:
            print(f"Erro ao notificar Teams sobre nova empresa: {e}")
        
        db.session.commit()
        
        print(f"✅ Empresa '{empresa.nome}' integrada automaticamente ao sistema")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao integrar empresa '{empresa.nome}': {e}")
        db.session.rollback()
        return False

def notificar_teams_nova_empresa(empresa):
    """Notifica o Teams sobre a criação de uma nova empresa"""
    webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        return
    
    usuario = session.get('usuario_email', 'Sistema')
    data_hora = now_brazil().strftime('%d/%m/%Y %H:%M:%S')
    
    message = {
        "text": f"🏢 **Nova Empresa Cadastrada**\n\n"
                f"**Empresa:** {empresa.nome}\n"
                f"**Cadastrada por:** {usuario}\n"
                f"**Data/Hora:** {data_hora}\n\n"
                f"✅ A empresa foi automaticamente integrada a todos os filtros e painéis do sistema."
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao enviar notificação Teams: {e}")

def obter_empresas_para_usuario():
    """
    Retorna a lista de empresas baseada no tipo de usuário e permissões.
    Para adm/supervisor: todas as empresas
    Para operador/cliente: apenas empresas permitidas
    """
    if session.get('usuario_tipo') in ['adm', 'supervisor']:
        # Admin e supervisor veem todas as empresas
        return [empresa.nome for empresa in Empresa.query.order_by(Empresa.nome).all()]
    else:
        # Operador e cliente veem apenas suas empresas permitidas
        usuario = Usuario.query.get(session.get('usuario_id'))
        if usuario and usuario.empresas:
            return [empresa.nome for empresa in usuario.empresas]
        else:
            return []

def pode_atuar_como_operador():
    """
    Verifica se o usuário atual pode atuar como operador.
    Permite que supervisor execute ações de operador.
    """
    return session.get('usuario_tipo') in ['operador', 'supervisor']

def pode_atuar_como_supervisor():
    """
    Verifica se o usuário atual pode atuar como supervisor.
    """
    return session.get('usuario_tipo') in ['adm', 'supervisor']

@app.context_processor
def inject_today_str():
    """Injeta a data de hoje em formato string em todos os templates"""
    return {
        'today_str': now_brazil().strftime('%Y-%m-%d'),
        'current_month': now_brazil().strftime('%Y-%m'),
        'now_brazil': now_brazil
    }

def enviar_email_cliente(pendencia):
    if not pendencia.email_cliente:
        return
    link = url_for('ver_pendencia', token=pendencia.token_acesso, _external=True)
    msg = Message(
        'Pendência Financeira Identificada',
        recipients=[pendencia.email_cliente]
    )
    msg.body = f"""
    Olá,

    Identificamos uma pendência no valor de R$ {pendencia.valor:.2f}.

    Por favor, acesse o link abaixo para nos informar do que se trata:
    {link}

    Obrigado,
    Equipe UP380
    """
    mail.send(msg)

def enviar_email_resposta_recusada(pendencia, motivo_recusa):
    """Envia e-mail ao cliente informando que sua resposta foi recusada"""
    if not pendencia.email_cliente:
        return
    
    link = url_for('ver_pendencia', token=pendencia.token_acesso, _external=True)
    msg = Message(
        'Resposta Recusada - Pendência Financeira',
        recipients=[pendencia.email_cliente]
    )
    msg.body = f"""
    Olá,

    Sua resposta para a pendência no valor de R$ {pendencia.valor:.2f} foi recusada.

    Motivo da recusa: {motivo_recusa}

    Por favor, acesse o link abaixo para ver sua resposta anterior e o motivo da recusa:
    {link}

    Ao reabrir o link, você verá sua resposta anterior e o motivo da recusa.

    Obrigado,
    Equipe UP380
    """
    mail.send(msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Tenta ambos os campos (senha_hash e senha) para compatibilidade
            senha_valida = False
            if hasattr(usuario, 'senha_hash'):
                senha_valida = check_password_hash(usuario.senha_hash, senha)
            elif hasattr(usuario, 'senha'):
                senha_valida = check_password_hash(usuario.senha, senha)
            
            if senha_valida:
                # Configurar sessão permanente
                session.permanent = True
                session['usuario_id'] = usuario.id
                session['usuario_email'] = usuario.email
                session['usuario_tipo'] = usuario.tipo
                
                # Log de debug (remover em produção após validar)
                print(f"[LOGIN OK] Usuário: {usuario.email} | Tipo: {usuario.tipo}")
                
                # Redirecionar para a tela de segmentos após login
                return redirect(url_for('listar_segmentos'))
        
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

def permissao_requerida(*tipos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('login'))
            if session.get('usuario_tipo') not in tipos:
                flash('Acesso não autorizado.', 'danger')
                return redirect(url_for('acesso_negado'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# ROTAS DE SEGMENTOS - NAVEGAÇÃO HIERÁRQUICA
# ============================================================================

@app.route('/segmentos')
@app.route('/')  # Rota raiz também vai para segmentos
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def listar_segmentos():
    """
    Tela principal - exibe cards de todos os segmentos
    Filtra segmentos conforme acesso às empresas do usuário
    """
    # Segmentos disponíveis conforme acesso às empresas
    if session.get('usuario_tipo') in ['adm', 'supervisor']:
        segmentos = Segmento.query.order_by(Segmento.nome).all()
    else:
        usuario = Usuario.query.get(session['usuario_id'])
        segmentos_ids = {emp.segmento_id for emp in (usuario.empresas or []) if emp.segmento_id}
        if segmentos_ids:
            segmentos = Segmento.query.filter(Segmento.id.in_(segmentos_ids)).order_by(Segmento.nome).all()
        else:
            segmentos = []

    # Contar empresas e pendências por segmento
    resumo = []
    empresas_disponiveis = obter_empresas_para_usuario()
    
    for seg in segmentos:
        empresas_seg = [e for e in (seg.empresas or []) if e.nome in empresas_disponiveis]
        
        # Contar pendências abertas no segmento
        total_abertas = 0
        for empresa in empresas_seg:
            pendencias_abertas = Pendencia.query.filter(
                Pendencia.empresa == empresa.nome,
                Pendencia.status != 'RESOLVIDA'
            ).count()
            total_abertas += pendencias_abertas
        
        resumo.append({
            'id': seg.id,
            'nome': seg.nome,
            'total_empresas': len(empresas_seg),
            'total_abertas': total_abertas
        })
    
    return render_template('segmentos.html', segmentos=resumo)

@app.route('/segmento/<int:id>')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def empresas_por_segmento(id):
    """
    Exibe todas as empresas de um segmento específico
    Com contadores de pendências abertas e resolvidas por empresa
    """
    segmento = Segmento.query.get_or_404(id)
    empresas_disponiveis = obter_empresas_para_usuario()
    empresas = [e for e in (segmento.empresas or []) if e.nome in empresas_disponiveis]

    empresas_info = []
    for empresa in empresas:
        # Contar pendências
        pendencias_total = Pendencia.query.filter(Pendencia.empresa == empresa.nome).all()
        pendencias_abertas = [p for p in pendencias_total if p.status != 'RESOLVIDA']
        pendencias_resolvidas = [p for p in pendencias_total if p.status == 'RESOLVIDA']
        
        empresas_info.append({
            'id': empresa.id,
            'nome': empresa.nome,
            'abertas': len(pendencias_abertas),
            'resolvidas': len(pendencias_resolvidas)
        })
    
    # Obter mês atual para relatório mensal
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    
    return render_template(
        'empresas_por_segmento.html', 
        segmento=segmento, 
        empresas_info=empresas_info,
        current_month=current_month,
        current_user_tipo=session.get('usuario_tipo')
    )

@app.route('/empresa/<int:id>')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def empresa_redirect(id):
    """
    Redireciona para o dashboard de pendências da empresa
    Valida se o usuário tem acesso à empresa
    """
    empresa = Empresa.query.get_or_404(id)
    
    # Validar acesso
    if empresa.nome not in obter_empresas_para_usuario():
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('acesso_negado'))
    
    return redirect(url_for('dashboard', empresa=empresa.nome))

# ============================================================================
# FIM DAS ROTAS DE SEGMENTOS
# ============================================================================

@app.route('/empresas')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def pre_dashboard():
    from datetime import datetime, timedelta
    
    # Obter filtros de data da URL
    data_abertura_inicio = request.args.get('data_abertura_inicio', '')
    data_abertura_fim = request.args.get('data_abertura_fim', '')
    data_resolucao_inicio = request.args.get('data_resolucao_inicio', '')
    data_resolucao_fim = request.args.get('data_resolucao_fim', '')
    
    if session.get('usuario_tipo') == 'adm':
        empresas = Empresa.query.all()
    else:
        usuario = Usuario.query.get(session['usuario_id'])
        empresas = usuario.empresas
    
    empresas_info = []
    tipo_counts = {}
    abertas_count = 0
    resolvidas_count = 0
    
    for empresa in empresas:
        # Query base
        query = Pendencia.query.filter(Pendencia.empresa == empresa.nome)
        
        # Aplicar filtros de data de abertura
        if data_abertura_inicio:
            try:
                data_inicio = datetime.strptime(data_abertura_inicio, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_abertura >= data_inicio)
            except:
                pass
        
        if data_abertura_fim:
            try:
                data_fim = datetime.strptime(data_abertura_fim, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_abertura <= data_fim)
            except:
                pass
        
        # Aplicar filtros de data de resolução
        if data_resolucao_inicio:
            try:
                data_inicio = datetime.strptime(data_resolucao_inicio, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_resolucao >= data_inicio)
            except:
                pass
        
        if data_resolucao_fim:
            try:
                data_fim = datetime.strptime(data_resolucao_fim, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_resolucao <= data_fim)
            except:
                pass
        
        pendencias = query.all()
        pendencias_abertas = [p for p in pendencias if p.status != 'RESOLVIDA']
        
        empresas_info.append({
            'id': empresa.id,
            'nome': empresa.nome,
            'abertas': len(pendencias_abertas)
        })
        
        # Contar por tipo e status
        for p in pendencias:
            # Contar por tipo
            if p.tipo_pendencia not in tipo_counts:
                tipo_counts[p.tipo_pendencia] = 0
            tipo_counts[p.tipo_pendencia] += 1
            
            # Contar abertas vs resolvidas
            if p.status == 'RESOLVIDA':
                resolvidas_count += 1
            else:
                abertas_count += 1
    
    # Preparar dados para os gráficos
    tipos_labels = list(tipo_counts.keys())
    tipos_valores = list(tipo_counts.values())
    
    today_str = now_brazil().strftime('%Y-%m-%d')
    current_month = now_brazil().strftime('%Y-%m')
    
    return render_template(
        'pre_dashboard.html',
        empresas_info=empresas_info,
        tipos_labels=tipos_labels,
        tipos_valores=tipos_valores,
        abertas_count=abertas_count,
        resolvidas_count=resolvidas_count,
        data_abertura_inicio=data_abertura_inicio,
        data_abertura_fim=data_abertura_fim,
        data_resolucao_inicio=data_resolucao_inicio,
        data_resolucao_fim=data_resolucao_fim,
        today_str=today_str,
        current_month=current_month
    )

@app.route('/api/dados_graficos')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente_supervisor')
def api_dados_graficos():
    """Retorna dados dos gráficos em JSON"""
    from datetime import datetime
    from flask import jsonify
    
    # Obter filtros de data da URL
    data_abertura_inicio = request.args.get('data_abertura_inicio', '')
    data_abertura_fim = request.args.get('data_abertura_fim', '')
    data_resolucao_inicio = request.args.get('data_resolucao_inicio', '')
    data_resolucao_fim = request.args.get('data_resolucao_fim', '')
    
    if session.get('usuario_tipo') == 'adm':
        empresas = Empresa.query.all()
    else:
        usuario = Usuario.query.get(session['usuario_id'])
        empresas = usuario.empresas
    
    tipo_counts = {}
    abertas_count = 0
    resolvidas_count = 0
    
    for empresa in empresas:
        query = Pendencia.query.filter(Pendencia.empresa == empresa.nome)
        
        if data_abertura_inicio:
            try:
                data_inicio = datetime.strptime(data_abertura_inicio, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_abertura >= data_inicio)
            except:
                pass
        
        if data_abertura_fim:
            try:
                data_fim = datetime.strptime(data_abertura_fim, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_abertura <= data_fim)
            except:
                pass
        
        if data_resolucao_inicio:
            try:
                data_inicio = datetime.strptime(data_resolucao_inicio, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_resolucao >= data_inicio)
            except:
                pass
        
        if data_resolucao_fim:
            try:
                data_fim = datetime.strptime(data_resolucao_fim, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_resolucao <= data_fim)
            except:
                pass
        
        pendencias = query.all()
        
        for p in pendencias:
            if p.tipo_pendencia not in tipo_counts:
                tipo_counts[p.tipo_pendencia] = 0
            tipo_counts[p.tipo_pendencia] += 1
            
            if p.status == 'RESOLVIDA':
                resolvidas_count += 1
            else:
                abertas_count += 1
    
    return jsonify({
        'tipos': list(tipo_counts.keys()),
        'valores': list(tipo_counts.values()),
        'abertas': abertas_count,
        'resolvidas': resolvidas_count
    })

@app.route('/dashboard', methods=['GET'])
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def dashboard():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    empresa_filtro = request.args.get('empresa', empresas_usuario[0])
    tipo_filtro = request.args.get('tipo_pendencia', TIPOS_PENDENCIA[0])
    busca = request.args.get('busca', '')
    
    # Filtra pendências não resolvidas (incluindo os novos status)
    pendencias_empresa = Pendencia.query.filter_by(empresa=empresa_filtro).filter(
        Pendencia.status.notin_(['RESOLVIDA'])
    ).all()
    
    query = Pendencia.query.filter_by(empresa=empresa_filtro, tipo_pendencia=tipo_filtro).filter(
        Pendencia.status.notin_(['RESOLVIDA'])
    )
    
    if busca:
        query = query.filter(
            db.or_(Pendencia.fornecedor_cliente.ilike(f'%{busca}%'),
                Pendencia.banco.ilike(f'%{busca}%'),
                    Pendencia.observacao.ilike(f'%{busca}%'),
                    Pendencia.resposta_cliente.ilike(f'%{busca}%'),
                    Pendencia.natureza_operacao.ilike(f'%{busca}%'))
            )
    
    pendencias = query.order_by(Pendencia.data.desc()).all()
    
    # Obter empresa para o relatório
    empresa_obj = Empresa.query.filter_by(nome=empresa_filtro).first()
    empresa_id = empresa_obj.id if empresa_obj else None
    today_str = now_brazil().strftime('%Y-%m-%d')
    current_month = now_brazil().strftime('%Y-%m')
    
    # Obter segmento da empresa para o breadcrumb
    segmento_nome = None
    segmento_id = None
    if empresa_obj and empresa_obj.segmento_id:
        segmento = Segmento.query.get(empresa_obj.segmento_id)
        if segmento:
            segmento_nome = segmento.nome
            segmento_id = segmento.id
    
    # Obter colunas específicas para o tipo selecionado
    colunas_tipo = obter_colunas_por_tipo(tipo_filtro)
    todas_colunas = obter_todas_colunas()
    
    # Buscar respostas anteriores para pendências com status PENDENTE COMPLEMENTO CLIENTE
    respostas_anteriores = {}
    if session.get('usuario_tipo') == 'cliente':
        for pendencia in pendencias:
            if pendencia.status == 'PENDENTE COMPLEMENTO CLIENTE':
                # Busca a última resposta do cliente nos logs
                ultima_resposta = (
                    LogAlteracao.query
                    .filter_by(pendencia_id=pendencia.id, campo_alterado="resposta_cliente")
                    .order_by(LogAlteracao.data_hora.desc())
                    .first()
                )
                if ultima_resposta:
                    respostas_anteriores[pendencia.id] = ultima_resposta
    
    return render_template(
        'dashboard.html', 
        pendencias=pendencias, 
        pendencias_empresa=pendencias_empresa, 
        empresas=empresas_usuario, 
        empresa_filtro=empresa_filtro, 
        tipos_pendencia=TIPOS_PENDENCIA, 
        tipo_filtro=tipo_filtro, 
        busca=busca,
        empresa_id=empresa_id,
        today_str=today_str,
        current_month=current_month,
        colunas_tipo=colunas_tipo,
        todas_colunas=todas_colunas,
        respostas_anteriores=respostas_anteriores,
        segmento_nome=segmento_nome,
        segmento_id=segmento_id
    )

@app.route('/nova', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
def nova_pendencia():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    # Obter empresa pré-selecionada da query string
    empresa_preselecionada = request.args.get('empresa')
    preselect_empresa = None
    
    # Validar se a empresa pré-selecionada está na lista de empresas do usuário
    if empresa_preselecionada and empresa_preselecionada in empresas_usuario:
        preselect_empresa = empresa_preselecionada
    
    if request.method == 'POST':
        try:
            empresa = request.form['empresa']
            tipo_pendencia = request.form['tipo_pendencia']
            banco = request.form.get('banco', '')
            
            # Preparar payload para validação
            payload = {
                'tipo_pendencia': tipo_pendencia,
                'empresa': empresa,
                'banco': banco,
                'fornecedor_cliente': request.form.get('fornecedor_cliente', ''),
                'valor': request.form.get('valor', ''),
                'codigo_lancamento': request.form.get('codigo_lancamento', ''),
                'data': request.form.get('data', ''),
                'data_competencia': request.form.get('data_competencia', ''),
                'data_baixa': request.form.get('data_baixa', ''),
                'observacao': request.form.get('observacao', ''),
                'natureza_sistema': request.form.get('natureza_sistema', '')
            }
            
            # Validar por tipo
            is_valid, error_msg = validar_por_tipo(payload)
            if not is_valid:
                flash(f'Erro de validação: {error_msg}', 'danger')
                return redirect(url_for('nova_pendencia'))
            
            # Tratar Data da Pendência (pode ser NULL para "Nota Fiscal Não Identificada")
            data_pendencia = request.form.get('data')
            if tipo_pendencia == 'Nota Fiscal Não Identificada':
                data_value = None
            else:
                data_value = datetime.strptime(data_pendencia, '%Y-%m-%d').date() if data_pendencia else None
            
            # Tratar Data Competência
            data_competencia_value = None
            if request.form.get('data_competencia'):
                data_competencia_value = datetime.strptime(request.form.get('data_competencia'), '%Y-%m-%d').date()
            
            # Tratar Data Baixa
            data_baixa_value = None
            if request.form.get('data_baixa'):
                data_baixa_value = datetime.strptime(request.form.get('data_baixa'), '%Y-%m-%d').date()
            
            fornecedor_cliente = request.form['fornecedor_cliente']
            valor = parse_currency_to_float(request.form['valor'])
            observacao = request.form.get('observacao') or 'DO QUE SE TRATA?'
            email_cliente = request.form.get('email_cliente')
            codigo_lancamento = request.form.get('codigo_lancamento', '')
            natureza_sistema = request.form.get('natureza_sistema', '')
            
            nota_fiscal_arquivo = None
            if tipo_pendencia == 'Nota Fiscal Não Anexada' and 'nota_fiscal_arquivo' in request.files:
                file = request.files['nota_fiscal_arquivo']
                if file and file.filename:
                    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                    file.save(os.path.join('static/notas_fiscais', filename))
                    nota_fiscal_arquivo = filename
            
            # Validar se o usuário tem acesso à empresa selecionada
            if empresa not in empresas_usuario:
                flash('Você não tem acesso a esta empresa.', 'danger')
                return redirect(url_for('nova_pendencia'))
            
            nova_p = Pendencia(
                empresa=empresa,
                tipo_pendencia=tipo_pendencia,
                banco=banco,
                data=data_value,  # Data da Pendência (pode ser NULL)
                data_abertura=datetime.utcnow(),  # Data de Abertura (automática)
                fornecedor_cliente=fornecedor_cliente,
                valor=valor,
                observacao=observacao,
                email_cliente=email_cliente,
                status='PENDENTE CLIENTE',
                nota_fiscal_arquivo=nota_fiscal_arquivo,
                # Novos campos especializados
                codigo_lancamento=codigo_lancamento,
                data_competencia=data_competencia_value,
                data_baixa=data_baixa_value,
                natureza_sistema=natureza_sistema
            )
            db.session.add(nova_p)
            db.session.commit()
            
            # Log da criação da pendência
            log = LogAlteracao(
                pendencia_id=nova_p.id,
                usuario=session.get('usuario_email', 'Sistema'),
                tipo_usuario=session.get('usuario_tipo', 'sistema'),
                data_hora=now_brazil(),
                acao='Criação de Pendência',
                campo_alterado='empresa',
                valor_anterior='',
                valor_novo=empresa
            )
            db.session.add(log)
            db.session.commit()
            
            enviar_email_cliente(nova_p)
            flash('Pendência criada com sucesso!', 'success')
            # Redireciona para o painel correto já filtrado pela empresa
            if session.get('usuario_tipo') == 'supervisor':
                return redirect(url_for('supervisor_pendencias', empresa=empresa))
            else:
                return redirect(url_for('operador_pendencias', empresa=empresa))
        except Exception as e:
            flash(f'Erro ao criar pendência: {str(e)}', 'error')
            return redirect(url_for('nova_pendencia'))
    
    return render_template('nova_pendencia.html', 
                         empresas=empresas_usuario, 
                         tipos_pendencia=TIPOS_PENDENCIA,
                         preselect_empresa=preselect_empresa)

@app.route('/pendencia/<token>', methods=['GET', 'POST'])
def ver_pendencia(token):
    pendencia = Pendencia.query.filter_by(token_acesso=token).first_or_404()
    
    # Consulta da última resposta do cliente (apenas se status for PENDENTE CLIENTE e houver motivo_recusa)
    ultima_resposta = None
    historico_respostas = []
    
    if pendencia.status == 'PENDENTE CLIENTE' and (pendencia.motivo_recusa or pendencia.resposta_cliente):
        # Busca a última resposta do cliente nos logs
        ultima_resposta = (
            LogAlteracao.query
            .filter_by(pendencia_id=pendencia.id, campo_alterado="resposta_cliente")
            .order_by(LogAlteracao.data_hora.desc())
            .first()
        )
        
        # Busca histórico completo de respostas
        historico_respostas = (
            LogAlteracao.query
            .filter_by(pendencia_id=pendencia.id, campo_alterado="resposta_cliente")
            .order_by(LogAlteracao.data_hora.desc())
            .all()
        )
    
    if request.method == 'POST':
        # Verifica se é complemento de resposta ou resposta inicial
        # Inicializar variável resposta_anterior
        resposta_anterior = pendencia.resposta_cliente or ''
        
        if pendencia.status == 'PENDENTE COMPLEMENTO CLIENTE':
            # Complemento de resposta
            resposta_atual = pendencia.resposta_cliente or ''
            complemento = request.form['resposta']
            pendencia.resposta_cliente = f"{resposta_atual}\n\n--- COMPLEMENTO ---\n{complemento}"
            pendencia.motivo_recusa = None  # Limpa o motivo da recusa
            acao_log = 'Complemento de Resposta do Cliente'
            valor_anterior = 'PENDENTE COMPLEMENTO CLIENTE'
            valor_novo = 'PENDENTE OPERADOR UP'
        else:
            # Resposta inicial
            pendencia.resposta_cliente = request.form['resposta']
            acao_log = 'Resposta do Cliente'
            valor_anterior = 'Pendente Cliente'
            valor_novo = 'PENDENTE OPERADOR UP'
        
        # Upload de anexo pelo cliente (permitido para qualquer tipo de pendência)
        if 'nota_fiscal_arquivo' in request.files:
            file = request.files['nota_fiscal_arquivo']
            if file and file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join('static/notas_fiscais', filename))
                pendencia.nota_fiscal_arquivo = filename
        
        # Atualiza status
        pendencia.status = 'PENDENTE OPERADOR UP'
        pendencia.data_resposta = now_brazil()
        db.session.commit()
        
        # Log da alteração de status
        log_status = LogAlteracao(
            pendencia_id=pendencia.id,
            usuario='Cliente',
            tipo_usuario='cliente',
            data_hora=now_brazil(),
            acao=acao_log,
            campo_alterado='status',
            valor_anterior=valor_anterior,
            valor_novo=valor_novo
        )
        db.session.add(log_status)
        
        # Log da resposta do cliente
        log_resposta = LogAlteracao(
            pendencia_id=pendencia.id,
            usuario='Cliente',
            tipo_usuario='cliente',
            data_hora=now_brazil(),
            acao='update',
            campo_alterado='resposta_cliente',
            valor_anterior=resposta_anterior or '',
            valor_novo=pendencia.resposta_cliente
        )
        db.session.add(log_resposta)
        db.session.commit()
        
        # Notificação Teams
        notificar_teams_pendente_operador(pendencia)
        
        if pendencia.status == 'PENDENTE COMPLEMENTO CLIENTE':
            flash('Complemento enviado com sucesso!', 'success')
        else:
            flash('Resposta enviada com sucesso!', 'success')
        
        empresa = request.form.get('empresa', pendencia.empresa)
        tipo_pendencia = request.form.get('tipo_pendencia', pendencia.tipo_pendencia)
        busca = request.form.get('busca', '')
        return redirect(url_for('dashboard', empresa=empresa, tipo_pendencia=tipo_pendencia, busca=busca))
    
    return render_template('ver_pendencia.html', 
                         pendencia=pendencia,
                         motivo_recusa=pendencia.motivo_recusa,
                         ultima_resposta=ultima_resposta,
                         historico_respostas=historico_respostas)

@app.route('/resolver/<int:id>')
@permissao_requerida('supervisor', 'adm')
def resolver_pendencia(id):
    pendencia = Pendencia.query.get_or_404(id)
    valor_anterior = pendencia.status
    pendencia.status = 'RESOLVIDA'
    pendencia.modificado_por = 'ADIMIN UP380'
    db.session.commit()
    # Log da resolução
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'ADIMIN UP380'),
        tipo_usuario='admin',
        data_hora=now_brazil(),
        acao='Resolução de Pendência',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='Resolvida'
    )
    db.session.add(log)
    db.session.commit()
    flash('Pendência marcada como resolvida!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/baixar_modelo')
def baixar_modelo():
    tipo = request.args.get('tipo', 'Cartão de Crédito Não Identificado')
    empresa = request.args.get('empresa', 'ALIANZE')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pendências'
    ws.append(['EMPRESA', 'TIPO DE PENDÊNCIA', 'BANCO', 'DATA DE COMPETÊNCIA', 'FORNECEDOR/CLIENTE', 'VALOR', 'OBSERVAÇÃO'])
    ws.append([empresa, tipo, 'SICREDI', '24/03/2025', 'E A R PEREIRA COMBUSTIVEIS LTDA', '150,00', 'DO QUE SE TRATA?'])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"modelo_{tipo.replace(' ', '_')}_{empresa.replace(' ', '_')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route("/import/modelo", methods=["GET"])
@permissao_requerida('supervisor', 'adm', 'operador')
def download_modelo_pendencias():
    """
    Serve a planilha modelo específica para cada tipo de pendência
    Uma planilha individual por tipo, formatada e com exemplo
    """
    import os
    
    # Obter tipo da pendência
    tipo = request.args.get('tipo', '').upper()
    
    # Mapeamento: tipo (como vem do template) → nome do arquivo
    # IMPORTANTE: Mapeamento baseado em TIPO_RULES - campos EXATOS!
    mapeamento_arquivos = {
        'NATUREZA_ERRADA': 'modelo_natureza_errada.xlsx',
        'COMPETENCIA_ERRADA': 'modelo_competencia_errada.xlsx',
        'DATA_BAIXA_ERRADA': 'modelo_data_da_baixa_errada.xlsx',
        'CARTAO_NAO_IDENTIFICADO': 'modelo_cartao_de_credito_nao_identificado.xlsx',
        'PAGAMENTO_NAO_IDENTIFICADO': 'modelo_pagamento_nao_identificado.xlsx',
        'RECEBIMENTO_NAO_IDENTIFICADO': 'modelo_recebimento_nao_identificado.xlsx',
        'DOCUMENTO_NAO_ANEXADO': 'modelo_documento_nao_anexado.xlsx',
        'LANCAMENTO_NAO_ENCONTRADO_EXTRATO': 'modelo_lancamento_nao_encontrado_em_extrato.xlsx',
        'LANCAMENTO_NAO_ENCONTRADO_SISTEMA': 'modelo_lancamento_nao_encontrado_em_sistema.xlsx'
    }
    
    # Obter nome do arquivo
    nome_arquivo = mapeamento_arquivos.get(tipo)
    
    if not nome_arquivo:
        flash(f'Tipo de modelo inválido: {tipo}', 'error')
        return redirect(url_for('importar_planilha'))
    
    # Caminho completo do arquivo
    arquivo_modelo = os.path.join(os.getcwd(), nome_arquivo)
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo_modelo):
        flash(f'Arquivo modelo não encontrado: {nome_arquivo}. Contate o administrador.', 'error')
        return redirect(url_for('importar_planilha'))
    
    # Servir o arquivo
    try:
        return send_file(
            arquivo_modelo,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Erro ao baixar modelo: {str(e)}', 'error')
        return redirect(url_for('importar_planilha'))

@app.route('/importar', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
def importar_planilha():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    # Verificar se veio de uma empresa específica
    empresa_contexto = request.args.get('empresa')
    empresa_id_contexto = None
    if empresa_contexto:
        empresa_obj = Empresa.query.filter_by(nome=empresa_contexto).first()
        if empresa_obj:
            empresa_id_contexto = empresa_obj.id
    
    preview = None
    erros = []
    if request.method == 'POST':
        if request.form.get('confirmar_importacao') == '1' and 'preview_data' in session and 'preview_filename' in session:
            # Segunda etapa: confirmar importação usando dados em sessão
            try:
                df = pd.read_json(session['preview_data'])
                tipo_import = session.get('tipo_import')
                empresa_id_ctx = session.get('empresa_id_contexto')
                ts_lote = datetime.utcnow()
                
                for idx, row in df.iterrows():
                    # Processar linha conforme tipo
                    r = {k: str(row.get(k, "")).strip() for k in df.columns}
                    
                    # Empresa
                    if empresa_id_ctx:
                        empresa = Empresa.query.get(empresa_id_ctx)
                    else:
                        empresa = Empresa.query.filter_by(nome=r.get("empresa")).first()
                    
                    if not empresa or not usuario_tem_acesso(session.get('usuario_email'), empresa.id):
                        continue
                    
                    # Mapear campos
                    fornecedor_nome = pick(r.get("fornecedor_id"), r.get("fornecedor"))
                    banco_nome = pick(r.get("banco_id"), r.get("banco"))
                    
                    # Para tipos que não precisam de banco, definir como string vazia
                    if label_tipo_planilha(tipo_import) in ["Natureza Errada", "Competência Errada"]:
                        banco_nome = ""  # String vazia em vez de None
                    
                    # Criar pendência
                    nova_p = Pendencia(
                        empresa=empresa.nome,
                        tipo_pendencia=label_tipo_planilha(tipo_import),
                        fornecedor_cliente=fornecedor_nome or "",
                        valor=parse_currency_to_float(r.get("valor", "0")),
                        codigo_lancamento=r.get("codigo_lancamento") or "",
                        natureza_sistema=r.get("natureza_sistema") or "",
                        data=parse_date_or_none(r.get("data")),
                        data_competencia=parse_date_or_none(r.get("data_competencia")),
                        data_baixa=parse_date_or_none(r.get("data_baixa")),
                        banco=banco_nome or "",
                        observacao=r.get("observacao") or "",
                        email_cliente=r.get("email_cliente") or "",
                        status='PENDENTE CLIENTE',
                        data_abertura=ts_lote
                    )
                    db.session.add(nova_p)
                
                db.session.commit()
                
                # Log de importação
                imp = Importacao(
                    nome_arquivo=session['preview_filename'],
                    usuario=session.get('usuario_email', 'admin'),
                    data_hora=now_brazil(),
                    status='Sucesso',
                    mensagem_erro=None
                )
                db.session.add(imp)
                db.session.commit()
                
                session.pop('preview_data', None)
                session.pop('preview_filename', None)
                session.pop('tipo_import', None)
                session.pop('empresa_id_contexto', None)
                
                flash('Pendências importadas com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                erros.append(f'Erro ao importar: {e}')
        else:
            file = request.files.get('arquivo')
            tipo_import = request.form.get('tipo_import')
            empresa_id_ctx = request.form.get('empresa_id', type=int)
            
            if not file or not tipo_import:
                flash('Arquivo e tipo são obrigatórios.', 'error')
                return render_template('importar_planilha.html', empresas=empresas_usuario, preview=preview, erros=erros, empresa_id_contexto=empresa_id_contexto)
            
            try:
                # Ler xlsx
                df = pd.read_excel(file, dtype=str).fillna("")
                errors, rows_ok = [], []
                ts_lote = datetime.utcnow()
                
                for i, row in df.iterrows():
                    r = {k: str(row.get(k, "")).strip() for k in df.columns}
                    msg = validar_row_por_tipo(label_tipo_planilha(tipo_import), r)
                    if msg:
                        errors.append({"linha": i+2, "erro": msg})
                        continue
                    
                    # Empresa
                    if empresa_id_ctx:
                        empresa = Empresa.query.get(empresa_id_ctx)
                    else:
                        empresa = Empresa.query.filter_by(nome=r.get("empresa")).first()
                    
                    if not empresa or not usuario_tem_acesso(session.get('usuario_email'), empresa.id):
                        errors.append({"linha": i+2, "erro": "Empresa inválida ou sem permissão"})
                        continue
                    
                    # Mapear campos
                    fornecedor_nome = pick(r.get("fornecedor_id"), r.get("fornecedor"))
                    banco_nome = pick(r.get("banco_id"), r.get("banco"))
                    
                    # Para tipos que não precisam de banco, definir como string vazia
                    if label_tipo_planilha(tipo_import) in ["NATUREZA ERRADA", "COMPETÊNCIA ERRADA"]:
                        banco_nome = ""  # String vazia em vez de None
                    
                    # Garantir que campos obrigatórios não sejam nulos
                    tipo_pendencia = label_tipo_planilha(tipo_import)
                    rule = TIPO_RULES.get(tipo_pendencia, {})
                    
                    # DEBUG: Log dos dados da linha
                    print(f"DEBUG - Linha {i+2}: tipo={tipo_pendencia}, data_raw={r.get('data')}, required={rule.get('required', [])}")
                    
                    # Tratar campos de data obrigatórios
                    data_value = parse_date_or_none(r.get("data"))
                    data_competencia_value = parse_date_or_none(r.get("data_competencia"))
                    data_baixa_value = parse_date_or_none(r.get("data_baixa"))
                    
                    # DEBUG: Log dos valores parseados
                    print(f"DEBUG - data_value={data_value}, data_competencia_value={data_competencia_value}, data_baixa_value={data_baixa_value}")
                    
                    # Se data é obrigatória mas está None, usar data atual como fallback
                    if "data" in rule.get("required", []) and not data_value:
                        data_value = datetime.now().date()
                        print(f"DEBUG - Aplicando fallback para data: {data_value}")
                    
                    # Se data_competencia é obrigatória mas está None, usar data atual como fallback
                    if "data_competencia" in rule.get("required", []) and not data_competencia_value:
                        data_competencia_value = datetime.now().date()
                        print(f"DEBUG - Aplicando fallback para data_competencia: {data_competencia_value}")
                    
                    # Se data_baixa é obrigatória mas está None, usar data atual como fallback
                    if "data_baixa" in rule.get("required", []) and not data_baixa_value:
                        data_baixa_value = datetime.now().date()
                        print(f"DEBUG - Aplicando fallback para data_baixa: {data_baixa_value}")
                    
                    # Garantir que fornecedor_cliente não seja vazio se obrigatório
                    fornecedor_final = fornecedor_nome or ""
                    if "fornecedor_cliente" in rule.get("required", []) and not fornecedor_final:
                        fornecedor_final = "FORNECEDOR NÃO INFORMADO"
                    
                    # Garantir que banco não seja vazio se obrigatório
                    banco_final = banco_nome or ""
                    if "banco" in rule.get("required", []) and not banco_final:
                        banco_final = "BANCO NÃO INFORMADO"
                    
                    # Garantir que codigo_lancamento não seja vazio se obrigatório
                    codigo_final = r.get("codigo_lancamento") or ""
                    if "codigo_lancamento" in rule.get("required", []) and not codigo_final:
                        codigo_final = "CÓDIGO NÃO INFORMADO"
                    
                    # VALIDAÇÃO FINAL: Garantir que campos obrigatórios não sejam None
                    # Para tipos que requerem data, garantir que nunca seja None
                    if tipo_pendencia in ["Recebimento Não Identificado", "Pagamento Não Identificado", "Cartão de Crédito Não Identificado", "Nota Fiscal Não Anexada", "Natureza Errada"]:
                        if data_value is None:
                            data_value = datetime.now().date()
                            print(f"DEBUG - FORÇANDO data para {tipo_pendencia}: {data_value}")
                    
                    if "data_competencia" in rule.get("required", []) and data_competencia_value is None:
                        data_competencia_value = datetime.now().date()
                        print(f"DEBUG - VALIDAÇÃO FINAL: data_competencia estava None, aplicando fallback: {data_competencia_value}")
                    
                    if "data_baixa" in rule.get("required", []) and data_baixa_value is None:
                        data_baixa_value = datetime.now().date()
                        print(f"DEBUG - VALIDAÇÃO FINAL: data_baixa estava None, aplicando fallback: {data_baixa_value}")
                    
                    # DEBUG: Log final dos valores
                    print(f"DEBUG - VALORES FINAIS: data={data_value}, data_competencia={data_competencia_value}, data_baixa={data_baixa_value}")
                    
                    p = Pendencia(
                        empresa=empresa.nome,
                        tipo_pendencia=tipo_pendencia,
                        fornecedor_cliente=fornecedor_final,
                        valor=parse_currency_to_float(r.get("valor", "0")),
                        codigo_lancamento=codigo_final,
                        natureza_sistema=r.get("natureza_sistema") or "",
                        data=data_value,
                        data_competencia=data_competencia_value,
                        data_baixa=data_baixa_value,
                        banco=banco_final,
                        observacao=r.get("observacao") or "",
                        email_cliente=r.get("email_cliente") or "",
                        status='PENDENTE CLIENTE',
                        data_abertura=ts_lote
                    )
                    rows_ok.append(p)
                
                # Preview se houver erros
                if errors:
                    preview = df.head(5).to_dict(orient='records')
                    erros = [f"Linha {e['linha']}: {e['erro']}" for e in errors]
                else:
                    # Salvar dados em sessão para confirmação
                    session['preview_data'] = df.to_json()
                    session['preview_filename'] = file.filename
                    session['tipo_import'] = tipo_import
                    session['empresa_id_contexto'] = empresa_id_ctx
                    preview = df.head(5).to_dict(orient='records')
                    
            except Exception as e:
                erros.append(f'Erro ao processar arquivo: {e}')
    
    return render_template('importar_planilha.html', 
                         empresas=empresas_usuario, 
                         preview=preview, 
                         erros=erros, 
                         empresa_id_contexto=empresa_id_contexto,
                         tipos_importacao=TIPO_IMPORT_MAP.keys())

@app.route('/historico_importacoes')
@permissao_requerida('supervisor', 'adm', 'operador')
def historico_importacoes():
    historico = Importacao.query.order_by(Importacao.data_hora.desc()).limit(20).all()
    return render_template('historico_importacoes.html', historico=historico)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_pendencia(id):
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    if pendencia.resposta_cliente:
        flash('Não é possível editar uma pendência já respondida pelo cliente.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        campos = ['empresa', 'tipo_pendencia', 'banco', 'data', 'fornecedor_cliente', 'valor', 'observacao', 'email_cliente']
        valores_anteriores = {campo: getattr(pendencia, campo) for campo in campos}
        novos_valores = {
            'empresa': request.form['empresa'],
            'tipo_pendencia': request.form['tipo_pendencia'],
            'banco': request.form['banco'],
            'data': datetime.strptime(request.form['data'], '%Y-%m-%d').date(),
            'fornecedor_cliente': request.form['fornecedor_cliente'],
            'valor': parse_currency_to_float(request.form['valor']),
            'observacao': request.form.get('observacao') or 'DO QUE SE TRATA?',
            'email_cliente': request.form.get('email_cliente')
        }
        for campo in campos:
            if valores_anteriores[campo] != novos_valores[campo]:
                log = LogAlteracao(
                    pendencia_id=pendencia.id,
                    usuario=session.get('usuario_email', 'ADIMIN UP380'),
                    tipo_usuario='admin',
                    data_hora=now_brazil(),
                    acao='Edição de Pendência',
                    campo_alterado=campo,
                    valor_anterior=str(valores_anteriores[campo]),
                    valor_novo=str(novos_valores[campo])
                )
                db.session.add(log)
        pendencia.empresa = novos_valores['empresa']
        pendencia.tipo_pendencia = novos_valores['tipo_pendencia']
        pendencia.banco = novos_valores['banco']
        pendencia.data = novos_valores['data']
        pendencia.fornecedor_cliente = novos_valores['fornecedor_cliente']
        pendencia.valor = novos_valores['valor']
        pendencia.observacao = novos_valores['observacao']
        pendencia.email_cliente = novos_valores['email_cliente']
        # Upload de nota fiscal
        if pendencia.tipo_pendencia == 'Nota Fiscal Não Anexada' and 'nota_fiscal_arquivo' in request.files:
            file = request.files['nota_fiscal_arquivo']
            if file and file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join('static/notas_fiscais', filename))
                pendencia.nota_fiscal_arquivo = filename
        pendencia.modificado_por = 'ADIMIN UP380'
        db.session.commit()
        flash('Pendência editada com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editar_pendencia.html', pendencia=pendencia, empresas=empresas_usuario, tipos_pendencia=TIPOS_PENDENCIA)

TEAMS_WEBHOOK_URL = "https://upfinance.webhook.office.com/webhookb2/7c8dacfa-6413-4b34-9659-5be33e876493@62d96e16-cfeb-4bad-8803-4a764ac7339a/IncomingWebhook/a6612b3a144d4915bf9bc1171093c8c9/9cdf59ae-5ee6-4c43-8604-31390b2d5425/V21glDBnmGcX-HxLgk_gJxnhqHC79TV9BLey3t5_DzMbU1"

def notificar_teams(pendencia):
    webhook_url = TEAMS_WEBHOOK_URL
    if not webhook_url:
        return
    mensagem = {
        "title": "Pendência Atualizada pelo Cliente",
        "text": (
            f"O cliente <b>USUARIO</b> informou sobre a pendência <b>ID {pendencia.id}</b>:<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Observação:</b> {pendencia.observacao}<br><br>"
            f"<b>@Luiz Marcelo</b> (luiz.marcelo@up380.com.br) verifique esta atualização!"
        )
    }
    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": mensagem["title"],
            "themeColor": "0076D7",
            "title": mensagem["title"],
            "text": mensagem["text"]
        }, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Teams: {e}")

def notificar_teams_pendente_operador(pendencia):
    """Notifica quando pendência fica PENDENTE OPERADOR UP"""
    webhook_url = TEAMS_WEBHOOK_URL
    if not webhook_url:
        return
    mensagem = {
        "title": "🔄 Pendência PENDENTE OPERADOR UP",
        "text": (
            f"<b>Nova pendência aguardando operador!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Resposta do Cliente:</b> {pendencia.resposta_cliente}<br><br>"
            f"<b>@Operadores UP380</b> - Pendência aguardando Natureza de Operação!"
        )
    }
    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": mensagem["title"],
            "themeColor": "FFA500",
            "title": mensagem["title"],
            "text": mensagem["text"]
        }, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Teams: {e}")

def notificar_teams_pendente_supervisor(pendencia):
    """Notifica quando pendência fica PENDENTE SUPERVISOR UP"""
    webhook_url = TEAMS_WEBHOOK_URL
    if not webhook_url:
        return
    mensagem = {
        "title": "👨‍💼 Pendência PENDENTE SUPERVISOR UP",
        "text": (
            f"<b>Pendência aguardando aprovação do supervisor!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Natureza de Operação:</b> {pendencia.natureza_operacao}<br><br>"
            f"<b>@Supervisores UP380</b> - Pendência aguardando resolução!"
        )
    }
    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": mensagem["title"],
            "themeColor": "FF0000",
            "title": mensagem["title"],
            "text": mensagem["text"]
        }, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Teams: {e}")

def notificar_teams_recusa_cliente(pendencia):
    """Notifica quando operador recusa resposta do cliente"""
    webhook_url = TEAMS_WEBHOOK_URL
    if not webhook_url:
        return
    mensagem = {
        "title": "❌ Resposta Recusada - Complemento Necessário",
        "text": (
            f"<b>Operador recusou a resposta do cliente!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Motivo da Recusa:</b> {pendencia.motivo_recusa}<br><br>"
            f"<b>@Cliente</b> - Pendência aguardando complemento de informações!"
        )
    }
    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": mensagem["title"],
            "themeColor": "FF6B35",
            "title": mensagem["title"],
            "text": mensagem["text"]
        }, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Teams: {e}")

def notificar_teams_recusa_supervisor(pendencia):
    """Notifica quando pendência é recusada pelo supervisor e devolvida ao operador"""
    webhook_url = TEAMS_WEBHOOK_URL
    if not webhook_url:
        return
    mensagem = {
        "title": "🔄 Pendência Devolvida pelo Supervisor",
        "text": (
            f"<b>Pendência recusada e devolvida ao operador!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Natureza de Operação:</b> {pendencia.natureza_operacao}<br>"
            f"<b>Motivo da Recusa:</b> {pendencia.motivo_recusa_supervisor}<br><br>"
            f"<b>@Operadores UP380</b> - Pendência devolvida para correção!"
        )
    }
    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": mensagem["title"],
            "themeColor": "FFA500",
            "title": mensagem["title"],
            "text": mensagem["text"]
        }, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Teams: {e}")

@app.route('/operador/pendencias')
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_pendencias():
    """Dashboard do operador - mostra pendências PENDENTE OPERADOR UP"""
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    empresa_filtro = request.args.get('empresa', empresas_usuario[0])
    tipo_filtro = request.args.get('tipo_pendencia', TIPOS_PENDENCIA[0])
    busca = request.args.get('busca', '')
    empresas_selecionadas = request.args.getlist('empresas')
    filtro_status = request.args.get('filtro_status', '')
    filtro_prazo = request.args.get('filtro_prazo', '')
    filtro_valor = request.args.get('filtro_valor', '')
    
    # Definir status de pendências em aberto para o operador
    status_abertos_operador = ['PENDENTE OPERADOR UP', 'PENDENTE COMPLEMENTO CLIENTE', 'DEVOLVIDA AO OPERADOR']
    
    # Obter empresas permitidas para o usuário
    usuario = Usuario.query.get(session['usuario_id'])
    if session.get('usuario_tipo') == 'adm':
        empresas_permitidas = empresas_usuario
    else:
        empresas_permitidas = [e.nome for e in usuario.empresas]
    
    # Consulta agrupada de pendências em aberto por empresa
    from sqlalchemy import func
    pendencias_abertas_por_empresa = (
        db.session.query(Pendencia.empresa, func.count(Pendencia.id).label('quantidade'))
        .filter(Pendencia.status.in_(status_abertos_operador))
        .filter(Pendencia.empresa.in_(empresas_permitidas))
        .group_by(Pendencia.empresa)
        .having(func.count(Pendencia.id) > 0)  # Só empresas com pendências em aberto
        .order_by(func.count(Pendencia.id).desc())  # Ordenar por quantidade (mais críticas primeiro)
        .all()
    )
    
    # Filtro de empresas (múltipla seleção)
    if empresas_selecionadas:
        query = Pendencia.query.filter(Pendencia.empresa.in_(empresas_selecionadas))
    else:
        query = Pendencia.query.filter_by(empresa=empresa_filtro)
    
    # Filtro de status
    if filtro_status:
        query = query.filter(Pendencia.status == filtro_status)
    else:
        # Mostra pendências que precisam de ação do operador
        query = query.filter(Pendencia.status.in_(status_abertos_operador))
    
    if busca:
        query = query.filter(
            db.or_(
                Pendencia.fornecedor_cliente.ilike(f'%{busca}%'),
                Pendencia.banco.ilike(f'%{busca}%'),
                Pendencia.observacao.ilike(f'%{busca}%'),
                Pendencia.resposta_cliente.ilike(f'%{busca}%'),
                Pendencia.natureza_operacao.ilike(f'%{busca}%'),
                db.cast(Pendencia.valor, db.String).ilike(f'%{busca}%'),
                db.cast(Pendencia.data, db.String).ilike(f'%{busca}%'),
                Pendencia.status.ilike(f'%{busca}%')
            )
        )
    # Filtros rápidos adicionais
    from datetime import datetime, timedelta
    if filtro_prazo == 'atrasadas':
        limite = datetime.now().date() - timedelta(days=7)
        query = query.filter(Pendencia.data < limite)
    elif filtro_prazo == 'recentes':
        limite = datetime.now().date() - timedelta(days=7)
        query = query.filter(Pendencia.data >= limite)
    if filtro_valor == 'alto':
        query = query.filter(Pendencia.valor >= 5000)
    elif filtro_valor == 'baixo':
        query = query.filter(Pendencia.valor < 5000)
    
    pendencias = query.order_by(Pendencia.data.desc()).all()
    # Adicionar logs para cada pendência
    for p in pendencias:
        p.logs = LogAlteracao.query.filter_by(pendencia_id=p.id).order_by(LogAlteracao.data_hora.desc()).all()
    
    # Calcular pendências sem resposta por empresa (mantido para compatibilidade)
    pendencias_sem_resposta_por_empresa = {}
    for empresa in empresas_usuario:
        count = Pendencia.query.filter(
            Pendencia.empresa == empresa,
            Pendencia.status.in_(status_abertos_operador),
            (Pendencia.resposta_cliente == None) | (Pendencia.resposta_cliente == '')
        ).count()
        pendencias_sem_resposta_por_empresa[empresa] = count
    
    return render_template(
        'operador_pendencias.html', 
        pendencias=pendencias, 
        empresas=empresas_usuario, 
        empresas_selecionadas=empresas_selecionadas,
        empresa_filtro=empresa_filtro, 
        tipos_pendencia=TIPOS_PENDENCIA, 
        tipo_filtro=tipo_filtro, 
        busca=busca,
        now=datetime.now().date(),  # Adicionado para uso no template
        timedelta=timedelta,  # Adicionado para uso no template
        pendencias_sem_resposta_por_empresa=pendencias_sem_resposta_por_empresa,
        pendencias_abertas_por_empresa=pendencias_abertas_por_empresa  # Nova variável para o indicador
    )

@app.route('/operador/natureza_operacao/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_natureza_operacao(id):
    """Operador informa a Natureza de Operação"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status not in ['PENDENTE OPERADOR UP', 'DEVOLVIDA AO OPERADOR']:
        flash('Esta pendência não está disponível para operador.', 'warning')
        return redirect(url_for('operador_pendencias'))
    
    if request.method == 'POST':
        natureza_operacao = request.form.get('natureza_operacao', '').strip()
        if not natureza_operacao:
            flash('Natureza de Operação é obrigatória.', 'danger')
            return redirect(url_for('operador_natureza_operacao', id=id))
        
        # Atualiza pendência
        pendencia.natureza_operacao = natureza_operacao
        pendencia.status = 'PENDENTE SUPERVISOR UP'
        pendencia.modificado_por = session.get('usuario_email', 'Operador UP380')
        
        # Se era uma pendência devolvida, limpa o motivo de recusa
        if pendencia.motivo_recusa_supervisor:
            pendencia.motivo_recusa_supervisor = None
        
        db.session.commit()
        
        # Log da alteração
        log = LogAlteracao(
            pendencia_id=pendencia.id,
            usuario=session.get('usuario_email', 'Operador UP380'),
            tipo_usuario='operador',
            data_hora=now_brazil(),
            acao='Informação de Natureza de Operação',
            campo_alterado='status',
            valor_anterior='PENDENTE OPERADOR UP',
            valor_novo='PENDENTE SUPERVISOR UP'
        )
        db.session.add(log)
        
        # Log da natureza de operação
        log_natureza = LogAlteracao(
            pendencia_id=pendencia.id,
            usuario=session.get('usuario_email', 'Operador UP380'),
            tipo_usuario='operador',
            data_hora=now_brazil(),
            acao='Informação de Natureza de Operação',
            campo_alterado='natureza_operacao',
            valor_anterior='',
            valor_novo=natureza_operacao
        )
        db.session.add(log_natureza)
        db.session.commit()
        
        # Notificação Teams
        notificar_teams_pendente_supervisor(pendencia)
        
        flash('Natureza de Operação informada com sucesso! Pendência enviada para supervisor.', 'success')
        return redirect(url_for('operador_pendencias'))
    
    return render_template('operador_natureza_operacao.html', pendencia=pendencia)

@app.route('/operador/recusar_resposta/<int:id>', methods=['POST'])
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_recusar_resposta(id):
    """Operador recusa a resposta do cliente e solicita complemento"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está disponível para recusa.', 'warning')
        return redirect(url_for('operador_pendencias'))
    
    motivo_recusa = request.form.get('motivo_recusa', '').strip()
    if not motivo_recusa:
        flash('Motivo da recusa é obrigatório.', 'danger')
        return redirect(url_for('operador_pendencias'))
    
    # Atualiza pendência
    pendencia.motivo_recusa = motivo_recusa
    pendencia.status = 'PENDENTE COMPLEMENTO CLIENTE'
    pendencia.modificado_por = session.get('usuario_email', 'Operador UP380')
    
    db.session.commit()
    
    # Log da recusa
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Operador UP380'),
        tipo_usuario='operador',
        data_hora=now_brazil(),
        acao='Recusa de Resposta do Cliente',
        campo_alterado='status',
        valor_anterior='PENDENTE OPERADOR UP',
        valor_novo='PENDENTE COMPLEMENTO CLIENTE'
    )
    db.session.add(log)
    
    # Log do motivo da recusa
    log_motivo = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Operador UP380'),
        tipo_usuario='operador',
        data_hora=now_brazil(),
        acao='Recusa de Resposta do Cliente',
        campo_alterado='motivo_recusa',
        valor_anterior='',
        valor_novo=motivo_recusa
    )
    db.session.add(log_motivo)
    db.session.commit()
    
    flash('Resposta recusada. Cliente foi notificado para complementar.', 'success')
    return redirect(url_for('operador_pendencias'))

@app.route('/operador/lote_enviar_supervisor', methods=['POST'])
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_lote_enviar_supervisor():
    ids = request.form.getlist('ids')
    if not ids:
        flash('Nenhuma pendência selecionada.', 'warning')
        return redirect(url_for('operador_pendencias'))
    count = 0
    for pid in ids:
        pendencia = Pendencia.query.get(pid)
        if pendencia and pendencia.status == 'PENDENTE OPERADOR UP':
            pendencia.status = 'PENDENTE SUPERVISOR UP'
            pendencia.modificado_por = session.get('usuario_email', 'Operador UP380')
            # Log da alteração
            log = LogAlteracao(
                pendencia_id=pendencia.id,
                usuario=session.get('usuario_email', 'Operador UP380'),
                tipo_usuario='operador',
                data_hora=now_brazil(),
                acao='Envio em lote para supervisor',
                campo_alterado='status',
                valor_anterior='PENDENTE OPERADOR UP',
                valor_novo='PENDENTE SUPERVISOR UP'
            )
            db.session.add(log)
            count += 1
    db.session.commit()
    flash(f'{count} pendência(s) enviadas ao supervisor!', 'success')
    return redirect(url_for('operador_pendencias'))

@app.route('/supervisor/pendencias')
@permissao_requerida('supervisor', 'adm')
def supervisor_pendencias():
    """Dashboard do supervisor - mostra pendências PENDENTE SUPERVISOR UP"""
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    empresa_filtro = request.args.get('empresa', empresas_usuario[0])
    tipo_filtro = request.args.get('tipo_pendencia', '')
    busca = request.args.get('busca', '')
    empresas_selecionadas = request.args.getlist('empresas')
    filtro_status = request.args.get('filtro_status', '')
    filtro_prazo = request.args.get('filtro_prazo', '')
    filtro_valor = request.args.get('filtro_valor', '')
    
    # Definir status de pendências em aberto para o supervisor
    status_abertos_supervisor = ['PENDENTE SUPERVISOR UP']
    
    # Obter empresas permitidas para o usuário
    usuario = Usuario.query.get(session['usuario_id'])
    if session.get('usuario_tipo') == 'adm':
        empresas_permitidas = empresas_usuario
    else:
        empresas_permitidas = [e.nome for e in usuario.empresas]
    
    # Consulta agrupada de pendências em aberto por empresa
    from sqlalchemy import func
    pendencias_abertas_por_empresa = (
        db.session.query(Pendencia.empresa, func.count(Pendencia.id).label('quantidade'))
        .filter(Pendencia.status.in_(status_abertos_supervisor))
        .filter(Pendencia.empresa.in_(empresas_permitidas))
        .group_by(Pendencia.empresa)
        .having(func.count(Pendencia.id) > 0)  # Só empresas com pendências em aberto
        .order_by(func.count(Pendencia.id).desc())  # Ordenar por quantidade (mais críticas primeiro)
        .all()
    )
    
    # Filtro de empresas (múltipla seleção)
    if empresas_selecionadas:
        query = Pendencia.query.filter(Pendencia.empresa.in_(empresas_selecionadas))
    else:
        query = Pendencia.query.filter_by(empresa=empresa_filtro)
    
    # Filtro de status
    if filtro_status:
        query = query.filter(Pendencia.status == filtro_status)
    else:
        query = query.filter(Pendencia.status.in_(status_abertos_supervisor))
    
    # Filtro de tipo de pendência
    if tipo_filtro:
        query = query.filter(Pendencia.tipo_pendencia == tipo_filtro)
    
    if busca:
        query = query.filter(
            db.or_(
                Pendencia.fornecedor_cliente.ilike(f'%{busca}%'),
                Pendencia.banco.ilike(f'%{busca}%'),
                Pendencia.observacao.ilike(f'%{busca}%'),
                Pendencia.resposta_cliente.ilike(f'%{busca}%'),
                Pendencia.natureza_operacao.ilike(f'%{busca}%'),
                db.cast(Pendencia.valor, db.String).ilike(f'%{busca}%'),
                db.cast(Pendencia.data, db.String).ilike(f'%{busca}%'),
                Pendencia.status.ilike(f'%{busca}%')
            )
        )
    
    # Filtros rápidos adicionais
    from datetime import datetime, timedelta
    if filtro_prazo == 'atrasadas':
        limite = datetime.now().date() - timedelta(days=7)
        query = query.filter(Pendencia.data < limite)
    elif filtro_prazo == 'recentes':
        limite = datetime.now().date() - timedelta(days=7)
        query = query.filter(Pendencia.data >= limite)
    
    if filtro_valor == 'alto':
        query = query.filter(Pendencia.valor >= 5000)
    elif filtro_valor == 'baixo':
        query = query.filter(Pendencia.valor < 5000)
    
    pendencias = query.order_by(Pendencia.data.desc()).all()
    
    # Adicionar logs para cada pendência
    for p in pendencias:
        p.logs = LogAlteracao.query.filter_by(pendencia_id=p.id).order_by(LogAlteracao.data_hora.desc()).all()
    
    # Calcular pendências sem resposta por empresa (mantido para compatibilidade)
    pendencias_sem_resposta_por_empresa = {}
    for empresa in empresas_usuario:
        count = Pendencia.query.filter(
            Pendencia.empresa == empresa,
            Pendencia.status.in_(status_abertos_supervisor),
            (Pendencia.resposta_cliente == None) | (Pendencia.resposta_cliente == '')
        ).count()
        pendencias_sem_resposta_por_empresa[empresa] = count
    
    return render_template(
        'supervisor_pendencias.html', 
        pendencias=pendencias, 
        empresas=empresas_usuario, 
        empresas_selecionadas=empresas_selecionadas,
        empresa_filtro=empresa_filtro, 
        tipos_pendencia=TIPOS_PENDENCIA, 
        tipo_filtro=tipo_filtro, 
        busca=busca,
        filtro_status=filtro_status,
        filtro_prazo=filtro_prazo,
        filtro_valor=filtro_valor,
        now=datetime.now().date(),  # Adicionado para uso no template
        timedelta=timedelta,  # Adicionado para uso no template
        pendencias_sem_resposta_por_empresa=pendencias_sem_resposta_por_empresa,
        pendencias_abertas_por_empresa=pendencias_abertas_por_empresa  # Nova variável para o indicador
    )

@app.route('/supervisor/resolver_pendencia/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def supervisor_resolver_pendencia(id):
    """Supervisor resolve a pendência"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE SUPERVISOR UP':
        flash('Esta pendência não está disponível para resolução.', 'warning')
        return redirect(url_for('supervisor_pendencias'))
    
    valor_anterior = pendencia.status
    pendencia.status = 'RESOLVIDA'
    pendencia.modificado_por = session.get('usuario_email', 'Supervisor UP380')
    
    db.session.commit()
    
    # Log da resolução
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Supervisor UP380'),
        tipo_usuario='supervisor',
        data_hora=now_brazil(),
        acao='Resolução de Pendência pelo Supervisor',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='Resolvida'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Pendência resolvida com sucesso!', 'success')
    return redirect(url_for('supervisor_pendencias'))

@app.route('/supervisor/lote_resolver_pendencias', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def supervisor_lote_resolver_pendencias():
    """Supervisor resolve múltiplas pendências em lote"""
    ids = request.form.getlist('ids')
    if not ids:
        flash('Nenhuma pendência selecionada.', 'warning')
        return redirect(url_for('supervisor_pendencias'))
    
    count = 0
    for pid in ids:
        pendencia = Pendencia.query.get(pid)
        if pendencia and pendencia.status == 'PENDENTE SUPERVISOR UP':
            valor_anterior = pendencia.status
            pendencia.status = 'RESOLVIDA'
            pendencia.modificado_por = session.get('usuario_email', 'Supervisor UP380')
            
            # Log da resolução
            log = LogAlteracao(
                pendencia_id=pendencia.id,
                usuario=session.get('usuario_email', 'Supervisor UP380'),
                tipo_usuario='supervisor',
                data_hora=now_brazil(),
                acao='Resolução em lote pelo Supervisor',
                campo_alterado='status',
                valor_anterior=valor_anterior,
                valor_novo='Resolvida'
            )
            db.session.add(log)
            count += 1
    
    db.session.commit()
    flash(f'{count} pendência(s) resolvidas com sucesso!', 'success')
    return redirect(url_for('supervisor_pendencias'))

@app.route('/supervisor/recusar_devolver_operador/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def supervisor_recusar_devolver_operador(id):
    """Supervisor recusa a pendência e devolve ao operador para correção"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE SUPERVISOR UP':
        flash('Esta pendência não está disponível para recusa.', 'warning')
        return redirect(url_for('supervisor_pendencias'))
    
    motivo_recusa = request.form.get('motivo_recusa_supervisor', '').strip()
    if not motivo_recusa:
        flash('Motivo da recusa é obrigatório.', 'danger')
        return redirect(url_for('supervisor_pendencias'))
    
    # Atualiza pendência
    valor_anterior = pendencia.status
    pendencia.motivo_recusa_supervisor = motivo_recusa
    pendencia.status = 'DEVOLVIDA AO OPERADOR'
    pendencia.modificado_por = session.get('usuario_email', 'Supervisor UP380')
    
    db.session.commit()
    
    # Log da recusa
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Supervisor UP380'),
        tipo_usuario='supervisor',
        data_hora=now_brazil(),
        acao='Recusa e Devolução ao Operador',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='DEVOLVIDA AO OPERADOR'
    )
    db.session.add(log)
    
    # Log do motivo da recusa
    log_motivo = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Supervisor UP380'),
        tipo_usuario='supervisor',
        data_hora=now_brazil(),
        acao='Recusa e Devolução ao Operador',
        campo_alterado='motivo_recusa_supervisor',
        valor_anterior='',
        valor_novo=motivo_recusa
    )
    db.session.add(log_motivo)
    db.session.commit()
    
    # Notificação Teams
    notificar_teams_recusa_supervisor(pendencia)
    
    flash('Pendência recusada e devolvida ao operador para correção!', 'success')
    return redirect(url_for('supervisor_pendencias'))

@app.route('/editar_observacao/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'cliente', 'cliente_supervisor')
def editar_observacao(id):
    pendencia = Pendencia.query.get_or_404(id)
    if request.method == 'POST':
        valor_anterior = pendencia.observacao
        novo_valor = request.form.get('observacao') or 'DO QUE SE TRATA?'
        pendencia.observacao = novo_valor
        pendencia.modificado_por = 'USUARIO'
        pendencia.status = 'PENDENTE OPERADOR UP'  # Corrigido para novo fluxo
        # Upload de anexo pelo cliente
        if 'documento_cliente' in request.files:
            file = request.files['documento_cliente']
            if file and file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join('static/notas_fiscais', filename))
                pendencia.nota_fiscal_arquivo = filename
        db.session.commit()
        # Log da alteração
        log = LogAlteracao(
            pendencia_id=pendencia.id,
            usuario=session.get('usuario_email', 'USUARIO'),
            tipo_usuario='cliente',
            data_hora=now_brazil(),
            acao='Alteração de Observação',
            campo_alterado='observacao',
            valor_anterior=valor_anterior,
            valor_novo=novo_valor
        )
        db.session.add(log)
        db.session.commit()
        # Notificação para operadores
        notificar_teams_pendente_operador(pendencia)
        flash('Observação atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editar_observacao.html', pendencia=pendencia)

@app.route('/resolvidas', methods=['GET'])
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def dashboard_resolvidas():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
    empresa_filtro = request.args.get('empresa', empresas_usuario[0])
    tipo_filtro = request.args.get('tipo_pendencia', TIPOS_PENDENCIA[0])
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    def filtro_data(query):
        if data_inicio:
            query = query.filter(Pendencia.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Pendencia.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
        return query
    resolvidas = filtro_data(Pendencia.query.filter_by(empresa=empresa_filtro, tipo_pendencia=tipo_filtro, status='RESOLVIDA')).order_by(Pendencia.data.desc()).all()
    logs_por_pendencia = {}
    for pend in resolvidas:
        logs_por_pendencia[pend.id] = LogAlteracao.query.filter_by(pendencia_id=pend.id).order_by(LogAlteracao.data_hora.desc()).all()
    return render_template(
        'resolvidas.html',
        resolvidas=resolvidas,
        logs_por_pendencia=logs_por_pendencia,
        empresas=empresas_usuario,
        empresa_filtro=empresa_filtro,
        tipos_pendencia=TIPOS_PENDENCIA,
        tipo_filtro=tipo_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

@app.route('/pendencias')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente_supervisor')
def listar_pendencias():
    """
    Rota genérica para listar pendências com filtros
    """
    status = request.args.get('status')
    empresa = request.args.get('empresa')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=50, type=int)
    per_page = max(10, min(per_page, 200))  # limites seguros

    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))

    query = Pendencia.query

    # Filtro por empresa
    if empresa:
        if empresa not in empresas_usuario:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('pre_dashboard'))
        query = query.filter(Pendencia.empresa == empresa)

    # Filtro por status
    if status:
        query = query.filter(Pendencia.status == status)

    # Ordenação padrão
    if status == "RESOLVIDA":
        query = query.order_by(Pendencia.data_resposta.desc().nullslast(), Pendencia.id.desc())
    else:
        query = query.order_by(Pendencia.data.desc().nullslast(), Pendencia.id.desc())

    pager = query.paginate(page=page, per_page=per_page, error_out=False)

    # Registrar log de visualização
    log = LogAlteracao(
        pendencia_id=0,  # 0 indica que é uma alteração de sistema
        usuario=session.get('usuario_email', 'sistema'),
        tipo_usuario=session.get('usuario_tipo', 'sistema'),
        data_hora=now_brazil(),
        acao="view",
        campo_alterado="pendencias_list",
        valor_anterior=None,
        valor_novo=f"status={status}; empresa={empresa}; page={page}; per_page={per_page}"
    )
    db.session.add(log)
    db.session.commit()

    return render_template(
        'pendencias_list.html',
        pager=pager,
        status=status,
        empresa=empresa,
        empresas=empresas_usuario,
        filtros={
            "status": status,
            "empresa": empresa,
            "ordenacao": "data_resposta_desc" if status == "RESOLVIDA" else "data_desc"
        }
    )

@app.route('/logs/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def ver_logs_pendencia(pendencia_id):
    logs = LogAlteracao.query.filter_by(pendencia_id=pendencia_id).order_by(LogAlteracao.data_hora.desc()).all()
    pendencia = Pendencia.query.get_or_404(pendencia_id)
    return render_template('logs_pendencia.html', logs=logs, pendencia=pendencia)

@app.route('/exportar_logs/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def exportar_logs(pendencia_id):
    logs = LogAlteracao.query.filter_by(pendencia_id=pendencia_id).order_by(LogAlteracao.data_hora.desc()).all()
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(['Data/Hora', 'Usuário', 'Tipo', 'Ação', 'Campo Alterado', 'Valor Anterior', 'Valor Novo'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for log in logs:
            writer.writerow([
                log.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
                log.usuario,
                log.tipo_usuario,
                log.acao,
                log.campo_alterado or '-',
                log.valor_anterior or '-',
                log.valor_novo or '-'
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
    headers = {
        'Content-Disposition': f'attachment; filename=logs_pendencia_{pendencia_id}.csv'
    }
    return Response(generate(), mimetype='text/csv', headers=headers)

@app.route('/logs_recentes')
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def logs_recentes():
    logs = LogAlteracao.query.order_by(LogAlteracao.data_hora.desc()).limit(50).all()
    return render_template('logs_recentes.html', logs=logs)

@app.route('/exportar_logs_csv')
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def exportar_logs_csv():
    logs = LogAlteracao.query.order_by(LogAlteracao.data_hora.desc()).limit(50).all()
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(['Data/Hora', 'Usuário', 'Tipo', 'Ação', 'Campo Alterado', 'Valor Anterior', 'Valor Novo'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for log in logs:
            writer.writerow([
                log.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
                log.usuario,
                log.tipo_usuario,
                log.acao,
                log.campo_alterado or '-',
                log.valor_anterior or '-',
                log.valor_novo or '-'
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
    headers = {
        'Content-Disposition': 'attachment; filename=logs_recentes.csv'
    }
    return Response(generate(), mimetype='text/csv', headers=headers)

@app.route('/exportar_pendencias_csv')
@permissao_requerida('supervisor', 'adm', 'operador')
def exportar_pendencias_csv():
    """
    Exporta pendências para CSV com filtros aplicados
    """
    status = request.args.get('status')
    empresa = request.args.get('empresa')
    
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))

    query = Pendencia.query

    # Filtro por empresa
    if empresa:
        if empresa not in empresas_usuario:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('pre_dashboard'))
        query = query.filter(Pendencia.empresa == empresa)

    # Filtro por status
    if status:
        query = query.filter(Pendencia.status == status)

    # Ordenação
    if status == "RESOLVIDA":
        query = query.order_by(Pendencia.data_resposta.desc().nullslast(), Pendencia.id.desc())
    else:
        query = query.order_by(Pendencia.data.desc().nullslast(), Pendencia.id.desc())

    pendencias = query.all()

    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow([
            'ID', 'Empresa', 'Tipo', 'Status', 'Data da Pendência', 'Data de Abertura', 'Data Resposta', 
            'Fornecedor/Cliente', 'Valor', 'Observação', 'Banco', 
            'Natureza Operação', 'Modificado por'
        ])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for pendencia in pendencias:
            writer.writerow([
                pendencia.id,
                pendencia.empresa,
                pendencia.tipo_pendencia,
                pendencia.status,
                pendencia.data.strftime('%d/%m/%Y') if pendencia.data else '',
                pendencia.data_abertura.strftime('%d/%m/%Y %H:%M') if pendencia.data_abertura else '',
                pendencia.data_resposta.strftime('%d/%m/%Y') if pendencia.data_resposta else '',
                pendencia.fornecedor_cliente,
                f"R$ {pendencia.valor:.2f}" if pendencia.valor else '',
                pendencia.observacao or '',
                pendencia.banco or '',
                pendencia.natureza_operacao or '',
                pendencia.modificado_por or ''
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    # Nome do arquivo
    filename = f"pendencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if empresa:
        filename += f"_{empresa.replace(' ', '_')}"
    if status:
        filename += f"_{status.replace(' ', '_')}"
    filename += ".csv"

    headers = {
        'Content-Disposition': f'attachment; filename={filename}'
    }
    
    return Response(generate(), mimetype='text/csv', headers=headers)

@app.route('/pendencia/<int:id>/informar_natureza', methods=['POST'])
@permissao_requerida('operador', 'supervisor')
def informar_natureza_operacao(id):
    """
    Permite que operador ou supervisor informe a natureza da operação
    """
    if not pode_atuar_como_operador():
        flash('Você não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    
    # Verificar se o status atual permite a ação
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está no status correto para esta ação.', 'warning')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    # Verificar permissão de empresa
    empresas_usuario = obter_empresas_para_usuario()
    if pendencia.empresa not in empresas_usuario:
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('dashboard'))
    
    natureza_operacao = request.form.get('natureza_operacao')
    if not natureza_operacao:
        flash('Natureza da operação é obrigatória.', 'danger')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    # Atualizar a pendência
    valor_anterior = pendencia.natureza_operacao
    pendencia.natureza_operacao = natureza_operacao
    pendencia.modificado_por = session.get('usuario_email', 'Sistema')
    
    db.session.commit()
    
    # Log da alteração
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Sistema'),
        tipo_usuario=session.get('usuario_tipo', 'sistema'),
        data_hora=now_brazil(),
        acao='Informação de Natureza de Operação',
        campo_alterado='natureza_operacao',
        valor_anterior=valor_anterior,
        valor_novo=natureza_operacao
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Natureza da operação informada com sucesso!', 'success')
    return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))

@app.route('/pendencia/<int:id>/aceitar_resposta', methods=['POST'])
@permissao_requerida('operador', 'supervisor')
def aceitar_resposta_cliente(id):
    """
    Permite que operador ou supervisor aceite a resposta do cliente
    """
    if not pode_atuar_como_operador():
        flash('Você não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    
    # Verificar se o status atual permite a ação
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está no status correto para esta ação.', 'warning')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    # Verificar permissão de empresa
    empresas_usuario = obter_empresas_para_usuario()
    if pendencia.empresa not in empresas_usuario:
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Atualizar status
    valor_anterior = pendencia.status
    pendencia.status = 'PENDENTE SUPERVISOR UP'
    pendencia.modificado_por = session.get('usuario_email', 'Sistema')
    
    db.session.commit()
    
    # Log da alteração
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Sistema'),
        tipo_usuario=session.get('usuario_tipo', 'sistema'),
        data_hora=now_brazil(),
        acao='Aceitar Resposta do Cliente',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='PENDENTE SUPERVISOR UP'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Resposta do cliente aceita! Pendência enviada para supervisor.', 'success')
    return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))

@app.route('/pendencia/<int:id>/recusar_resposta', methods=['POST'])
@permissao_requerida('operador', 'supervisor')
def recusar_resposta_cliente(id):
    """
    Permite que operador ou supervisor recuse a resposta do cliente
    """
    if not pode_atuar_como_operador():
        flash('Você não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    
    # Verificar se o status atual permite a ação
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está no status correto para esta ação.', 'warning')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    # Verificar permissão de empresa
    empresas_usuario = obter_empresas_para_usuario()
    if pendencia.empresa not in empresas_usuario:
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('dashboard'))
    
    motivo_recusa = request.form.get('motivo_recusa')
    if not motivo_recusa:
        flash('Motivo da recusa é obrigatório.', 'danger')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    # Atualizar status e motivo
    valor_anterior_status = pendencia.status
    valor_anterior_motivo = pendencia.motivo_recusa
    
    pendencia.status = 'PENDENTE CLIENTE'
    pendencia.motivo_recusa = motivo_recusa
    pendencia.modificado_por = session.get('usuario_email', 'Sistema')
    
    db.session.commit()
    
    # Log da alteração
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Sistema'),
        tipo_usuario=session.get('usuario_tipo', 'sistema'),
        data_hora=now_brazil(),
        acao='Recusar Resposta do Cliente',
        campo_alterado='status',
        valor_anterior=valor_anterior_status,
        valor_novo='PENDENTE CLIENTE'
    )
    db.session.add(log)
    
    # Log do motivo da recusa
    log_motivo = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Sistema'),
        tipo_usuario=session.get('usuario_tipo', 'sistema'),
        data_hora=now_brazil(),
        acao='Motivo da Recusa',
        campo_alterado='motivo_recusa',
        valor_anterior=valor_anterior_motivo,
        valor_novo=motivo_recusa
    )
    db.session.add(log_motivo)
    db.session.commit()
    
    # Enviar e-mail ao cliente informando sobre a recusa
    try:
        enviar_email_resposta_recusada(pendencia, motivo_recusa)
    except Exception as e:
        print(f"Erro ao enviar e-mail de recusa: {e}")
    
    flash('Resposta do cliente recusada! Pendência devolvida ao cliente.', 'warning')
    return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))

@app.route('/aprovar_pendencia/<int:id>', methods=['POST'])
@permissao_requerida('adm')
def aprovar_pendencia(id):
    """Admin aprova uma pendência diretamente"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status == 'RESOLVIDA':
        flash('Esta pendência já está resolvida.', 'warning')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    valor_anterior = pendencia.status
    pendencia.status = 'RESOLVIDA'
    pendencia.modificado_por = session.get('usuario_email', 'Admin UP380')
    pendencia.data_resposta = now_brazil()
    
    db.session.commit()
    
    # Log da aprovação
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email', 'Admin UP380'),
        tipo_usuario='adm',
        data_hora=now_brazil(),
        acao='Aprovação Direta pelo Admin',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='RESOLVIDA'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Pendência aprovada com sucesso!', 'success')
    return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))

@app.route("/relatorios/mensal", methods=["GET"])
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente_supervisor')
def relatorio_mensal():
    """
    Relatório mensal de pendências - resolvidas vs pendentes por mês
    Suporta filtro por empresa específica ou múltiplas empresas
    """
    from sqlalchemy import func
    from dateutil.relativedelta import relativedelta
    from datetime import date
    
    def month_bounds(ref_yyyy_mm: str):
        """Retorna início e fim do mês baseado em YYYY-MM"""
        base = datetime.strptime(ref_yyyy_mm, "%Y-%m")
        ini = date(base.year, base.month, 1)
        fim = (ini + relativedelta(months=1)) - relativedelta(days=1)
        return ini, fim
    
    def empresas_permitidas_ids(user):
        """Retorna lista de IDs das empresas às quais o usuário tem acesso"""
        empresas_usuario = obter_empresas_para_usuario()
        empresas_objs = Empresa.query.filter(Empresa.nome.in_(empresas_usuario)).all()
        return [e.id for e in empresas_objs]
    
    # --- parâmetros ---
    ref = request.args.get("ref") or datetime.utcnow().strftime("%Y-%m")
    try:
        dt_ini, dt_fim = month_bounds(ref)
    except ValueError:
        flash('Parâmetro "ref" inválido. Use YYYY-MM.', 'danger')
        return redirect(url_for('dashboard'))

    empresa_id = request.args.get("empresa_id", type=int)
    mult_empresas = request.args.getlist("empresas")  # usado no modo global (checkboxes)
    permitidas = empresas_permitidas_ids(session.get('usuario_email', 'sistema'))
    fmt = request.args.get("format", "html")
    base = request.args.get("base", "pendencia")  # "pendencia" | "abertura"

    # --- escopo por empresa ---
    empresas_alvo = []
    if empresa_id:
        if empresa_id not in permitidas:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('dashboard'))
        empresas_alvo = [empresa_id]
    elif mult_empresas:
        empresas_alvo = [int(x) for x in mult_empresas if int(x) in permitidas]
    else:
        # global: todas as permitidas
        empresas_alvo = permitidas

    # map id -> nome (Pendencia.empresa é string)
    emps = {e.id: e.nome for e in Empresa.query.filter(Empresa.id.in_(empresas_alvo)).all()}
    if not emps:
        flash('Nenhuma empresa selecionada ou permitida.', 'danger')
        return redirect(url_for('dashboard'))

    # --- Base de cálculo do mês ---
    if base == "abertura":
        filtro_data = (func.date(Pendencia.data_abertura) >= dt_ini) & (func.date(Pendencia.data_abertura) <= dt_fim)
    else:
        filtro_data = (func.date(Pendencia.data) >= dt_ini) & (func.date(Pendencia.data) <= dt_fim)

    q = Pendencia.query.filter(filtro_data, Pendencia.empresa.in_(list(emps.values())))

    # --- agregados principais ---
    por_status = (
        q.with_entities(Pendencia.empresa, Pendencia.status, func.count(Pendencia.id))
         .group_by(Pendencia.empresa, Pendencia.status).all()
    )
    resolvidas_no_mes = (
        db.session.query(Pendencia.empresa, func.count(Pendencia.id))
        .filter(Pendencia.status == "RESOLVIDA",
                func.date(Pendencia.data_resposta) >= dt_ini,
                func.date(Pendencia.data_resposta) <= dt_fim,
                Pendencia.empresa.in_(list(emps.values())))
        .group_by(Pendencia.empresa).all()
    )

    # --- montar payload ---
    agg_status = {}  # {empresa_nome: {status: qtde}}
    for emp, st, qt in por_status:
        agg_status.setdefault(emp, {})[st] = qt

    agg_resolvidas = dict(resolvidas_no_mes)  # {empresa_nome: qtde}

    payload = {
        "ref": ref,
        "base": base,
        "intervalo": {"inicio": dt_ini.isoformat(), "fim": dt_fim.isoformat()},
        "empresas": list(emps.values()),
        "por_status": agg_status,
        "resolvidas_no_mes": agg_resolvidas
    }

    # --- logging ---
    log = LogAlteracao(
        pendencia_id=0,  # 0 indica que é uma alteração de sistema
        usuario=session.get('usuario_email', 'sistema'),
        tipo_usuario=session.get('usuario_tipo', 'sistema'),
        data_hora=now_brazil(),
        acao="view",
        campo_alterado="relatorio_mensal",
        valor_anterior=None,
        valor_novo=f"ref={ref}; empresa_id={empresa_id}; empresas={','.join(map(str, empresas_alvo))}; base={base}"
    )
    db.session.add(log)
    db.session.commit()

    # --- formatos ---
    if fmt == "json":
        return jsonify(payload)

    if fmt == "csv":
        # CSV com dados agregados por empresa
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["Relatório mensal de pendências", ref])
        w.writerow([f"Período: {dt_ini.strftime('%d/%m/%Y')} a {dt_fim.strftime('%d/%m/%Y')}"])
        w.writerow([f"Base: {'Data de Abertura' if base == 'abertura' else 'Data da Pendência'}"])
        w.writerow([f"Empresas: {', '.join(emps.values())}"])
        w.writerow([])
        
        # Por empresa
        for empresa_nome in emps.values():
            w.writerow([f"Empresa: {empresa_nome}"])
            w.writerow(["Status", "Quantidade"])
            if empresa_nome in agg_status:
                for status, qtde in agg_status[empresa_nome].items():
                    w.writerow([status, qtde])
            w.writerow(["Resolvidas no mês", agg_resolvidas.get(empresa_nome, 0)])
            w.writerow([])

        resp = Response(buf.getvalue(), mimetype='text/csv')
        nome_arq = f"relatorio_mensal_{ref}_{','.join(emps.values())}.csv"
        resp.headers["Content-Disposition"] = f"attachment; filename={nome_arq}"
        return resp

    # formato HTML (default)
    empresas_lista = Empresa.query.filter(Empresa.id.in_(permitidas)).all()
    empresas_selecionadas = list(emps.keys())
    empresa_bloqueada = (empresa_id is not None)
    
    return render_template("relatorio_mensal.html",
                           payload=payload,
                           ref=ref,
                           base=base,
                           empresas_lista=empresas_lista,
                           empresas_selecionadas=empresas_selecionadas,
                           empresa_bloqueada=empresa_bloqueada,
                           dt_ini=dt_ini,
                           dt_fim=dt_fim)

@app.route('/relatorio_operadores')
@permissao_requerida('adm', 'supervisor', 'cliente_supervisor')
def relatorio_operadores():
    from sqlalchemy.sql import func
    # Buscar todos os operadores
    operadores = Usuario.query.filter_by(tipo='operador').all()
    dados = []
    for operador in operadores:
        # Pendências em que o operador informou a natureza (ação: 'Informação de Natureza de Operação')
        logs_natureza = LogAlteracao.query.filter_by(usuario=operador.email, acao='Informação de Natureza de Operação').all()
        pendencias_ids = list(set([log.pendencia_id for log in logs_natureza]))
        qtd = len(pendencias_ids)
        # Calcular tempo médio de resposta (PENDENTE OPERADOR UP -> PENDENTE SUPERVISOR UP)
        tempos = []
        for pid in pendencias_ids:
            log_inicio = LogAlteracao.query.filter_by(pendencia_id=pid, valor_novo='PENDENTE OPERADOR UP').order_by(LogAlteracao.data_hora).first()
            log_fim = LogAlteracao.query.filter_by(pendencia_id=pid, valor_novo='PENDENTE SUPERVISOR UP').order_by(LogAlteracao.data_hora).first()
            if log_inicio and log_fim:
                delta = (log_fim.data_hora - log_inicio.data_hora).total_seconds() / 60  # minutos
                tempos.append(delta)
        tempo_medio = sum(tempos)/len(tempos) if tempos else 0
        dados.append({
            'operador': operador.email,
            'qtd': qtd,
            'tempo_medio': tempo_medio
        })
    # Ranking
    dados = sorted(dados, key=lambda x: (-x['qtd'], x['tempo_medio']))
    return render_template('relatorio_operadores.html', dados=dados)

@app.route('/')
def index():
    """Rota raiz - redireciona baseado no tipo de usuário"""
    if not session.get('usuario_email'):
        return redirect(url_for('login'))
    
    # Redirecionar direto para empresas
    return redirect(url_for('pre_dashboard'))

# ROTA DESATIVADA - SEGMENTOS REMOVIDOS
# @app.route('/segmentos')
# @permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def listar_segmentos_DESATIVADO():
    """Lista todos os segmentos disponíveis"""
    segmentos = Segmento.query.order_by(Segmento.nome).all()
    
    # Se não houver segmentos, redirecionar para empresas
    if not segmentos:
        flash('Nenhum segmento cadastrado. Exibindo empresas diretamente.', 'info')
        return redirect(url_for('pre_dashboard'))
    
    # Contar empresas e pendências por segmento
    segmentos_data = []
    for seg in segmentos:
        empresas_segmento = seg.empresas
        
        # Filtrar por permissão de usuário
        if session.get('usuario_tipo') != 'adm':
            empresas_usuario = obter_empresas_para_usuario()
            empresas_segmento = [e for e in empresas_segmento if e.nome in empresas_usuario]
        
        # Contar pendências abertas (não resolvidas)
        total_pendencias = 0
        for empresa in empresas_segmento:
            total_pendencias += Pendencia.query.filter(
                Pendencia.empresa == empresa.nome,
                Pendencia.status != 'RESOLVIDA'
            ).count()
        
        # Preview de empresas (primeiras 6)
        empresas_preview = [e.nome for e in empresas_segmento[:6]]
        
        segmentos_data.append({
            'id': seg.id,
            'nome': seg.nome,
            'total_empresas': len(empresas_segmento),
            'total_pendencias': total_pendencias,
            'empresas_preview': empresas_preview
        })
    
    return render_template('segmentos.html', segmentos=segmentos_data)

# ROTA DESATIVADA - SEGMENTOS REMOVIDOS
# @app.route('/segmento/<int:segmento_id>')
# @permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def empresas_por_segmento_DESATIVADO(segmento_id):
    """Lista empresas de um segmento específico"""
    segmento = Segmento.query.get_or_404(segmento_id)
    
    # Obter empresas do segmento
    if session.get('usuario_tipo') == 'adm':
        empresas = segmento.empresas
    else:
        empresas_usuario = obter_empresas_para_usuario()
        empresas = [e for e in segmento.empresas if e.nome in empresas_usuario]
    
    # Contar pendências por empresa
    empresas_data = []
    total_pendencias_abertas = 0
    
    for empresa in empresas:
        total_pendencias = Pendencia.query.filter_by(empresa=empresa.nome).count()
        pendencias_abertas = Pendencia.query.filter(
            Pendencia.empresa == empresa.nome,
            Pendencia.status != 'RESOLVIDA'
        ).count()
        
        total_pendencias_abertas += pendencias_abertas
        
        empresas_data.append({
            'id': empresa.id,
            'nome': empresa.nome,
            'total_pendencias': total_pendencias,
            'pendencias_abertas': pendencias_abertas
        })
    
    # Ordenar por mais pendências abertas
    empresas_data.sort(key=lambda x: x['pendencias_abertas'], reverse=True)
    
    # Data atual para relatórios
    today = datetime.now().date()
    current_month = today.strftime('%Y-%m')
    
    return render_template('empresas_por_segmento.html', 
                         segmento=segmento, 
                         empresas=empresas_data,
                         total_pendencias_abertas=total_pendencias_abertas,
                         current_month=current_month)

# ROTA DESATIVADA - SEGMENTOS REMOVIDOS
# @app.route('/empresa/<int:empresa_id>')
# @permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def listar_pendencias_empresa_DESATIVADO(empresa_id):
    """Lista pendências de uma empresa específica"""
    empresa = Empresa.query.get_or_404(empresa_id)
    
    # Verificar permissão
    if session.get('usuario_tipo') != 'adm':
        empresas_usuario = obter_empresas_para_usuario()
        if empresa.nome not in empresas_usuario:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('pre_dashboard'))
    
    # Redirecionar para dashboard com filtro de empresa
    return redirect(url_for('dashboard', empresa=empresa.nome))

@app.route('/gerenciar_usuarios')
@permissao_requerida('supervisor', 'adm')
def gerenciar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/gerenciar_usuarios.html', usuarios=usuarios)

# Lista de funcionalidades e categorias para uso nos formulários de usuário
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

@app.route('/novo_usuario', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def novo_usuario():
    empresas = Empresa.query.all()
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']
        empresas_ids = request.form.getlist('empresas_permitidas')
        ativo = True
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
            return redirect(url_for('novo_usuario'))
        novo = Usuario(email=email, senha_hash=generate_password_hash(senha), tipo=tipo)
        if empresas_ids:
            novo.empresas = Empresa.query.filter(Empresa.id.in_(empresas_ids)).all()
        db.session.add(novo)
        db.session.commit()
        # Permissões individualizadas
        for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
            for func, _ in funcionalidades:
                permitido = request.form.get(f'perm_{func}') == 'on'
                if permitido != checar_permissao(tipo, func):
                    p = PermissaoUsuarioPersonalizada(usuario_id=novo.id, funcionalidade=func, permitido=permitido)
                    db.session.add(p)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))
    # Permissões padrão do tipo
    permissoes_tipo = {func: checar_permissao('operador', func) for cat, funclist in FUNCIONALIDADES_CATEGORIZADAS for func, _ in funclist}
    return render_template('admin/novo_usuario.html', empresas=empresas, funcionalidades_categorizadas=FUNCIONALIDADES_CATEGORIZADAS, permissoes_tipo=permissoes_tipo)

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    empresas = Empresa.query.all()
    if request.method == 'POST':
        usuario.email = request.form['email']
        nova_senha = request.form.get('nova_senha')
        if nova_senha:
            usuario.senha_hash = generate_password_hash(nova_senha)
        usuario.tipo = request.form['tipo']
        empresas_ids = request.form.getlist('empresas_permitidas')
        if empresas_ids:
            usuario.empresas = Empresa.query.filter(Empresa.id.in_(empresas_ids)).all()
        else:
            usuario.empresas = []
        db.session.commit()
        # Permissões individualizadas
        # Remove antigas
        PermissaoUsuarioPersonalizada.query.filter_by(usuario_id=usuario.id).delete()
        for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
            for func, _ in funcionalidades:
                permitido = request.form.get(f'perm_{func}') == 'on'
                if permitido != checar_permissao(usuario.tipo, func):
                    p = PermissaoUsuarioPersonalizada(usuario_id=usuario.id, funcionalidade=func, permitido=permitido)
                    db.session.add(p)
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))
    empresas_permitidas = [e.id for e in usuario.empresas]
    # Permissões atuais (personalizadas ou herdadas)
    permissoes_usuario = {}
    for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
        for func, _ in funcionalidades:
            permissoes_usuario[func] = checar_permissao_usuario(usuario.id, usuario.tipo, func)
    return render_template('admin/editar_usuario.html', usuario=usuario, empresas=empresas, empresas_permitidas=empresas_permitidas, funcionalidades_categorizadas=FUNCIONALIDADES_CATEGORIZADAS, permissoes_usuario=permissoes_usuario)

@app.route('/gerenciar_empresas')
@permissao_requerida('supervisor', 'adm')
def gerenciar_empresas():
    """Lista todas as empresas com informações adicionais"""
    empresas = Empresa.query.order_by(Empresa.nome).all()
    
    # Adicionar contagem de pendências para cada empresa
    empresas_info = []
    for empresa in empresas:
        total_pendencias = Pendencia.query.filter_by(empresa=empresa.nome).count()
        empresas_info.append({
            'empresa': empresa,
            'total_pendencias': total_pendencias
        })
    
    return render_template('admin/gerenciar_empresas.html', empresas_info=empresas_info)

@app.route('/nova_empresa', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def nova_empresa():
    if request.method == 'POST':
        nome = request.form['nome']
        segmento_id = request.form.get('segmento_id')
        
        # Validação de nome
        if not nome or nome.strip() == '':
            flash('Nome da empresa é obrigatório.', 'danger')
            return redirect(url_for('nova_empresa'))
        
        # Verificar se empresa já existe
        if Empresa.query.filter_by(nome=nome).first():
            flash('Empresa já cadastrada.', 'danger')
            return redirect(url_for('nova_empresa'))
        
        # Validar se segmento existe (se fornecido)
        if segmento_id and segmento_id != '':
            segmento = Segmento.query.get(int(segmento_id))
            if not segmento:
                flash('Segmento inválido.', 'danger')
                return redirect(url_for('nova_empresa'))
        
        # Cria a nova empresa com segmento
        nova = Empresa(
            nome=nome,
            segmento_id=int(segmento_id) if segmento_id and segmento_id != '' else None
        )
        db.session.add(nova)
        db.session.flush()  # Gera o ID da empresa
        
        # Integra automaticamente a nova empresa em todo o sistema
        if integrar_nova_empresa(nova):
            segmento_msg = f' no segmento {segmento.nome}' if segmento_id and segmento_id != '' else ''
            flash(f'Empresa "{nome}"{segmento_msg} criada e integrada automaticamente em todo o sistema!', 'success')
        else:
            flash(f'Empresa "{nome}" criada, mas houve um problema na integração automática.', 'warning')
        
        return redirect(url_for('gerenciar_empresas'))
    
    # GET - Buscar segmentos para o formulário
    segmentos = Segmento.query.order_by(Segmento.nome).all()
    return render_template('admin/form_empresa.html', empresa=None, segmentos=segmentos, title='Nova Empresa')

@app.route('/editar_empresa/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form['nome']
        segmento_id = request.form.get('segmento_id')
        
        # Validação de nome
        if not nome or nome.strip() == '':
            flash('Nome da empresa é obrigatório.', 'danger')
            return redirect(url_for('editar_empresa', id=id))
        
        # Verificar se nome já existe em outra empresa
        empresa_existente = Empresa.query.filter_by(nome=nome).first()
        if empresa_existente and empresa_existente.id != empresa.id:
            flash('Já existe outra empresa com este nome.', 'danger')
            return redirect(url_for('editar_empresa', id=id))
        
        # Validar se segmento existe (se fornecido)
        if segmento_id and segmento_id != '':
            segmento = Segmento.query.get(int(segmento_id))
            if not segmento:
                flash('Segmento inválido.', 'danger')
                return redirect(url_for('editar_empresa', id=id))
        
        # Atualizar empresa
        empresa.nome = nome
        empresa.segmento_id = int(segmento_id) if segmento_id and segmento_id != '' else None
        
        db.session.commit()
        flash(f'Empresa "{nome}" atualizada com sucesso!', 'success')
        return redirect(url_for('gerenciar_empresas'))
    
    # GET - Buscar segmentos para o formulário
    segmentos = Segmento.query.order_by(Segmento.nome).all()
    return render_template('admin/form_empresa.html', empresa=empresa, segmentos=segmentos, title='Editar Empresa')

@app.route('/deletar_usuario/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def deletar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário removido com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/deletar_empresa/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def deletar_empresa(id):
    """Deleta uma empresa após validações"""
    print(f"\n{'='*50}")
    print(f"TENTATIVA DE EXCLUSÃO - Empresa ID: {id}")
    print(f"{'='*50}")
    
    empresa = Empresa.query.get_or_404(id)
    print(f"Empresa encontrada: {empresa.nome}")
    
    # Verificar se há pendências associadas
    total_pendencias = Pendencia.query.filter_by(empresa=empresa.nome).count()
    print(f"Total de pendências: {total_pendencias}")
    
    if total_pendencias > 0:
        print(f"BLOQUEADO: Empresa tem {total_pendencias} pendências")
        flash(f'Não é possível excluir a empresa "{empresa.nome}" pois ela possui {total_pendencias} pendência(s) associada(s). Exclua as pendências primeiro.', 'danger')
        return redirect(url_for('gerenciar_empresas'))
    
    # Verificar se há usuários vinculados
    total_usuarios = len(empresa.usuarios) if empresa.usuarios else 0
    print(f"Total de usuários vinculados: {total_usuarios}")
    
    if total_usuarios > 0:
        usuarios_nomes = ', '.join([u.email for u in empresa.usuarios])
        print(f"BLOQUEADO: Empresa tem {total_usuarios} usuários")
        flash(f'Não é possível excluir a empresa "{empresa.nome}" pois ela possui {total_usuarios} usuário(s) vinculado(s): {usuarios_nomes}. Remova os vínculos primeiro.', 'warning')
        return redirect(url_for('gerenciar_empresas'))
    
    # Se passou nas validações, pode deletar
    nome_empresa = empresa.nome
    print(f"VALIDAÇÕES OK! Deletando empresa...")
    
    try:
        db.session.delete(empresa)
        db.session.commit()
        print(f"✅ Empresa '{nome_empresa}' excluída com sucesso!")
        flash(f'Empresa "{nome_empresa}" removida com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO ao excluir: {str(e)}")
        flash(f'Erro ao excluir empresa: {str(e)}', 'danger')
    
    return redirect(url_for('gerenciar_empresas'))

# ============================================================================
# ROTAS ADMINISTRATIVAS DE SEGMENTOS
# ============================================================================

@app.route('/gerenciar_segmentos')
@permissao_requerida('supervisor', 'adm')
def gerenciar_segmentos():
    """Lista todos os segmentos para gerenciamento"""
    segmentos = Segmento.query.order_by(Segmento.nome).all()
    
    # Contar empresas por segmento
    segmentos_info = []
    for seg in segmentos:
        total_empresas = Empresa.query.filter_by(segmento_id=seg.id).count()
        segmentos_info.append({
            'id': seg.id,
            'nome': seg.nome,
            'total_empresas': total_empresas
        })
    
    return render_template('admin/gerenciar_segmentos.html', segmentos=segmentos_info)

@app.route('/novo_segmento', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def novo_segmento():
    """Cria um novo segmento"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip().upper()
        
        if not nome:
            flash('Nome do segmento é obrigatório.', 'danger')
            return redirect(url_for('novo_segmento'))
        
        # Verificar se já existe
        if Segmento.query.filter_by(nome=nome).first():
            flash('Já existe um segmento com este nome.', 'warning')
            return redirect(url_for('novo_segmento'))
        
        novo_seg = Segmento(nome=nome)
        db.session.add(novo_seg)
        db.session.commit()
        
        flash(f'Segmento "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('gerenciar_segmentos'))
    
    return render_template('admin/form_segmento.html', segmento=None)

@app.route('/editar_segmento/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_segmento(id):
    """Edita um segmento existente"""
    segmento = Segmento.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip().upper()
        
        if not nome:
            flash('Nome do segmento é obrigatório.', 'danger')
            return redirect(url_for('editar_segmento', id=id))
        
        segmento.nome = nome
        db.session.commit()
        
        flash(f'Segmento "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('gerenciar_segmentos'))
    
    return render_template('admin/form_segmento.html', segmento=segmento)

@app.route('/deletar_segmento/<int:id>', methods=['POST'])
@permissao_requerida('adm')
def deletar_segmento(id):
    """Deleta um segmento (apenas se não tiver empresas vinculadas)"""
    segmento = Segmento.query.get_or_404(id)
    
    # Verificar se tem empresas vinculadas
    total_empresas = Empresa.query.filter_by(segmento_id=segmento.id).count()
    if total_empresas > 0:
        flash(f'Não é possível deletar o segmento "{segmento.nome}" pois existem {total_empresas} empresas vinculadas.', 'danger')
        return redirect(url_for('gerenciar_segmentos'))
    
    nome = segmento.nome
    db.session.delete(segmento)
    db.session.commit()
    
    flash(f'Segmento "{nome}" removido com sucesso!', 'success')
    return redirect(url_for('gerenciar_segmentos'))

# ============================================================================
# FIM DAS ROTAS ADMINISTRATIVAS DE SEGMENTOS
# ============================================================================

@app.route('/deletar_pendencia/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def deletar_pendencia(id):
    pendencia = Pendencia.query.get_or_404(id)
    db.session.delete(pendencia)
    db.session.commit()
    flash('Pendência removida com sucesso!', 'success')
    # Recupera filtros do formulário
    empresa = request.form.get('empresa')
    tipo_pendencia = request.form.get('tipo_pendencia')
    busca = request.form.get('busca')
    return redirect(url_for('dashboard', empresa=empresa, tipo_pendencia=tipo_pendencia, busca=busca))

@app.route('/acesso_negado')
def acesso_negado():
    return render_template('acesso_negado.html'), 403

@app.route('/log_suporte', methods=['POST'])
def log_suporte():
    """Registra log de abertura do modal de suporte"""
    if 'usuario_id' in session:
        log = LogAlteracao(
            pendencia_id=0,  # 0 indica que é uma ação de sistema
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

@app.route('/baixar_anexo/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm', 'operador')
def baixar_anexo(pendencia_id):
    pendencia = Pendencia.query.get_or_404(pendencia_id)
    if not pendencia.nota_fiscal_arquivo:
        flash('Nenhum anexo encontrado para esta pendência.', 'warning')
        return redirect(url_for('dashboard'))
    
    arquivo_path = os.path.join('static/notas_fiscais', pendencia.nota_fiscal_arquivo)
    if not os.path.exists(arquivo_path):
        flash('Arquivo não encontrado no servidor.', 'error')
        return redirect(url_for('dashboard'))
    
    return send_file(arquivo_path, as_attachment=True, download_name=pendencia.nota_fiscal_arquivo)

def checar_permissao(tipo_usuario, funcionalidade):
    permissao = PermissaoUsuarioTipo.query.filter_by(tipo_usuario=tipo_usuario, funcionalidade=funcionalidade).first()
    if permissao:
        return permissao.permitido
    # Se não houver registro, por padrão permite (ou pode retornar False, conforme política)
    return True

def checar_permissao_usuario(usuario_id, tipo_usuario, funcionalidade):
    p = PermissaoUsuarioPersonalizada.query.filter_by(usuario_id=usuario_id, funcionalidade=funcionalidade).first()
    if p:
        return p.permitido
    return checar_permissao(tipo_usuario, funcionalidade)

def atualizar_permissao(tipo_usuario, funcionalidade, permitido):
    permissao = PermissaoUsuarioTipo.query.filter_by(tipo_usuario=tipo_usuario, funcionalidade=funcionalidade).first()
    if permissao:
        permissao.permitido = permitido
    else:
        permissao = PermissaoUsuarioTipo(tipo_usuario=tipo_usuario, funcionalidade=funcionalidade, permitido=permitido)
        db.session.add(permissao)
    db.session.commit()

def configurar_permissoes_padrao():
    """Configura as permissões padrão do sistema"""
    # Permissões para operadores
    atualizar_permissao('operador', 'importar_planilha', True)
    atualizar_permissao('operador', 'cadastrar_pendencia', True)
    atualizar_permissao('operador', 'editar_pendencia', True)
    atualizar_permissao('operador', 'baixar_anexo', True)
    atualizar_permissao('operador', 'aprovar_pendencia', True)
    atualizar_permissao('operador', 'recusar_pendencia', True)
    atualizar_permissao('operador', 'visualizar_relatorios', True)
    
    # Permissões para supervisores
    atualizar_permissao('supervisor', 'importar_planilha', True)
    atualizar_permissao('supervisor', 'cadastrar_pendencia', True)
    atualizar_permissao('supervisor', 'editar_pendencia', True)
    atualizar_permissao('supervisor', 'baixar_anexo', True)
    atualizar_permissao('supervisor', 'aprovar_pendencia', True)
    atualizar_permissao('supervisor', 'recusar_pendencia', True)
    atualizar_permissao('supervisor', 'exportar_logs', True)
    atualizar_permissao('supervisor', 'gerenciar_empresas', True)
    atualizar_permissao('supervisor', 'visualizar_relatorios', True)
    
    # Permissões para clientes
    atualizar_permissao('cliente', 'cadastrar_pendencia', False)
    atualizar_permissao('cliente', 'editar_pendencia', False)
    atualizar_permissao('cliente', 'importar_planilha', False)
    atualizar_permissao('cliente', 'baixar_anexo', False)
    atualizar_permissao('cliente', 'aprovar_pendencia', False)
    atualizar_permissao('cliente', 'recusar_pendencia', False)
    atualizar_permissao('cliente', 'exportar_logs', False)
    atualizar_permissao('cliente', 'gerenciar_usuarios', False)
    atualizar_permissao('cliente', 'gerenciar_empresas', False)
    atualizar_permissao('cliente', 'visualizar_relatorios', False)
    
    # Permissões para cliente_supervisor (novo tipo - visualização avançada sem edição)
    atualizar_permissao('cliente_supervisor', 'cadastrar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'editar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'importar_planilha', False)
    atualizar_permissao('cliente_supervisor', 'baixar_anexo', True)
    atualizar_permissao('cliente_supervisor', 'aprovar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'recusar_pendencia', False)
    atualizar_permissao('cliente_supervisor', 'exportar_logs', True)
    atualizar_permissao('cliente_supervisor', 'gerenciar_usuarios', False)
    atualizar_permissao('cliente_supervisor', 'gerenciar_empresas', False)
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

from functools import wraps

def permissao_funcionalidade(funcionalidade):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tipo = session.get('usuario_tipo')
            if not checar_permissao(tipo, funcionalidade):
                flash('Acesso não autorizado para esta funcionalidade.', 'danger')
                return redirect(url_for('acesso_negado'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/gerenciar_permissoes', methods=['GET', 'POST'])
@permissao_requerida('adm')
def gerenciar_permissoes():
    TIPOS_USUARIO = ['supervisor', 'operador', 'cliente', 'cliente_supervisor']
    FUNCIONALIDADES = [
        ('cadastrar_pendencia', 'Cadastrar Pendência'),
        ('editar_pendencia', 'Editar Pendência'),
        ('importar_planilha', 'Importar Planilha'),
        ('baixar_anexo', 'Baixar Anexo'),
        ('aprovar_pendencia', 'Aprovar Pendência'),
        ('recusar_pendencia', 'Recusar Pendência'),
        ('exportar_logs', 'Exportar Logs'),
        ('gerenciar_usuarios', 'Gerenciar Usuários'),
        ('gerenciar_empresas', 'Gerenciar Empresas'),
        ('visualizar_relatorios', 'Visualizar Relatórios'),
    ]
    if request.method == 'POST':
        for tipo in TIPOS_USUARIO:
            for func, _ in FUNCIONALIDADES:
                permitido = request.form.get(f'{tipo}_{func}') == 'on'
                atualizar_permissao(tipo, func, permitido)
        flash('Permissões atualizadas com sucesso!', 'success')
        return redirect(url_for('gerenciar_permissoes'))
    # Montar matriz de permissões
    permissoes = {}
    for tipo in TIPOS_USUARIO:
        permissoes[tipo] = {}
        for func, _ in FUNCIONALIDADES:
            permissoes[tipo][func] = checar_permissao(tipo, func)
    return render_template('admin/gerenciar_permissoes.html',
        tipos_usuario=TIPOS_USUARIO,
        funcionalidades=FUNCIONALIDADES,
        permissoes=permissoes
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        db.create_all()
        ensure_segmento_schema()  # Garante estrutura de segmentos
        criar_usuarios_iniciais()
        migrar_empresas_existentes()  # Agora também migra segmentos
        configurar_permissoes_padrao()
    app.run(host='0.0.0.0', port=port, debug=True) 