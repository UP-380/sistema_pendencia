from flask import Blueprint, jsonify, session, request
from werkzeug.security import check_password_hash
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa, Segmento
from app.models.pendencia import Pendencia, LogAlteracao
from app.extensions import db
from app.services.business import obter_empresas_para_usuario
from app.services.rules import TIPO_IMPORT_MAP
from app.services.notifications import (
    notificar_teams_pendente_supervisor,
    notificar_teams_recusa_cliente,
    notificar_teams_recusa_supervisor
)
from app.utils.decorators import api_auth_required
from app.utils.helpers import now_brazil
from datetime import datetime, timedelta
from sqlalchemy import func, or_

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API de login"""
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    
    usuario = Usuario.query.filter_by(email=email).first()
    
    if usuario:
        senha_valida = False
        if hasattr(usuario, 'senha_hash'):
            senha_valida = check_password_hash(usuario.senha_hash, senha)
        elif hasattr(usuario, 'senha'):
            senha_valida = check_password_hash(usuario.senha, senha)
            
        if senha_valida:
            session.permanent = True
            session['usuario_id'] = usuario.id
            session['usuario_email'] = usuario.email
            session['usuario_tipo'] = usuario.tipo
            
            return jsonify({
                'success': True,
                'user': {
                    'id': usuario.id,
                    'email': usuario.email,
                    'tipo': usuario.tipo
                }
            })
            
    return jsonify({'success': False, 'message': 'E-mail ou senha inválidos.'}), 401

    return jsonify({'success': False, 'message': 'E-mail ou senha inválidos.'}), 401

@api_bp.route('/empresas', methods=['GET'])
@api_auth_required
def api_empresas():
    # Obter filtros de data da URL
    data_abertura_inicio = request.args.get('data_abertura_inicio', '')
    data_abertura_fim = request.args.get('data_abertura_fim', '')
    data_resolucao_inicio = request.args.get('data_resolucao_inicio', '')
    data_resolucao_fim = request.args.get('data_resolucao_fim', '')
    
    # ===== NOVOS FILTROS AVANÇADOS =====
    segmentos_selecionados = request.args.getlist('segmentos')
    clientes_selecionados = request.args.getlist('clientes')
    operadores_selecionados = request.args.getlist('operadores')
    supervisores_selecionados = request.args.getlist('supervisores') if session.get('usuario_tipo') == 'adm' else []
    
    # ===== QUERY BASE DE EMPRESAS =====
    if session.get('usuario_tipo') == 'adm':
        query_empresas = Empresa.query
    else:
        usuario = Usuario.query.get(session['usuario_id'])
        query_empresas = Empresa.query.filter(Empresa.id.in_([e.id for e in usuario.empresas]))
        
    # ===== APLICAR FILTRO DE SEGMENTO =====
    if segmentos_selecionados:
        try:
            segmentos_ids = [int(s) for s in segmentos_selecionados]
            query_empresas = query_empresas.filter(Empresa.segmento_id.in_(segmentos_ids))
        except (ValueError, TypeError):
            pass
            
    # ===== APLICAR FILTRO DE CLIENTE (Nome da Empresa) =====
    if clientes_selecionados:
        query_empresas = query_empresas.filter(Empresa.nome.in_(clientes_selecionados))
        
    # ===== APLICAR FILTRO DE OPERADOR =====
    if operadores_selecionados:
        try:
            operadores_ids = [int(o) for o in operadores_selecionados]
            empresas_operadores = db.session.query(usuario_empresas.c.empresa_id).filter(
                usuario_empresas.c.usuario_id.in_(operadores_ids)
            ).distinct().all()
            empresas_ids = [e[0] for e in empresas_operadores]
            if empresas_ids:
                query_empresas = query_empresas.filter(Empresa.id.in_(empresas_ids))
            else:
                query_empresas = query_empresas.filter(Empresa.id == -1)
        except (ValueError, TypeError):
            pass

    # ===== APLICAR FILTRO DE SUPERVISOR (apenas adm) =====
    if session.get('usuario_tipo') == 'adm' and supervisores_selecionados:
        try:
            supervisores_ids = [int(s) for s in supervisores_selecionados]
            empresas_supervisores = db.session.query(usuario_empresas.c.empresa_id).filter(
                usuario_empresas.c.usuario_id.in_(supervisores_ids)
            ).distinct().all()
            empresas_ids = [e[0] for e in empresas_supervisores]
            if empresas_ids:
                query_empresas = query_empresas.filter(Empresa.id.in_(empresas_ids))
            else:
                query_empresas = query_empresas.filter(Empresa.id == -1)
        except (ValueError, TypeError):
            pass
            
    # ===== EXECUTAR QUERY DE EMPRESAS =====
    empresas = query_empresas.all()
    
    result_empresas = []
    tipo_counts = {}
    abertas_count = 0
    resolvidas_count = 0
    
    for empresa in empresas:
        # Query base de pendências
        query = Pendencia.query.filter(Pendencia.empresa == empresa.nome)
        
        # Filtros de data
        if data_abertura_inicio:
            try:
                dt = datetime.strptime(data_abertura_inicio, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_abertura >= dt)
            except: pass
        if data_abertura_fim:
            try:
                dt = datetime.strptime(data_abertura_fim, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_abertura <= dt)
            except: pass
        if data_resolucao_inicio:
            try:
                dt = datetime.strptime(data_resolucao_inicio, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_resolucao >= dt)
            except: pass
        if data_resolucao_fim:
            try:
                dt = datetime.strptime(data_resolucao_fim, '%Y-%m-%d').date()
                query = query.filter(Pendencia.data_resolucao <= dt)
            except: pass
            
        pendencias = query.all()
        pendencias_abertas = [p for p in pendencias if p.status != 'RESOLVIDA']
        pendencias_resolvidas = [p for p in pendencias if p.status == 'RESOLVIDA']
        
        result_empresas.append({
            'id': empresa.id,
            'nome': empresa.nome,
            'abertas': len(pendencias_abertas),
            'resolvidas': len(pendencias_resolvidas)
        })
        
        # Agregação global
        for p in pendencias:
            if p.tipo_pendencia not in tipo_counts:
                tipo_counts[p.tipo_pendencia] = 0
            tipo_counts[p.tipo_pendencia] += 1
            
            if p.status == 'RESOLVIDA':
                resolvidas_count += 1
            else:
                abertas_count += 1

    return jsonify({
        'empresas': result_empresas,
        'tipos_labels': list(tipo_counts.keys()),
        'tipos_valores': list(tipo_counts.values()),
        'abertas_count': abertas_count,
        'resolvidas_count': resolvidas_count
    })



@api_bp.route('/operador/pendencias', methods=['GET'])
@api_auth_required
def api_operador_pendencias():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        return jsonify({'message': 'Você não tem acesso a nenhuma empresa.'}), 403
    
    empresa_filtro = request.args.get('empresa')
    tipo_filtro = request.args.get('tipo_pendencia')
    busca = request.args.get('busca', '')
    empresas_selecionadas = request.args.getlist('empresas')
    filtro_status = request.args.get('filtro_status', '')
    filtro_prazo = request.args.get('filtro_prazo', '')
    filtro_valor = request.args.get('filtro_valor', '')
    
    status_abertos_operador = ['PENDENTE OPERADOR UP', 'PENDENTE COMPLEMENTO CLIENTE', 'DEVOLVIDA AO OPERADOR']
    TIPOS_PENDENCIA = list(TIPO_IMPORT_MAP.keys())
    
    usuario = Usuario.query.get(session['usuario_id'])
    if session.get('usuario_tipo') == 'adm':
        empresas_permitidas = empresas_usuario
    else:
        empresas_permitidas = [e.nome for e in usuario.empresas] 
        
    # Indicadores por empresa
    pendencias_abertas_por_empresa = (
        db.session.query(Pendencia.empresa, func.count(Pendencia.id).label('quantidade'))
        .filter(Pendencia.status.in_(status_abertos_operador))
        .filter(Pendencia.empresa.in_(empresas_permitidas))
        .group_by(Pendencia.empresa)
        .having(func.count(Pendencia.id) > 0)
        .order_by(func.count(Pendencia.id).desc())
        .all()
    )
    
    # Base query
    query = Pendencia.query
    if empresas_selecionadas:
        query = query.filter(Pendencia.empresa.in_(empresas_selecionadas))
    elif empresa_filtro:
        query = query.filter(Pendencia.empresa == empresa_filtro)
    else:
        # Default: filter by allowed companies
         query = query.filter(Pendencia.empresa.in_(empresas_permitidas))

    
    if filtro_status:
        query = query.filter(Pendencia.status == filtro_status)
    else:
        query = query.filter(Pendencia.status.in_(status_abertos_operador))
        
    if tipo_filtro:
        query = query.filter(Pendencia.tipo_pendencia == tipo_filtro)

    if busca:
        query = query.filter(
            or_(
                Pendencia.fornecedor_cliente.ilike(f'%{busca}%'),
                Pendencia.banco.ilike(f'%{busca}%'),
                Pendencia.observacao.ilike(f'%{busca}%'),
                Pendencia.resposta_cliente.ilike(f'%{busca}%'),
                Pendencia.natureza_operacao.ilike(f'%{busca}%'),
                flask_cast(Pendencia.valor).ilike(f'%{busca}%'), # Helper workaround
                Pendencia.status.ilike(f'%{busca}%')
            )
        )
        
    # Validando busca com cast ou ignorando cast complexo no sqlite
    # Simplificando a busca para evitar erros de cast no SQLAlchemy/SQLite sem pre-config
    # Se precisar de busca exata em numero, ok.

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
    
    # Serialize logs separately? Or include?
    # Optimization: Fetch logs in bulk or lazily?
    # React expects pendencias array.
    
    result_pendencias = []
    logs_por_pendencia = {}
    
    for p in pendencias:
        p_dict = {
            'id': p.id,
            'tipo_pendencia': p.tipo_pendencia,
            'banco': p.banco,
            'data': p.data.strftime('%Y-%m-%d') if p.data else None,
            'fornecedor_cliente': p.fornecedor_cliente,
            'valor': p.valor,
            'resposta_cliente': p.resposta_cliente,
            'nota_fiscal_arquivo': p.nota_fiscal_arquivo,
            'status': p.status,
            'observacao': p.observacao,
            'natureza_operacao': p.natureza_operacao,
            'motivo_recusa_supervisor': p.motivo_recusa_supervisor,
            'motivo_recusa': p.motivo_recusa,
            'tipo_credito_debito': p.tipo_credito_debito
        }
        result_pendencias.append(p_dict)
        
        logs = LogAlteracao.query.filter_by(pendencia_id=p.id).order_by(LogAlteracao.data_hora.desc()).all()
        logs_por_pendencia[p.id] = [{
            'id': l.id,
            'data_hora': l.data_hora.isoformat(),
            'usuario': l.usuario,
            'tipo_usuario': l.tipo_usuario,
            'acao': l.acao,
            'campo_alterado': l.campo_alterado,
            'valor_anterior': l.valor_anterior,
            'valor_novo': l.valor_novo
        } for l in logs]

    return jsonify({
        'pendencias': result_pendencias,
        'empresas': empresas_usuario,
        'pendencias_abertas_por_empresa': [{'empresa': r[0], 'quantidade': r[1]} for r in pendencias_abertas_por_empresa],
        'logs_por_pendencia': logs_por_pendencia,
        'tipos_pendencia': TIPOS_PENDENCIA
    })

@api_bp.route('/operador/pendencia/<int:id>/natureza', methods=['POST'])
@api_auth_required
def api_informar_natureza(id):
    pendencia = Pendencia.query.get_or_404(id)
    data = request.get_json()
    natureza = data.get('natureza_operacao')
    
    if not natureza:
        return jsonify({'message': 'Natureza obrigatória'}), 400
        
    pendencia.natureza_operacao = natureza
    pendencia.status = 'PENDENTE SUPERVISOR UP'
    pendencia.modificado_por = session.get('usuario_email', 'Operador API')
    if pendencia.motivo_recusa_supervisor:
        pendencia.motivo_recusa_supervisor = None
        
    db.session.commit()
    
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email'),
        tipo_usuario='operador',
        data_hora=now_brazil(),
        acao='Informação de Natureza (API)',
        campo_alterado='status',
        valor_anterior='PENDENTE OPERADOR UP',
        valor_novo='PENDENTE SUPERVISOR UP'
    )
    db.session.add(log)
    db.session.commit()
    
    notificar_teams_pendente_supervisor(pendencia)
    
    return jsonify({'success': True})

@api_bp.route('/operador/pendencia/<int:id>/recusar', methods=['POST'])
@api_auth_required
def api_recusar_resposta(id):
    pendencia = Pendencia.query.get_or_404(id)
    data = request.get_json()
    motivo = data.get('motivo_recusa')
    
    if not motivo:
        return jsonify({'message': 'Motivo obrigatório'}), 400
        
    pendencia.motivo_recusa = motivo
    pendencia.status = 'PENDENTE COMPLEMENTO CLIENTE'
    pendencia.modificado_por = session.get('usuario_email')
    
    db.session.commit()
    
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email'),
        tipo_usuario='operador',
        data_hora=now_brazil(),
        acao='Recusa de Resposta (API)',
        campo_alterado='status',
        valor_anterior='PENDENTE OPERADOR UP',
        valor_novo='PENDENTE COMPLEMENTO CLIENTE'
    )
    db.session.add(log)
    db.session.commit()
    
    notificar_teams_recusa_cliente(pendencia)
    return jsonify({'success': True})

@api_bp.route('/operador/pendencias/lote-enviar', methods=['POST'])
@api_auth_required
def api_lote_enviar_supervisor():
    data = request.get_json()
    ids = data.get('ids', [])
    count = 0
    
    for pid in ids:
        pendencia = Pendencia.query.get(pid)
        if pendencia and pendencia.status == 'PENDENTE OPERADOR UP':
            pendencia.status = 'PENDENTE SUPERVISOR UP'
            pendencia.modificado_por = session.get('usuario_email')
            log = LogAlteracao(
                pendencia_id=pendencia.id,
                usuario=session.get('usuario_email'),
                tipo_usuario='operador',
                data_hora=now_brazil(),
                acao='Envio em lote (API)',
                campo_alterado='status',
                valor_anterior='PENDENTE OPERADOR UP',
                valor_novo='PENDENTE SUPERVISOR UP'
            )
            db.session.add(log)
            count += 1
            
    db.session.commit()
    return jsonify({'success': True, 'count': count})
    
@api_bp.route('/supervisor/pendencias', methods=['GET'])
@api_auth_required
def api_supervisor_pendencias():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        return jsonify({'message': 'Voce nao tem acesso a nenhuma empresa.'}), 403
    
    empresa_filtro = request.args.get('empresa')
    tipo_filtro = request.args.get('tipo_pendencia')
    busca = request.args.get('busca', '')
    empresas_selecionadas = request.args.getlist('empresas')
    filtro_status = request.args.get('filtro_status', '')
    filtro_prazo = request.args.get('filtro_prazo', '')
    filtro_valor = request.args.get('filtro_valor', '')
    
    status_abertos_supervisor = ['PENDENTE SUPERVISOR UP']
    TIPOS_PENDENCIA = list(TIPO_IMPORT_MAP.keys())
    
    usuario = Usuario.query.get(session['usuario_id'])
    if session.get('usuario_tipo') == 'adm':
        empresas_permitidas = empresas_usuario
    else:
        empresas_permitidas = [e.nome for e in usuario.empresas]
        
    pendencias_abertas_por_empresa = (
        db.session.query(Pendencia.empresa, func.count(Pendencia.id).label('quantidade'))
        .filter(Pendencia.status.in_(status_abertos_supervisor))
        .filter(Pendencia.empresa.in_(empresas_permitidas))
        .group_by(Pendencia.empresa)
        .having(func.count(Pendencia.id) > 0)
        .order_by(func.count(Pendencia.id).desc())
        .all()
    )
    
    query = Pendencia.query
    if empresas_selecionadas:
        query = query.filter(Pendencia.empresa.in_(empresas_selecionadas))
    elif empresa_filtro:
        query = query.filter(Pendencia.empresa == empresa_filtro)
    else:
        query = query.filter(Pendencia.empresa.in_(empresas_permitidas))
        
    if filtro_status:
        query = query.filter(Pendencia.status == filtro_status)
    else:
        query = query.filter(Pendencia.status.in_(status_abertos_supervisor))
        
    if tipo_filtro:
        query = query.filter(Pendencia.tipo_pendencia == tipo_filtro)
        
    if busca:
         query = query.filter(
            or_(
                Pendencia.fornecedor_cliente.ilike(f'%{busca}%'),
                Pendencia.banco.ilike(f'%{busca}%'),
                Pendencia.observacao.ilike(f'%{busca}%'),
                Pendencia.resposta_cliente.ilike(f'%{busca}%'),
                Pendencia.natureza_operacao.ilike(f'%{busca}%'),
                flask_cast(Pendencia.valor).ilike(f'%{busca}%'),
                Pendencia.status.ilike(f'%{busca}%')
            )
        )
        
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
    
    # Calculate metrics
    limit_date = datetime.now().date() - timedelta(days=7)
    metricas = {
        'total': len(pendencias),
        'valor_alto': sum(1 for p in pendencias if p.valor >= 5000),
        'atrasadas': sum(1 for p in pendencias if p.data and p.data < limit_date)
    }
    
    result_pendencias = []
    logs_por_pendencia = {}
        
    for p in pendencias:
        days_open = (datetime.now().date() - p.data).days if p.data else 0
        p_dict = {
            'id': p.id,
            'tipo_pendencia': p.tipo_pendencia,
            'empresa': p.empresa,
            'banco': p.banco,
            'data': p.data.strftime('%Y-%m-%d') if p.data else None,
            'fornecedor_cliente': p.fornecedor_cliente,
            'valor': p.valor,
            'resposta_cliente': p.resposta_cliente,
            'nota_fiscal_arquivo': p.nota_fiscal_arquivo,
            'status': p.status,
            'observacao': p.observacao,
            'natureza_operacao': p.natureza_operacao,
            'motivo_recusa_supervisor': p.motivo_recusa_supervisor,
            'motivo_recusa': p.motivo_recusa,
            'dias_aberto': days_open,
            'tipo_credito_debito': p.tipo_credito_debito
        }
        result_pendencias.append(p_dict)
        
        logs = LogAlteracao.query.filter_by(pendencia_id=p.id).order_by(LogAlteracao.data_hora.desc()).all()
        logs_por_pendencia[p.id] = [{
            'id': l.id,
            'data_hora': l.data_hora.isoformat(),
            'usuario': l.usuario,
            'tipo_usuario': l.tipo_usuario,
            'acao': l.acao,
            'campo_alterado': l.campo_alterado,
            'valor_anterior': l.valor_anterior,
            'valor_novo': l.valor_novo
        } for l in logs]
        
    return jsonify({
        'pendencias': result_pendencias,
        'empresas': empresas_usuario,
        'pendencias_abertas_por_empresa': [{'empresa': r[0], 'quantidade': r[1]} for r in pendencias_abertas_por_empresa],
        'logs_por_pendencia': logs_por_pendencia,
        'tipos_pendencia': TIPOS_PENDENCIA,
        'metricas': metricas
    })

@api_bp.route('/supervisor/pendencia/<int:id>/resolver', methods=['POST'])
@api_auth_required
def api_resolver_pendencia(id):
    pendencia = Pendencia.query.get_or_404(id)
    if pendencia.status != 'PENDENTE SUPERVISOR UP':
        return jsonify({'message': 'Pendencia nao disponivel para resolucao'}), 400
        
    valor_anterior = pendencia.status
    pendencia.status = 'RESOLVIDA'
    pendencia.modificado_por = session.get('usuario_email')
    
    db.session.commit()
    
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email'),
        tipo_usuario='supervisor',
        data_hora=now_brazil(),
        acao='Resolucao (API)',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='Resolvida'
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/supervisor/pendencia/<int:id>/recusar', methods=['POST'])
@api_auth_required
def api_recusar_devolver(id):
    pendencia = Pendencia.query.get_or_404(id)
    data = request.get_json()
    motivo = data.get('motivo_recusa_supervisor')
    
    if not motivo:
        return jsonify({'message': 'Motivo obrigatorio'}), 400
        
    valor_anterior = pendencia.status
    pendencia.motivo_recusa_supervisor = motivo
    pendencia.status = 'DEVOLVIDA AO OPERADOR'
    pendencia.modificado_por = session.get('usuario_email')
    
    db.session.commit()
    
    log = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email'),
        tipo_usuario='supervisor',
        data_hora=now_brazil(),
        acao='Recusa Supervisor (API)',
        campo_alterado='status',
        valor_anterior=valor_anterior,
        valor_novo='DEVOLVIDA AO OPERADOR'
    )
    db.session.add(log)
    
    log_motivo = LogAlteracao(
        pendencia_id=pendencia.id,
        usuario=session.get('usuario_email'),
        tipo_usuario='supervisor',
        data_hora=now_brazil(),
        acao='Recusa Supervisor (API)',
        campo_alterado='motivo_recusa_supervisor',
        valor_anterior='',
        valor_novo=motivo
    )
    db.session.add(log_motivo)
    db.session.commit()
    
    notificar_teams_recusa_supervisor(pendencia)
    return jsonify({'success': True})

@api_bp.route('/supervisor/pendencias/lote-resolver', methods=['POST'])
@api_auth_required
def api_lote_resolver():
    data = request.get_json()
    ids = data.get('ids', [])
    count = 0
    
    for pid in ids:
        pendencia = Pendencia.query.get(pid)
        if pendencia and pendencia.status == 'PENDENTE SUPERVISOR UP':
            valor_anterior = pendencia.status
            pendencia.status = 'RESOLVIDA'
            pendencia.modificado_por = session.get('usuario_email')
            
            log = LogAlteracao(
                pendencia_id=pendencia.id,
                usuario=session.get('usuario_email'),
                tipo_usuario='supervisor',
                data_hora=now_brazil(),
                acao='Resolucao em Lote (API)',
                campo_alterado='status',
                valor_anterior=valor_anterior,
                valor_novo='Resolvida'
            )
            db.session.add(log)
            count += 1
            
    db.session.commit()
    return jsonify({'success': True, 'count': count})
    
def flask_cast(col):
    return db.cast(col, db.String)

@api_bp.route('/auth/logout', methods=['POST'])
@api_auth_required
def api_logout():
    """API de logout"""
    session.clear()
    return jsonify({'success': True})

@api_bp.route('/auth/check', methods=['GET'])
def api_check_auth():
    """Verifica se o usuário está autenticado"""
    if session.get('usuario_id'):
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session.get('usuario_id'),
                'email': session.get('usuario_email'),
                'tipo': session.get('usuario_tipo')
            }
        })
    return jsonify({'authenticated': False})
