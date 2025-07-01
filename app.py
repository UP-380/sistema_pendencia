from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import os
from dotenv import load_dotenv
import pandas as pd
import requests
import io
import openpyxl
import csv
import pytz
from functools import wraps
from urllib.parse import quote

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pendencias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    'Nota Fiscal Não Anexada'
]

# Função utilitária para data/hora local
BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')
def now_brazil():
    return datetime.now(BRAZIL_TZ)

usuario_empresas = db.Table('usuario_empresas',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('empresa_id', db.Integer, db.ForeignKey('empresa.id'))
)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class Pendencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(50), nullable=False)
    tipo_pendencia = db.Column(db.String(30), nullable=False)
    banco = db.Column(db.String(50), nullable=False)
    data = db.Column(db.Date, nullable=False)
    fornecedor_cliente = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.String(300), default='DO QUE SE TRATA?')
    resposta_cliente = db.Column(db.String(300))
    email_cliente = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), default='Pendente Cliente')
    token_acesso = db.Column(db.String(100), unique=True, default=lambda: secrets.token_urlsafe(16))
    data_resposta = db.Column(db.DateTime)
    modificado_por = db.Column(db.String(50))
    nota_fiscal_arquivo = db.Column(db.String(300))  # Caminho do arquivo da nota fiscal

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
            tipo='cliente'
        )
        db.session.add(cliente)
    db.session.commit()

def migrar_empresas_existentes():
    """Migra as empresas da lista EMPRESAS para o model Empresa"""
    for nome_empresa in EMPRESAS:
        if not Empresa.query.filter_by(nome=nome_empresa).first():
            nova_empresa = Empresa(nome=nome_empresa)
            db.session.add(nova_empresa)
    db.session.commit()

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            session['usuario_id'] = usuario.id
            session['usuario_email'] = usuario.email
            session['usuario_tipo'] = usuario.tipo
            # Redirecionar para o painel de empresas após login
            return redirect(url_for('pre_dashboard'))
        else:
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

@app.route('/empresas')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente')
def pre_dashboard():
    if session.get('usuario_tipo') == 'adm':
        empresas = Empresa.query.all()
    else:
        usuario = Usuario.query.get(session['usuario_id'])
        empresas = usuario.empresas
    empresas_info = []
    tipo_counts = {tipo: 0 for tipo in TIPOS_PENDENCIA}
    status_labels = ['Em Aberto', 'Resolvida']
    status_counts = [0, 0]
    for empresa in empresas:
        pendencias = Pendencia.query.filter(Pendencia.empresa == empresa.nome).all()
        pendencias_abertas = [p for p in pendencias if p.status != 'Resolvida']
        empresas_info.append({
            'nome': empresa.nome,
            'abertas': len(pendencias_abertas)
        })
        for p in pendencias:
            if p.tipo_pendencia in tipo_counts:
                tipo_counts[p.tipo_pendencia] += 1
            if p.status == 'Resolvida':
                status_counts[1] += 1
            else:
                status_counts[0] += 1
    return render_template(
        'pre_dashboard.html',
        empresas_info=empresas_info,
        tipos_pendencia=TIPOS_PENDENCIA,
        tipo_counts=[tipo_counts[t] for t in TIPOS_PENDENCIA],
        status_labels=status_labels,
        status_counts=status_counts
    )

@app.route('/dashboard', methods=['GET'])
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente')
def dashboard():
    empresa_filtro = request.args.get('empresa', EMPRESAS[0])
    tipo_filtro = request.args.get('tipo_pendencia', TIPOS_PENDENCIA[0])
    busca = request.args.get('busca', '')
    pendencias_empresa = Pendencia.query.filter_by(empresa=empresa_filtro).filter(Pendencia.status != 'Resolvida').all()
    query = Pendencia.query.filter_by(empresa=empresa_filtro, tipo_pendencia=tipo_filtro).filter(Pendencia.status != 'Resolvida')
    if busca:
        query = query.filter(
            db.or_(Pendencia.fornecedor_cliente.ilike(f'%{busca}%'),
                    Pendencia.banco.ilike(f'%{busca}%'),
                    Pendencia.observacao.ilike(f'%{busca}%'))
        )
    pendencias = query.order_by(Pendencia.data.desc()).all()
    return render_template('dashboard.html', pendencias=pendencias, pendencias_empresa=pendencias_empresa, empresas=EMPRESAS, empresa_filtro=empresa_filtro, tipos_pendencia=TIPOS_PENDENCIA, tipo_filtro=tipo_filtro, busca=busca)

@app.route('/nova', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
def nova_pendencia():
    if request.method == 'POST':
        try:
            empresa = request.form['empresa']
            tipo_pendencia = request.form['tipo_pendencia']
            banco = request.form['banco']
            data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
            fornecedor_cliente = request.form['fornecedor_cliente']
            valor = float(request.form['valor'])
            observacao = request.form.get('observacao') or 'DO QUE SE TRATA?'
            email_cliente = request.form.get('email_cliente')
            nota_fiscal_arquivo = None
            if tipo_pendencia == 'Nota Fiscal Não Anexada' and 'nota_fiscal_arquivo' in request.files:
                file = request.files['nota_fiscal_arquivo']
                if file and file.filename:
                    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                    file.save(os.path.join('static/notas_fiscais', filename))
                    nota_fiscal_arquivo = filename
            nova_p = Pendencia(
                empresa=empresa,
                tipo_pendencia=tipo_pendencia,
                banco=banco,
                data=data,
                fornecedor_cliente=fornecedor_cliente,
                valor=valor,
                observacao=observacao,
                email_cliente=email_cliente,
                status='Pendente Cliente',
                nota_fiscal_arquivo=nota_fiscal_arquivo
            )
            db.session.add(nova_p)
            db.session.commit()
            enviar_email_cliente(nova_p)
            flash('Pendência criada com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Erro ao criar pendência: {str(e)}', 'error')
            return redirect(url_for('nova_pendencia'))
    return render_template('nova_pendencia.html', empresas=EMPRESAS, tipos_pendencia=TIPOS_PENDENCIA)

@app.route('/pendencia/<token>', methods=['GET', 'POST'])
def ver_pendencia(token):
    pendencia = Pendencia.query.filter_by(token_acesso=token).first_or_404()
    if request.method == 'POST':
        pendencia.resposta_cliente = request.form['resposta']
        # Upload de nota fiscal pelo cliente
        if pendencia.tipo_pendencia == 'Nota Fiscal Não Anexada' and 'nota_fiscal_arquivo' in request.files:
            file = request.files['nota_fiscal_arquivo']
            if file and file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join('static/notas_fiscais', filename))
                pendencia.nota_fiscal_arquivo = filename
        pendencia.status = 'Pendente UP'
        pendencia.data_resposta = now_brazil()
        db.session.commit()
        flash('Resposta enviada com sucesso!', 'success')
        return redirect(url_for('pre_dashboard'))
    return render_template('ver_pendencia.html', pendencia=pendencia)

@app.route('/resolver/<int:id>')
@permissao_requerida('supervisor', 'adm')
def resolver_pendencia(id):
    pendencia = Pendencia.query.get_or_404(id)
    valor_anterior = pendencia.status
    pendencia.status = 'Resolvida'
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

@app.route('/importar', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def importar_planilha():
    preview = None
    erros = []
    if request.method == 'POST':
        if request.form.get('confirmar_importacao') == '1' and 'preview_data' in session and 'preview_filename' in session:
            # Segunda etapa: confirmar importação usando dados em sessão
            try:
                df = pd.read_json(session['preview_data'])
                for idx, row in df.iterrows():
                    empresa = row.get('EMPRESA', '').strip()
                    tipo_pendencia = row.get('TIPO DE PENDÊNCIA', '').strip()
                    banco = row.get('BANCO', '').strip()
                    data = row.get('DATA DE COMPETÊNCIA')
                    if pd.isnull(data):
                        continue
                    if isinstance(data, str):
                        data = datetime.strptime(data, '%d/%m/%Y').date()
                    else:
                        data = data.date() if hasattr(data, 'date') else data
                    fornecedor_cliente = row.get('FORNECEDOR/CLIENTE', '').strip()
                    valor = float(str(row.get('VALOR', '0')).replace('R$', '').replace('.', '').replace(',', '.'))
                    observacao = row.get('OBSERVAÇÃO', 'DO QUE SE TRATA?')
                    if not empresa or not tipo_pendencia:
                        continue
                    nova_p = Pendencia(
                        empresa=empresa,
                        tipo_pendencia=tipo_pendencia,
                        banco=banco,
                        data=data,
                        fornecedor_cliente=fornecedor_cliente,
                        valor=valor,
                        observacao=observacao
                    )
                    db.session.add(nova_p)
                db.session.commit()
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
                flash('Pendências importadas com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                erros.append(f'Erro ao importar: {e}')
        else:
            file = request.files.get('arquivo')
            if file:
                try:
                    df = pd.read_excel(file)
                    preview = df.head(5).to_dict(orient='records')
                    # Validação
                    for idx, row in df.iterrows():
                        if not row.get('EMPRESA') or not row.get('TIPO DE PENDÊNCIA') or not row.get('BANCO') or not row.get('DATA DE COMPETÊNCIA') or not row.get('FORNECEDOR/CLIENTE') or not row.get('VALOR'):
                            erros.append(f"Linha {idx+2}: Dados obrigatórios ausentes.")
                    if not erros:
                        # Salva o DataFrame em sessão para confirmação posterior
                        session['preview_data'] = df.to_json()
                        session['preview_filename'] = file.filename
                except Exception as e:
                    erros.append(f'Erro ao processar arquivo: {e}')
            else:
                flash('Nenhum arquivo selecionado.', 'error')
    return render_template('importar_planilha.html', empresas=EMPRESAS, preview=preview, erros=erros)

@app.route('/historico_importacoes')
@permissao_requerida('supervisor', 'adm')
def historico_importacoes():
    historico = Importacao.query.order_by(Importacao.data_hora.desc()).limit(20).all()
    return render_template('historico_importacoes.html', historico=historico)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_pendencia(id):
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
            'valor': float(request.form['valor']),
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
    return render_template('editar_pendencia.html', pendencia=pendencia, empresas=EMPRESAS, tipos_pendencia=TIPOS_PENDENCIA)

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

@app.route('/editar_observacao/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'cliente')
def editar_observacao(id):
    pendencia = Pendencia.query.get_or_404(id)
    if request.method == 'POST':
        valor_anterior = pendencia.observacao
        novo_valor = request.form.get('observacao') or 'DO QUE SE TRATA?'
        pendencia.observacao = novo_valor
        pendencia.modificado_por = 'USUARIO'
        pendencia.status = 'Pendente UP'
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
        notificar_teams(pendencia)
        flash('Observação atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editar_observacao.html', pendencia=pendencia)

@app.route('/resolvidas', methods=['GET'])
@permissao_requerida('supervisor', 'adm')
def dashboard_resolvidas():
    empresa_filtro = request.args.get('empresa', EMPRESAS[0])
    tipo_filtro = request.args.get('tipo_pendencia', TIPOS_PENDENCIA[0])
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    def filtro_data(query):
        if data_inicio:
            query = query.filter(Pendencia.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Pendencia.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
        return query
    resolvidas = filtro_data(Pendencia.query.filter_by(empresa=empresa_filtro, tipo_pendencia=tipo_filtro, status='Resolvida')).order_by(Pendencia.data.desc()).all()
    logs_por_pendencia = {}
    for pend in resolvidas:
        logs_por_pendencia[pend.id] = LogAlteracao.query.filter_by(pendencia_id=pend.id).order_by(LogAlteracao.data_hora.desc()).all()
    return render_template(
        'resolvidas.html',
        resolvidas=resolvidas,
        logs_por_pendencia=logs_por_pendencia,
        empresas=EMPRESAS,
        empresa_filtro=empresa_filtro,
        tipos_pendencia=TIPOS_PENDENCIA,
        tipo_filtro=tipo_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

@app.route('/logs/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm')
def ver_logs_pendencia(pendencia_id):
    logs = LogAlteracao.query.filter_by(pendencia_id=pendencia_id).order_by(LogAlteracao.data_hora.desc()).all()
    pendencia = Pendencia.query.get_or_404(pendencia_id)
    return render_template('logs_pendencia.html', logs=logs, pendencia=pendencia)

@app.route('/exportar_logs/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm')
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
@permissao_requerida('supervisor', 'adm')
def logs_recentes():
    logs = LogAlteracao.query.order_by(LogAlteracao.data_hora.desc()).limit(50).all()
    return render_template('logs_recentes.html', logs=logs)

@app.route('/exportar_logs_csv')
@permissao_requerida('supervisor', 'adm')
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

@app.route('/')
@permissao_requerida('supervisor', 'adm')
def index():
    return redirect(url_for('dashboard'))

@app.route('/gerenciar_usuarios')
@permissao_requerida('supervisor', 'adm')
def gerenciar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/gerenciar_usuarios.html', usuarios=usuarios)

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
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))
    return render_template('admin/novo_usuario.html', empresas=empresas)

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
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))
    empresas_permitidas = [e.id for e in usuario.empresas]
    return render_template('admin/editar_usuario.html', usuario=usuario, empresas=empresas, empresas_permitidas=empresas_permitidas)

@app.route('/gerenciar_empresas')
@permissao_requerida('supervisor', 'adm')
def gerenciar_empresas():
    empresas = Empresa.query.all()
    return render_template('admin/gerenciar_empresas.html', empresas=empresas)

@app.route('/nova_empresa', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def nova_empresa():
    if request.method == 'POST':
        nome = request.form['nome']
        if Empresa.query.filter_by(nome=nome).first():
            flash('Empresa já cadastrada.', 'danger')
            return redirect(url_for('nova_empresa'))
        nova = Empresa(nome=nome)
        db.session.add(nova)
        db.session.commit()
        flash('Empresa criada com sucesso!', 'success')
        return redirect(url_for('gerenciar_empresas'))
    return render_template('admin/form_empresa.html', title='Nova Empresa')

@app.route('/editar_empresa/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        empresa.nome = request.form['nome']
        db.session.commit()
        flash('Empresa atualizada com sucesso!', 'success')
        return redirect(url_for('gerenciar_empresas'))
    return render_template('admin/form_empresa.html', empresa=empresa, title='Editar Empresa')

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
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    flash('Empresa removida com sucesso!', 'success')
    return redirect(url_for('gerenciar_empresas'))

@app.route('/deletar_pendencia/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def deletar_pendencia(id):
    pendencia = Pendencia.query.get_or_404(id)
    db.session.delete(pendencia)
    db.session.commit()
    flash('Pendência removida com sucesso!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/acesso_negado')
def acesso_negado():
    return render_template('acesso_negado.html'), 403

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        db.create_all()
        criar_usuarios_iniciais()
        migrar_empresas_existentes()
    app.run(host='0.0.0.0', port=port, debug=True) 