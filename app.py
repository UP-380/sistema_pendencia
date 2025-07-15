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
    status = db.Column(db.String(50), default='PENDENTE CLIENTE')
    token_acesso = db.Column(db.String(100), unique=True, default=lambda: secrets.token_urlsafe(16))
    data_resposta = db.Column(db.DateTime)
    modificado_por = db.Column(db.String(50))
    nota_fiscal_arquivo = db.Column(db.String(300))  # Caminho do arquivo da nota fiscal
    natureza_operacao = db.Column(db.String(500))  # Campo para Natureza de Operação
    motivo_recusa = db.Column(db.String(500))  # Campo para motivo da recusa pelo operador

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
    
    # Novos status para o dashboard
    status_labels = ['PENDENTE CLIENTE', 'PENDENTE OPERADOR UP', 'PENDENTE SUPERVISOR UP', 'PENDENTE COMPLEMENTO CLIENTE', 'RESOLVIDA']
    status_counts = [0, 0, 0, 0, 0]
    
    for empresa in empresas:
        pendencias = Pendencia.query.filter(Pendencia.empresa == empresa.nome).all()
        pendencias_abertas = [p for p in pendencias if p.status != 'RESOLVIDA']
        empresas_info.append({
            'nome': empresa.nome,
            'abertas': len(pendencias_abertas)
        })
        for p in pendencias:
            if p.tipo_pendencia in tipo_counts:
                tipo_counts[p.tipo_pendencia] += 1
            
            # Contagem por status
            if p.status == 'PENDENTE CLIENTE':
                status_counts[0] += 1
            elif p.status == 'PENDENTE OPERADOR UP':
                status_counts[1] += 1
            elif p.status == 'PENDENTE SUPERVISOR UP':
                status_counts[2] += 1
            elif p.status == 'PENDENTE COMPLEMENTO CLIENTE':
                status_counts[3] += 1
            elif p.status == 'RESOLVIDA':
                status_counts[4] += 1
            else:
                # Status antigos (Pendente UP, etc.)
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
    
    return render_template(
        'dashboard.html', 
        pendencias=pendencias, 
        pendencias_empresa=pendencias_empresa, 
        empresas=empresas_usuario, 
        empresa_filtro=empresa_filtro, 
        tipos_pendencia=TIPOS_PENDENCIA, 
        tipo_filtro=tipo_filtro, 
        busca=busca
    )

@app.route('/nova', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
def nova_pendencia():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
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
                status='PENDENTE CLIENTE',
                nota_fiscal_arquivo=nota_fiscal_arquivo
            )
            db.session.add(nova_p)
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
    return render_template('nova_pendencia.html', empresas=empresas_usuario, tipos_pendencia=TIPOS_PENDENCIA)

@app.route('/pendencia/<token>', methods=['GET', 'POST'])
def ver_pendencia(token):
    pendencia = Pendencia.query.filter_by(token_acesso=token).first_or_404()
    if request.method == 'POST':
        # Verifica se é complemento de resposta ou resposta inicial
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
        
        # Log da alteração
        log = LogAlteracao(
            pendencia_id=pendencia.id,
            usuario='Cliente',
            tipo_usuario='cliente',
            data_hora=now_brazil(),
            acao=acao_log,
            campo_alterado='status',
            valor_anterior=valor_anterior,
            valor_novo=valor_novo
        )
        db.session.add(log)
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
    return render_template('ver_pendencia.html', pendencia=pendencia)

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

@app.route('/importar', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def importar_planilha():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('pre_dashboard'))
    
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
    return render_template('importar_planilha.html', empresas=empresas_usuario, preview=preview, erros=erros)

@app.route('/historico_importacoes')
@permissao_requerida('supervisor', 'adm')
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

@app.route('/operador/pendencias')
@permissao_requerida('operador', 'adm')
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
    status_abertos_operador = ['PENDENTE OPERADOR UP', 'PENDENTE COMPLEMENTO CLIENTE']
    
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
@permissao_requerida('operador', 'adm')
def operador_natureza_operacao(id):
    """Operador informa a Natureza de Operação"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE OPERADOR UP':
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
@permissao_requerida('operador', 'adm')
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
    
    # Notificação Teams para cliente
    notificar_teams_recusa_cliente(pendencia)
    
    flash('Resposta recusada. Cliente foi notificado para complementar.', 'success')
    return redirect(url_for('operador_pendencias'))

@app.route('/operador/lote_enviar_supervisor', methods=['POST'])
@permissao_requerida('operador', 'adm')
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

@app.route('/editar_observacao/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'cliente')
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
@permissao_requerida('supervisor', 'adm')
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

@app.route('/relatorio_operadores')
@permissao_requerida('adm', 'supervisor')
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
@permissao_requerida('supervisor', 'adm')
def index():
    return redirect(url_for('dashboard'))

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
        
        # Cria a nova empresa
        nova = Empresa(nome=nome)
        db.session.add(nova)
        db.session.flush()  # Gera o ID da empresa
        
        # Integra automaticamente a nova empresa em todo o sistema
        if integrar_nova_empresa(nova):
            flash(f'Empresa "{nome}" criada e integrada automaticamente em todo o sistema!', 'success')
        else:
            flash(f'Empresa "{nome}" criada, mas houve um problema na integração automática.', 'warning')
        
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
    # Recupera filtros do formulário
    empresa = request.form.get('empresa')
    tipo_pendencia = request.form.get('tipo_pendencia')
    busca = request.form.get('busca')
    return redirect(url_for('dashboard', empresa=empresa, tipo_pendencia=tipo_pendencia, busca=busca))

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
    TIPOS_USUARIO = ['supervisor', 'operador', 'cliente']
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
        criar_usuarios_iniciais()
        migrar_empresas_existentes()
    app.run(host='0.0.0.0', port=port, debug=True) 