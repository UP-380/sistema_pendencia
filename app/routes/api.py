from flask import Blueprint, jsonify, session, request, send_file, url_for
from werkzeug.security import check_password_hash
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa, Segmento
from app.models.pendencia import Pendencia, LogAlteracao
from app.extensions import db
from app.services.business import obter_empresas_para_usuario, pode_atuar_como_supervisor
from app.services.rules import TIPO_RULES, TIPO_IMPORT_MAP
from app.services.notifications import (
    notificar_teams_pendente_supervisor,
    notificar_teams_recusa_cliente,
    notificar_teams_recusa_supervisor
)
from app.utils.decorators import api_auth_required
from app.utils.helpers import now_brazil
from datetime import datetime, timedelta
from sqlalchemy import func, or_, case, extract, and_
import pandas as pd
import io

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
        # Supervisor, Operador e cliente veem apenas suas empresas vinculadas
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
        # Supervisor e Operador veem apenas suas empresas vinculadas
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
        # Supervisor vê apenas suas empresas vinculadas
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

@api_bp.route('/dashboard/metrics', methods=['GET'])
@api_auth_required
def api_dashboard_metrics():
    try:
        # 1. Filtros de Empresas
        empresas_selecionadas = request.args.getlist('empresas')
        
        # Validar acesso às empresas
        usuario = Usuario.query.get(session['usuario_id'])
        allowed_empresas = obter_empresas_para_usuario()
        
        if not allowed_empresas:
            # Retorna lista vazia em vez de erro 403 para não quebrar o frontend
            if request.args.get('only_companies') == 'true':
                return jsonify({'allowed_empresas': []})
            return jsonify({'message': 'Sem acesso a empresas'}), 403

        # Otimização: Se o frontend pedir apenas a lista (para preencher filtros), retorna rápido
        if request.args.get('only_companies') == 'true':
            return jsonify({
                'allowed_empresas': sorted(allowed_empresas)
            })

        # Se 'todas' ou vazio, usa todas permitidas. Se selecionadas, intersecta com permitidas.
        if not empresas_selecionadas or 'todas' in empresas_selecionadas:
            target_empresas = allowed_empresas
        else:
            target_empresas = [emp for emp in empresas_selecionadas if emp in allowed_empresas]
            
        if not target_empresas:
            return jsonify({'message': 'Nenhuma empresa válida selecionada'}), 400

        # 2. Query Base Construction
        base_clauses = [Pendencia.empresa.in_(target_empresas)]
        
        # Filtros de Data
        start_abertura = request.args.get('start_abertura')
        end_abertura = request.args.get('end_abertura')
        if start_abertura and end_abertura:
            base_clauses.append(func.date(Pendencia.data_abertura).between(start_abertura, end_abertura))
            
        start_pendencia = request.args.get('start_pendencia')
        end_pendencia = request.args.get('end_pendencia')
        if start_pendencia and end_pendencia:
            base_clauses.append(Pendencia.data.between(start_pendencia, end_pendencia))

        # Query Principal (Totais)
        query = Pendencia.query.filter(and_(*base_clauses))
        
        # 3. Métricas
        
        # A. Totais Gerais
        total = query.count()
        abertas = query.filter(Pendencia.status != 'RESOLVIDA').count()
        resolvidas = query.filter(Pendencia.status == 'RESOLVIDA').count()

        # B. Por Status
        por_status = db.session.query(Pendencia.status, func.count(Pendencia.id))\
            .filter(and_(*base_clauses))\
            .group_by(Pendencia.status).all()
        
        data_status = {s: count for s, count in por_status}
        
        # C. Por Tipo (Baseado em TIPO_RULES)
        por_tipo = db.session.query(Pendencia.tipo_pendencia, func.count(Pendencia.id))\
            .filter(and_(*base_clauses))\
            .group_by(Pendencia.tipo_pendencia).all()
            
        data_tipo = {}
        for t, count in por_tipo:
            label = TIPO_RULES.get(t, {}).get('label', t)
            data_tipo[label] = count

        # D. Por Empresa (Top 10)
        por_empresa = db.session.query(Pendencia.empresa, func.count(Pendencia.id))\
            .filter(and_(*base_clauses))\
            .group_by(Pendencia.empresa)\
            .order_by(func.count(Pendencia.id).desc())\
            .limit(10).all()
            
        data_empresa = [{'empresa': e, 'count': c} for e, c in por_empresa]

        # E. Evolução Abertura vs Fechamento
        six_months_ago = datetime.now().date() - timedelta(days=180)
        
        evolucao_abertura_query = db.session.query(
            func.strftime('%Y-%m', Pendencia.data_abertura).label('mes'),
            func.count(Pendencia.id)
        ).filter(and_(*base_clauses))
        
        if not (start_abertura and end_abertura):
            evolucao_abertura_query = evolucao_abertura_query.filter(Pendencia.data_abertura >= six_months_ago)
            
        evolucao_abertura = evolucao_abertura_query.group_by('mes').all()
        
        # Fechamento
        evolucao_fechamento_query = db.session.query(
            func.strftime('%Y-%m', Pendencia.data_resposta).label('mes'),
            func.count(Pendencia.id)
        ).filter(and_(*base_clauses))\
         .filter(Pendencia.status == 'RESOLVIDA')

        if not (start_abertura and end_abertura):
             evolucao_fechamento_query = evolucao_fechamento_query.filter(Pendencia.data_resposta >= six_months_ago)

        evolucao_fechamento = evolucao_fechamento_query.group_by('mes').all()

        evolucao_abertura_dict = {m: c for m, c in evolucao_abertura if m is not None}
        evolucao_fechamento_dict = {m: c for m, c in evolucao_fechamento if m is not None}
        
        # Remover Nones e ordenar
        keys_abertura = [k for k in evolucao_abertura_dict.keys() if k]
        keys_fechamento = [k for k in evolucao_fechamento_dict.keys() if k]
        all_months = sorted(list(set(keys_abertura + keys_fechamento)))
        
        data_evolucao = {
            'labels': all_months,
            'abertas': [evolucao_abertura_dict.get(m, 0) for m in all_months],
            'resolvidas': [evolucao_fechamento_dict.get(m, 0) for m in all_months]
        }

        return jsonify({
            'total': total,
            'abertas': abertas,
            'resolvidas': resolvidas,
            'por_status': data_status,
            'por_tipo': data_tipo,
            'por_empresa': data_empresa,
            'evolucao': data_evolucao,
            'allowed_empresas': sorted(allowed_empresas)
        })
    except Exception as e:
        print(f"ERRO em api_dashboard_metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Erro interno no dashboard: {str(e)}'}), 500

@api_bp.route('/dashboard/details', methods=['GET'])
@api_auth_required
def api_dashboard_details():
    try:
        tipo_grafico = request.args.get('type')
        empresas_selecionadas = request.args.getlist('empresas')
        
        # Validar acesso (Igual a metrics)
        usuario = Usuario.query.get(session['usuario_id'])
        allowed_empresas = obter_empresas_para_usuario()
        
        if not allowed_empresas:
            return jsonify({'message': 'Sem acesso'}), 403

        if not empresas_selecionadas or 'todas' in empresas_selecionadas:
            target_empresas = allowed_empresas
        else:
            target_empresas = [emp for emp in empresas_selecionadas if emp in allowed_empresas]
            
        if not target_empresas:
            return jsonify({'message': 'Nenhuma empresa válida selecionada'}), 400

        # 2. Query Base Construction
        base_clauses = [Pendencia.empresa.in_(target_empresas)]
        
        # Filtros de Data (Unificados)
        start_abertura = request.args.get('start_abertura') or request.args.get('start')
        end_abertura = request.args.get('end_abertura') or request.args.get('end')
        if start_abertura and end_abertura:
            base_clauses.append(func.date(Pendencia.data_abertura).between(start_abertura, end_abertura))
            
        start_pendencia = request.args.get('start_pendencia')
        end_pendencia = request.args.get('end_pendencia')
        if start_pendencia and end_pendencia:
            base_clauses.append(Pendencia.data.between(start_pendencia, end_pendencia))

        data_result = []
        columns = []

        if tipo_grafico == 'status':
            columns = ['Empresa', 'Status', 'Quantidade']
            results = db.session.query(Pendencia.empresa, Pendencia.status, func.count(Pendencia.id))\
                .filter(and_(*base_clauses))\
                .group_by(Pendencia.empresa, Pendencia.status)\
                .order_by(Pendencia.empresa, Pendencia.status).all()
            for row in results:
                data_result.append({'Empresa': row[0], 'Status': row[1], 'Quantidade': row[2]})
                
        elif tipo_grafico == 'tipo':
            columns = ['Empresa', 'Tipo de Pendência', 'Quantidade']
            results = db.session.query(Pendencia.empresa, Pendencia.tipo_pendencia, func.count(Pendencia.id))\
                .filter(and_(*base_clauses))\
                .group_by(Pendencia.empresa, Pendencia.tipo_pendencia)\
                .order_by(Pendencia.empresa, func.count(Pendencia.id).desc()).all()
            for row in results:
                data_result.append({'Empresa': row[0], 'Tipo de Pendência': row[1], 'Quantidade': row[2]})
                
        elif tipo_grafico == 'empresas':
            columns = ['Empresa', 'Total Pendências']
            results = db.session.query(Pendencia.empresa, func.count(Pendencia.id))\
                .filter(and_(*base_clauses))\
                .group_by(Pendencia.empresa)\
                .order_by(func.count(Pendencia.id).desc()).all()
            for row in results:
                data_result.append({'Empresa': row[0], 'Total Pendências': row[1]})
                
        elif tipo_grafico == 'evolucao':
            # Para evolução, detalhar por mês e status é mais útil
            columns = ['Mês', 'Status', 'Quantidade']
            six_months_ago = datetime.now().date() - timedelta(days=180)
            
            # Abertas
            abertas_query = db.session.query(
                func.strftime('%Y-%m', Pendencia.data_abertura).label('mes'),
                func.count(Pendencia.id)
            ).filter(and_(*base_clauses))
            
            if not (start_abertura and end_abertura):
                abertas_query = abertas_query.filter(Pendencia.data_abertura >= six_months_ago)
                
            abertas = abertas_query.group_by('mes').all()
             
            # Resolvidas
            resolvidas_query = db.session.query(
                func.strftime('%Y-%m', Pendencia.data_resposta).label('mes'),
                func.count(Pendencia.id)
            ).filter(and_(*base_clauses))\
             .filter(Pendencia.status == 'RESOLVIDA')

            if not (start_abertura and end_abertura):
                resolvidas_query = resolvidas_query.filter(Pendencia.data_resposta >= six_months_ago)

            resolvidas = resolvidas_query.group_by('mes').all()
             
            for row in abertas:
                if row[0]: # Ignorar se mes for None
                    data_result.append({'Mês': row[0], 'Status': 'Aberta (Criada)', 'Quantidade': row[1]})
            for row in resolvidas:
                if row[0]: # Ignorar se mes for None
                    data_result.append({'Mês': row[0], 'Status': 'Resolvida', 'Quantidade': row[1]})
                
            # Ordenar por mês
            data_result.sort(key=lambda x: x.get('Mês', '') or '', reverse=True)

        elif tipo_grafico == 'full_report':
            # Relatório completo para a Central de Relatórios
            columns = ['ID', 'Empresa', 'Data Abertura', 'Tipo', 'Fornecedor/Cliente', 'Valor', 'Status', 'Data Baixa', 'Token', 'SLA']
            
            results = Pendencia.query.filter(and_(*base_clauses)).order_by(Pendencia.data_abertura.desc()).all()
            
            for p in results:
                sla_days = None
                if p.status == 'RESOLVIDA' and p.data_abertura and p.data_resposta:
                    # Cálculo de SLA em dias (Garantir que ambos sejam date para o delta)
                    d_ini = p.data_abertura.date() if hasattr(p.data_abertura, 'date') else p.data_abertura
                    d_fim = p.data_resposta.date() if hasattr(p.data_resposta, 'date') else p.data_resposta
                    
                    try:
                        delta = d_fim - d_ini
                        sla_days = delta.days
                    except:
                        sla_days = 0

                data_result.append({
                    'ID': p.id,
                    'Empresa': p.empresa,
                    'Data Abertura': p.data_abertura.strftime('%d/%m/%Y') if p.data_abertura else '-',
                    'Tipo': p.tipo_pendencia,
                    'Fornecedor/Cliente': p.fornecedor_cliente or '-',
                    'Valor': float(p.valor or 0),
                    'Status': p.status,
                    'Data Baixa': p.data_resposta.strftime('%d/%m/%Y') if p.data_resposta else '-',
                    'Token': p.token_acesso,
                    'SLA': sla_days
                })

        return jsonify({
            'columns': columns,
            'data': data_result,
            'title': f'Detalhes: {tipo_grafico.upper()}'
        })
    except Exception as e:
        print(f"ERRO em api_dashboard_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Erro ao carregar detalhes: {str(e)}'}), 500

    return jsonify({
        'columns': columns,
        'data': data_result,
        'title': f'Detalhes: {tipo_grafico.upper()}'
    })


@api_bp.route('/dashboard/actions')
def api_dashboard_actions():
    """
    Retorna dados para os Cards de Ação:
    1. Última Pendência Aberta (Geral das empresas permitidas)
    2. Painel Rápido (Pendências que exigem ação do usuário)
    """
    try:
        usuario_id = session.get('usuario_id')
        usuario_tipo = session.get('usuario_tipo')
        
        if not usuario_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # 1. Obter empresas permitidas
        target_empresas = obter_empresas_para_usuario()
        if not target_empresas:
            return jsonify({
                'latest': None,
                'quick_panel': []
            })
            
        # 2. Última Pendência Aberta (Geral)
        latest_pendency = Pendencia.query.filter(
            Pendencia.empresa.in_(target_empresas)
        ).order_by(Pendencia.data_abertura.desc()).first()
        
        latest_data = None
        if latest_pendency:
            latest_data = {
                'id': latest_pendency.id,
                'empresa': latest_pendency.empresa,
                'data_abertura': latest_pendency.data_abertura.strftime('%d/%m/%Y %H:%M'),
                'tipo': latest_pendency.tipo_pendencia,
                'valor': latest_pendency.valor,
                'status': latest_pendency.status
            }
            
        # 3. Painel Rápido (Ação Necessária)
        # Define status urgentes baseados no perfil
        status_urgentes = []
        is_supervisor = pode_atuar_como_supervisor()
        
        if is_supervisor:
            # Supervisor vê o que aguarda aprovação dele
            status_urgentes = ['PENDENTE SUPERVISOR UP']
        else:
            # Operador vê o que caiu pra ele ou voltou
            status_urgentes = ['PENDENTE OPERADOR UP', 'DEVOLVIDA AO OPERADOR']
            
        quick_query = Pendencia.query.filter(
            Pendencia.empresa.in_(target_empresas),
            Pendencia.status.in_(status_urgentes)
        ).order_by(Pendencia.data_abertura.asc()) # Mais antigas primeiro (fila)
        
        # Limitar a 5 ou 10 itens para não poluir
        quick_items = quick_query.limit(10).all()
        
        quick_panel_data = []
        for p in quick_items:
            # Calcular dias em aberto
            dias_aberto = 0
            if p.data_abertura:
                dias_aberto = (datetime.now() - p.data_abertura).days
                
            # Determinar URL de ação baseado no perfil do usuário
            if is_supervisor:
                acao_url = url_for('main.supervisor_pendencias', empresa=p.empresa, _external=False)
            else:
                acao_url = url_for('main.operador_pendencias', empresa=p.empresa, _external=False)
            
            quick_panel_data.append({
                'id': p.id,
                'empresa': p.empresa,
                'data': p.data.strftime('%d/%m/%Y') if p.data else '-',
                'status': p.status,
                'prioridade': 'Alta' if dias_aberto > 7 or p.valor > 5000 else 'Normal',
                'acao_url': acao_url
            })

        return jsonify({
            'latest': latest_data,
            'quick_panel': quick_panel_data,
            'user_role': 'Supervisor' if is_supervisor else 'Operador'
        })

    except Exception as e:
        print(f"Erro em /api/dashboard/actions: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard/export', methods=['GET'])
@api_auth_required
def api_dashboard_export():
    try:
        # 1. Filtros (Igual metrics)
        empresas_selecionadas = request.args.getlist('empresas')
        usuario = Usuario.query.get(session['usuario_id'])
        allowed_empresas = obter_empresas_para_usuario()
        
        if not allowed_empresas:
            return jsonify({'message': 'Sem acesso'}), 403

        if not empresas_selecionadas or 'todas' in empresas_selecionadas:
            target_empresas = allowed_empresas
        else:
            target_empresas = [emp for emp in empresas_selecionadas if emp in allowed_empresas]
            
        # 2. Query Full com Filtros
        base_clauses = [Pendencia.empresa.in_(target_empresas)]
        
        start_abertura = request.args.get('start_abertura')
        end_abertura = request.args.get('end_abertura')
        if start_abertura and end_abertura:
            base_clauses.append(func.date(Pendencia.data_abertura).between(start_abertura, end_abertura))
            
        start_pendencia = request.args.get('start_pendencia')
        end_pendencia = request.args.get('end_pendencia')
        if start_pendencia and end_pendencia:
            base_clauses.append(Pendencia.data.between(start_pendencia, end_pendencia))
            
        pendencias = Pendencia.query.filter(and_(*base_clauses)).order_by(Pendencia.data_abertura.desc()).all()
        
        # 3. Gerar DataFrame
        data_list = []
        for p in pendencias:
            data_list.append({
                'ID': p.id,
                'Empresa': p.empresa,
                'Tipo': p.tipo_pendencia,
                'Banco': p.banco or '',
                'Data Pendência': p.data.strftime('%d/%m/%Y') if p.data else '',
                'Data Abertura': p.data_abertura.strftime('%d/%m/%Y %H:%M') if p.data_abertura else '',
                'Fornecedor/Cliente': p.fornecedor_cliente,
                'Valor': float(p.valor or 0),
                'Status': p.status,
                'Observação': p.observacao,
                'Natureza Operação': p.natureza_operacao or '',
                'Data Resposta': p.data_resposta.strftime('%d/%m/%Y %H:%M') if p.data_resposta else '',
                'Modificado Por': p.modificado_por or '',
                'Data Baixa (Doc)': p.data_baixa.strftime('%d/%m/%Y') if p.data_baixa else '',
                'Data Competência': p.data_competencia.strftime('%d/%m/%Y') if p.data_competencia else '',
                'Código Lançamento': p.codigo_lancamento or '',
                'Tipo Lançamento': p.tipo_credito_debito or ''
            })
            
        df = pd.DataFrame(data_list)
        
        # 4. Exportar para Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Pendencias')
            
        output.seek(0)
        
        filename = f"pendencias_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"ERRO em api_dashboard_export: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Erro ao exportar indicadores: {str(e)}'}), 500
