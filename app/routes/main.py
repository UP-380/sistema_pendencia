from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, Response, make_response, send_from_directory, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
import json
import os
import json
import uuid
import pandas as pd
import io
import openpyxl
import csv

from app.extensions import db, mail
from app.models import Usuario, Empresa, Segmento, Pendencia, LogAlteracao, Importacao, usuario_empresas, PermissaoUsuarioTipo, PermissaoUsuarioPersonalizada
from app.services.rules import TIPO_RULES, TIPO_IMPORT_MAP, validar_por_tipo, obter_colunas_por_tipo, obter_colunas_importacao_por_tipo, obter_todas_colunas, validar_row_por_tipo, label_tipo_planilha
from app.services.business import obter_empresas_para_usuario, pode_atuar_como_operador, pode_atuar_como_supervisor, usuario_tem_acesso, integrar_nova_empresa
from app.services.email_service import enviar_email_cliente, enviar_email_resposta_recusada
from app.services.notifications import (
    notificar_teams_pendente_operador,
    notificar_teams_pendente_supervisor,
    notificar_teams_recusa_cliente,
    notificar_teams_recusa_supervisor
)
from app.utils.helpers import parse_currency_to_float, parse_date_or_none, now_brazil, pick
from app.utils.decorators import permissao_requerida

TIPOS_PENDENCIA = list(TIPO_RULES.keys())

main_bp = Blueprint('main', __name__)

# Iframe clickup configuration should be moved to context processor or config, defining here for compatibility used in routes/templates
iframe_clickup = """
<iframe class="clickup-embed clickup-dynamic-height"
        src="https://forms.clickup.com/9007138778/f/8cdw1yu-193593/AZ6310ZHFCSW9ANQGA"
        width="100%" height="100%"
        style="background: transparent; border: 1px solid #ccc;"></iframe>
<script async src="https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"></script>
"""

@main_bp.context_processor
def inject_globals():
    return {
        'iframe_clickup': iframe_clickup,
        'today_str': now_brazil().strftime('%Y-%m-%d'),
        'current_month': now_brazil().strftime('%Y-%m'),
        'now_brazil': now_brazil,
        'pode_atuar_como_operador': pode_atuar_como_operador,
        'pode_atuar_como_supervisor': pode_atuar_como_supervisor,
        # Re-export filters if used as functions in templates (though filters are better)
    }

# Rotas de Segmentos



@main_bp.route('/segmentos')
@main_bp.route('/')
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

@main_bp.route('/segmento/<int:id>')
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

@main_bp.route('/empresa/<int:id>')
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
        return redirect(url_for('main.acesso_negado'))
    
    return redirect(url_for('main.dashboard', empresa=empresa.nome))

# ============================================================================
# FIM DAS ROTAS DE SEGMENTOS
# ============================================================================

@main_bp.route('/empresas')
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def pre_dashboard():
    from datetime import datetime, timedelta
    
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
            pass  # Ignorar valores inválidos
    
    # ===== APLICAR FILTRO DE CLIENTE (Nome da Empresa) =====
    if clientes_selecionados:
        # Filtrar diretamente por nome das empresas cadastradas
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
        pendencias_resolvidas = [p for p in pendencias if p.status == 'RESOLVIDA']
        
        empresas_info.append({
            'id': empresa.id,
            'nome': empresa.nome,
            'abertas': len(pendencias_abertas),
            'resolvidas': len(pendencias_resolvidas)
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
    
    # ===== PREPARAR DADOS PARA FILTROS =====
    segmentos = Segmento.query.order_by(Segmento.nome).all()
    
    # Buscar empresas cadastradas (respeitando permissões do usuário)
    if session.get('usuario_tipo') == 'adm':
        empresas_disponiveis = Empresa.query.order_by(Empresa.nome).all()
    else:
        usuario = Usuario.query.get(session['usuario_id'])
        empresas_disponiveis = usuario.empresas if usuario else []
    clientes_disponiveis = [empresa.nome for empresa in empresas_disponiveis]
    
    operadores_disponiveis = Usuario.query.filter(
        Usuario.tipo.in_(['adm', 'supervisor', 'operador'])
    ).order_by(Usuario.email).all()
    
    supervisores_disponiveis = Usuario.query.filter_by(tipo='supervisor').order_by(Usuario.email).all()
    
    return render_template(
        'pre_dashboard.html',
        empresas_info=empresas_info,
        tipo_counts=tipo_counts,
        tipos_labels=tipos_labels,
        tipos_valores=tipos_valores,
        abertas_count=abertas_count,
        resolvidas_count=resolvidas_count,
        data_abertura_inicio=data_abertura_inicio,
        data_abertura_fim=data_abertura_fim,
        data_resolucao_inicio=data_resolucao_inicio,
        data_resolucao_fim=data_resolucao_fim,
        today_str=today_str,
        current_month=current_month,
        # Novos parâmetros para filtros
        segmentos=segmentos,
        segmentos_selecionados=[int(s) for s in segmentos_selecionados] if segmentos_selecionados else [],
        clientes_disponiveis=clientes_disponiveis,
        clientes_selecionados=clientes_selecionados,
        operadores_disponiveis=operadores_disponiveis,
        operadores_selecionados=[int(o) for o in operadores_selecionados] if operadores_selecionados else [],
        supervisores_disponiveis=supervisores_disponiveis,
        supervisores_selecionados=[int(s) for s in supervisores_selecionados] if supervisores_selecionados else []
    )

@main_bp.route('/api/dados_graficos')
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

@main_bp.route('/dashboard-gerencial', methods=['GET'])
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor', 'operador')
def dashboard_gerencial():
    return render_template('dashboard_gerencial.html')

@main_bp.route('/dashboard', methods=['GET'])
@permissao_requerida('supervisor', 'adm', 'operador', 'cliente', 'cliente_supervisor')
def dashboard():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.pre_dashboard'))
    
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
    
    # Buscar respostas anteriores e primeira resposta do cliente
    respostas_anteriores = {}
    primeiras_respostas = {}
    for pendencia in pendencias:
        if pendencia.resposta_cliente:
            # Busca a primeira resposta do cliente nos logs (ordem crescente)
            primeira_resposta = (
                LogAlteracao.query
                .filter_by(pendencia_id=pendencia.id, campo_alterado="resposta_cliente")
                .order_by(LogAlteracao.data_hora.asc())
                .first()
            )
            if primeira_resposta:
                primeiras_respostas[pendencia.id] = primeira_resposta
            
            # Para clientes com status PENDENTE COMPLEMENTO CLIENTE, busca a última resposta
            if session.get('usuario_tipo') == 'cliente' and pendencia.status == 'PENDENTE COMPLEMENTO CLIENTE':
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
        primeiras_respostas=primeiras_respostas,
        segmento_nome=segmento_nome,
        segmento_id=segmento_id
    )

@main_bp.route('/nova', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
def nova_pendencia():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.pre_dashboard'))
    
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
            
            # Auto-preencher fornecedor para pendências não identificadas
            fornecedor = request.form.get('fornecedor_cliente', '').strip()
            tipos_sem_fornecedor = [
                "Cartão de Crédito Não Identificado",
                "Pagamento Não Identificado", 
                "Recebimento Não Identificado"
            ]
            
            if not fornecedor and tipo_pendencia in tipos_sem_fornecedor:
                fornecedor = "A IDENTIFICAR"

            # Preparar payload para validação
            payload = {
                'tipo_pendencia': tipo_pendencia,
                'empresa': empresa,
                'banco': banco,
                'fornecedor_cliente': fornecedor,
                'valor': request.form.get('valor', ''),
                'codigo_lancamento': request.form.get('codigo_lancamento', ''),
                'data': request.form.get('data', ''),
                'data_competencia': request.form.get('data_competencia', ''),
                'data_baixa': request.form.get('data_baixa', ''),
                'observacao': request.form.get('observacao', ''),
                'natureza_sistema': request.form.get('natureza_sistema', ''),
                'tipo_credito_debito': request.form.get('tipo_credito_debito', '')
            }
            
            # Validar por tipo
            is_valid, error_msg = validar_por_tipo(payload)
            if not is_valid:
                flash(f'Erro de validação: {error_msg}', 'danger')
                return redirect(url_for('main.nova_pendencia'))
            
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
                    # Corrigido: usando current_app.static_folder e uuid para nome único
                    original_filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                    target_path = os.path.join(current_app.static_folder, 'notas_fiscais', unique_filename)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    file.save(target_path)
                    nota_fiscal_arquivo = unique_filename
            
            # Validar se o usuário tem acesso à empresa selecionada
            if empresa not in empresas_usuario:
                flash('Você não tem acesso a esta empresa.', 'danger')
                return redirect(url_for('main.nova_pendencia'))
            
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
                return redirect(url_for('main.supervisor_pendencias', empresa=empresa))
            else:
                return redirect(url_for('main.operador_pendencias', empresa=empresa))
        except Exception as e:
            flash(f'Erro ao criar pendência: {str(e)}', 'error')
            return redirect(url_for('main.nova_pendencia'))
    
    return render_template('nova_pendencia.html', 
                         empresas=empresas_usuario, 
                         tipos_pendencia=TIPOS_PENDENCIA,
                         preselect_empresa=preselect_empresa)

@main_bp.route('/pendencia/<token>', methods=['GET', 'POST'])
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
                # Corrigido: definindo filename e garantindo nome único
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                target_path = os.path.join(current_app.static_folder, 'notas_fiscais', unique_filename)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                file.save(target_path)
                pendencia.nota_fiscal_arquivo = unique_filename
        
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
        return redirect(url_for('main.dashboard', empresa=empresa, tipo_pendencia=tipo_pendencia, busca=busca))
    
    return render_template('ver_pendencia.html', 
                         pendencia=pendencia,
                         motivo_recusa=pendencia.motivo_recusa,
                         ultima_resposta=ultima_resposta,
                         historico_respostas=historico_respostas)

@main_bp.route('/resolver/<int:id>')
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
    return redirect(url_for('main.dashboard'))

@main_bp.route('/baixar_modelo')
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

@main_bp.route("/import/modelo", methods=["GET"])
@permissao_requerida('supervisor', 'adm', 'operador')
def download_modelo_pendencias():
    """
    Gera e serve uma planilha modelo específica para cada tipo de pendência
    """
    import openpyxl
    from io import BytesIO
    
    # Obter tipo da pendência
    tipo = request.args.get('tipo', '').upper()
    
    # Mapeamento: tipo → nome legível
    mapeamento_nomes = {
        'NATUREZA_ERRADA': 'Natureza Errada',
        'COMPETENCIA_ERRADA': 'Competência Errada',
        'DATA_BAIXA_ERRADA': 'Data da Baixa Errada',
        'CARTAO_NAO_IDENTIFICADO': 'Cartão de Crédito Não Identificado',
        'PAGAMENTO_NAO_IDENTIFICADO': 'Pagamento Não Identificado',
        'RECEBIMENTO_NAO_IDENTIFICADO': 'Recebimento Não Identificado',
        'DOCUMENTO_NAO_ANEXADO': 'Documento Não Anexado',
        'LANCAMENTO_NAO_ENCONTRADO_EXTRATO': 'Lançamento Não Encontrado em Extrato',
        'LANCAMENTO_NAO_ENCONTRADO_SISTEMA': 'Lançamento Não Encontrado em Sistema'
    }
    
    tipo_nome = mapeamento_nomes.get(tipo)
    
    if not tipo_nome:
        flash(f'Tipo de modelo inválido: {tipo}', 'error')
        return redirect(url_for('main.importar_planilha'))
    
    # Buscar colunas necessárias para importação deste tipo
    colunas = obter_colunas_importacao_por_tipo(tipo_nome)
    
    if not colunas:
        flash(f'Não foi possível determinar as colunas para o tipo: {tipo_nome}', 'error')
        return redirect(url_for('main.importar_planilha'))
    
    # Criar planilha Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Modelo'
    
    # Adicionar cabeçalhos
    ws.append(colunas)
    
    # Adicionar linha de exemplo
    exemplo = []
    for col in colunas:
        if 'data' in col.lower():
            exemplo.append('2025-01-28')
        elif 'valor' in col.lower():
            exemplo.append('1500.50')
        elif 'empresa' in col.lower():
            exemplo.append('NOME DA EMPRESA')
        elif 'banco' in col.lower():
            exemplo.append('SICREDI')
        elif 'fornecedor' in col.lower() or 'cliente' in col.lower():
            exemplo.append('FORNECEDOR EXEMPLO LTDA')
        elif 'codigo' in col.lower():
            exemplo.append('12345')
        elif 'natureza' in col.lower():
            exemplo.append('RECEITA DE VENDAS')
        elif 'email' in col.lower():
            exemplo.append('cliente@exemplo.com')
        else:
            exemplo.append('EXEMPLO')
    
    ws.append(exemplo)
    
    # Salvar em BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    nome_arquivo = f"modelo_{tipo.lower()}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@main_bp.route('/importar', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm', 'operador')
def importar_planilha():
    empresas_nomes = obter_empresas_para_usuario()
    if not empresas_nomes:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Buscar objetos Empresa completos
    empresas = Empresa.query.filter(Empresa.nome.in_(empresas_nomes)).all()
    
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
        if request.form.get('confirmar_importacao') == '1' and 'preview_filepath' in session:
            # Segunda etapa: confirmar importação usando dados em disco
            try:
                temp_path = session['preview_filepath']
                if not os.path.exists(temp_path):
                    flash('Sessão de importação expirou ou arquivo não encontrado.', 'error')
                    return redirect(url_for('main.importar_planilha'))
                
                df = pd.read_excel(temp_path, dtype=str).fillna("")
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
                        tipo_credito_debito=r.get("tipo_credito_debito") or "",
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
                
                session.pop('preview_filepath', None)
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass

                session.pop('preview_filename', None)
                session.pop('tipo_import', None)
                session.pop('empresa_id_contexto', None)
                
                flash('Pendências importadas com sucesso!', 'success')
                return redirect(url_for('main.dashboard_gerencial'))
            except Exception as e:
                erros.append(f'Erro ao importar: {e}')
        else:
            file = request.files.get('arquivo')
            tipo_import = request.form.get('tipo_import')
            empresa_id_ctx = request.form.get('empresa_id', type=int)
            
            if not file or not tipo_import:
                flash('Arquivo e tipo são obrigatórios.', 'error')
                return render_template('importar_planilha.html', empresas=empresas, preview=preview, erros=erros, empresa_id_contexto=empresa_id_contexto)
            
            try:
                # Salvar arquivo temporário
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                temp_dir = os.path.join(current_app.instance_path, 'temp_imports')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, unique_name)
                file.save(temp_path)
                
                # Ler xlsx do disco
                df = pd.read_excel(temp_path, dtype=str).fillna("")
                errors = []
                
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
                
                # Preview se houver erros
                if errors:
                    preview = df.head(5).to_dict(orient='records')
                    erros = [f"Linha {e['linha']}: {e['erro']}" for e in errors]
                else:
                    # Salvar caminho do arquivo em sessão para confirmação
                    session['preview_filepath'] = temp_path
                    session['preview_filename'] = file.filename
                    session['tipo_import'] = tipo_import
                    session['empresa_id_contexto'] = empresa_id_ctx
                    preview = df.head(5).to_dict(orient='records')
                    
            except Exception as e:
                erros.append(f'Erro ao processar arquivo: {e}')
    
    return render_template('importar_planilha.html', 
                         empresas=empresas, 
                         preview=preview, 
                         erros=erros, 
                         empresa_id_contexto=empresa_id_contexto,
                         tipos_importacao=TIPO_IMPORT_MAP.keys())

@main_bp.route('/historico_importacoes')
@permissao_requerida('supervisor', 'adm', 'operador')
def historico_importacoes():
    historico = Importacao.query.order_by(Importacao.data_hora.desc()).limit(20).all()
    return render_template('historico_importacoes.html', historico=historico)

@main_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('supervisor', 'adm')
def editar_pendencia(id):
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.pre_dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    if pendencia.resposta_cliente:
        flash('Não é possível editar uma pendência já respondida pelo cliente.', 'danger')
        return redirect(url_for('main.dashboard'))
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
                # Corrigido: usando current_app.static_folder e uuid para nome único
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                target_path = os.path.join(current_app.static_folder, 'notas_fiscais', unique_filename)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                file.save(target_path)
                pendencia.nota_fiscal_arquivo = unique_filename
        pendencia.modificado_por = 'ADIMIN UP380'
        db.session.commit()
        flash('Pendência editada com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))
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


@main_bp.route('/operador/pendencias')
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_pendencias():
    """Dashboard do operador - mostra pendências PENDENTE OPERADOR UP"""
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.pre_dashboard'))
    
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

@main_bp.route('/operador/natureza_operacao/<int:id>', methods=['GET', 'POST'])
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_natureza_operacao(id):
    """Operador informa a Natureza de Operação"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status not in ['PENDENTE OPERADOR UP', 'DEVOLVIDA AO OPERADOR']:
        flash('Esta pendência não está disponível para operador.', 'warning')
        return redirect(url_for('main.operador_pendencias'))
    
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
        return redirect(url_for('main.operador_pendencias'))
    
    return render_template('operador_natureza_operacao.html', pendencia=pendencia)

@main_bp.route('/operador/recusar_resposta/<int:id>', methods=['POST'])
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_recusar_resposta(id):
    """Operador recusa a resposta do cliente e solicita complemento"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está disponível para recusa.', 'warning')
        return redirect(url_for('main.operador_pendencias'))
    
    motivo_recusa = request.form.get('motivo_recusa', '').strip()
    if not motivo_recusa:
        flash('Motivo da recusa é obrigatório.', 'danger')
        return redirect(url_for('main.operador_pendencias'))
    
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
    return redirect(url_for('main.operador_pendencias'))

@main_bp.route('/operador/lote_enviar_supervisor', methods=['POST'])
@permissao_requerida('operador', 'adm', 'supervisor')
def operador_lote_enviar_supervisor():
    ids = request.form.getlist('ids')
    if not ids:
        flash('Nenhuma pendência selecionada.', 'warning')
        return redirect(url_for('main.operador_pendencias'))
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
    return redirect(url_for('main.operador_pendencias'))

@main_bp.route('/supervisor/pendencias')
@permissao_requerida('supervisor', 'adm')
def supervisor_pendencias():
    """Dashboard do supervisor - mostra pendências PENDENTE SUPERVISOR UP"""
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.pre_dashboard'))
    
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
    
    # Calcular total de pendências aguardando supervisor (todas as empresas)
    total_pendencias_supervisor = Pendencia.query.filter(
        Pendencia.empresa.in_(empresas_permitidas),
        Pendencia.status.in_(status_abertos_supervisor)
    ).count()
    
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
        pendencias_abertas_por_empresa=pendencias_abertas_por_empresa,  # Nova variável para o indicador
        total_pendencias_supervisor=total_pendencias_supervisor  # Total geral de pendências
    )

@main_bp.route('/supervisor/resolver_pendencia/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def supervisor_resolver_pendencia(id):
    """Supervisor resolve a pendência"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE SUPERVISOR UP':
        flash('Esta pendência não está disponível para resolução.', 'warning')
        return redirect(url_for('main.supervisor_pendencias'))
    
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
    return redirect(url_for('main.supervisor_pendencias'))

@main_bp.route('/supervisor/lote_resolver_pendencias', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def supervisor_lote_resolver_pendencias():
    """Supervisor resolve múltiplas pendências em lote"""
    ids = request.form.getlist('ids')
    if not ids:
        flash('Nenhuma pendência selecionada.', 'warning')
        return redirect(url_for('main.supervisor_pendencias'))
    
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
    return redirect(url_for('main.supervisor_pendencias'))

@main_bp.route('/supervisor/recusar_devolver_operador/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def supervisor_recusar_devolver_operador(id):
    """Supervisor recusa a pendência e devolve ao operador para correção"""
    pendencia = Pendencia.query.get_or_404(id)
    
    if pendencia.status != 'PENDENTE SUPERVISOR UP':
        flash('Esta pendência não está disponível para recusa.', 'warning')
        return redirect(url_for('main.supervisor_pendencias'))
    
    motivo_recusa = request.form.get('motivo_recusa_supervisor', '').strip()
    if not motivo_recusa:
        flash('Motivo da recusa é obrigatório.', 'danger')
        return redirect(url_for('main.supervisor_pendencias'))
    
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
    return redirect(url_for('main.supervisor_pendencias'))

@main_bp.route('/editar_observacao/<int:id>', methods=['GET', 'POST'])
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
                # Corrigido: usando current_app.static_folder e uuid para nome único
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                target_path = os.path.join(current_app.static_folder, 'notas_fiscais', unique_filename)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                file.save(target_path)
                pendencia.nota_fiscal_arquivo = unique_filename
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
        return redirect(url_for('main.dashboard'))
    return render_template('editar_observacao.html', pendencia=pendencia)

@main_bp.route('/resolvidas', methods=['GET'])
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def dashboard_resolvidas():
    empresas_usuario = obter_empresas_para_usuario()
    if not empresas_usuario:
        flash('Você não tem acesso a nenhuma empresa.', 'warning')
        return redirect(url_for('main.pre_dashboard'))
    
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

@main_bp.route('/pendencias')
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
        return redirect(url_for('main.pre_dashboard'))

    query = Pendencia.query

    # Filtro por empresa
    if empresa:
        if empresa not in empresas_usuario:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('main.pre_dashboard'))
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

@main_bp.route('/logs/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def ver_logs_pendencia(pendencia_id):
    logs = LogAlteracao.query.filter_by(pendencia_id=pendencia_id).order_by(LogAlteracao.data_hora.desc()).all()
    pendencia = Pendencia.query.get_or_404(pendencia_id)
    return render_template('logs_pendencia.html', logs=logs, pendencia=pendencia)

@main_bp.route('/exportar_logs/<int:pendencia_id>')
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

@main_bp.route('/logs_recentes')
@permissao_requerida('supervisor', 'adm', 'cliente_supervisor')
def logs_recentes():
    logs = LogAlteracao.query.order_by(LogAlteracao.data_hora.desc()).limit(50).all()
    return render_template('logs_recentes.html', logs=logs)

@main_bp.route('/exportar_logs_csv')
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

@main_bp.route('/exportar_pendencias_csv')
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
        return redirect(url_for('main.pre_dashboard'))

    query = Pendencia.query

    # Filtro por empresa
    if empresa:
        if empresa not in empresas_usuario:
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('main.pre_dashboard'))
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

@main_bp.route('/pendencia/<int:id>/informar_natureza', methods=['POST'])
@permissao_requerida('operador', 'supervisor')
def informar_natureza_operacao(id):
    """
    Permite que operador ou supervisor informe a natureza da operação
    """
    if not pode_atuar_como_operador():
        flash('Você não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    
    # Verificar se o status atual permite a ação
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está no status correto para esta ação.', 'warning')
        return redirect(url_for('main.ver_pendencia', token=pendencia.token_acesso))
    
    # Verificar permissão de empresa
    empresas_usuario = obter_empresas_para_usuario()
    if pendencia.empresa not in empresas_usuario:
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    natureza_operacao = request.form.get('natureza_operacao')
    if not natureza_operacao:
        flash('Natureza da operação é obrigatória.', 'danger')
        return redirect(url_for('main.ver_pendencia', token=pendencia.token_acesso))
    
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
    return redirect(url_for('main.ver_pendencia', token=pendencia.token_acesso))

@main_bp.route('/pendencia/<int:id>/aceitar_resposta', methods=['POST'])
@permissao_requerida('operador', 'supervisor')
def aceitar_resposta_cliente(id):
    """
    Permite que operador ou supervisor aceite a resposta do cliente
    """
    if not pode_atuar_como_operador():
        flash('Você não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    
    # Verificar se o status atual permite a ação
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está no status correto para esta ação.', 'warning')
        return redirect(url_for('main.ver_pendencia', token=pendencia.token_acesso))
    
    # Verificar permissão de empresa
    empresas_usuario = obter_empresas_para_usuario()
    if pendencia.empresa not in empresas_usuario:
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('main.dashboard'))
    
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

@main_bp.route('/pendencia/<int:id>/recusar_resposta', methods=['POST'])
@permissao_requerida('operador', 'supervisor')
def recusar_resposta_cliente(id):
    """
    Permite que operador ou supervisor recuse a resposta do cliente
    """
    if not pode_atuar_como_operador():
        flash('Você não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    pendencia = Pendencia.query.get_or_404(id)
    
    # Verificar se o status atual permite a ação
    if pendencia.status != 'PENDENTE OPERADOR UP':
        flash('Esta pendência não está no status correto para esta ação.', 'warning')
        return redirect(url_for('ver_pendencia', token=pendencia.token_acesso))
    
    # Verificar permissão de empresa
    empresas_usuario = obter_empresas_para_usuario()
    if pendencia.empresa not in empresas_usuario:
        flash('Você não tem acesso a esta empresa.', 'danger')
        return redirect(url_for('main.dashboard'))
    
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

@main_bp.route('/aprovar_pendencia/<int:id>', methods=['POST'])
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

@main_bp.route("/relatorios/mensal", methods=["GET"])
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
        return redirect(url_for('main.dashboard'))

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
            return redirect(url_for('main.dashboard'))
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
        return redirect(url_for('main.dashboard'))

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

@main_bp.route('/relatorio_operadores')
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

@main_bp.route('/')
def index():
    """Rota raiz - redireciona baseado no tipo de usuário"""
    if not session.get('usuario_email'):
        return redirect(url_for('login'))
    
    # Redirecionar direto para empresas
    return redirect(url_for('pre_dashboard'))

# ROTA DESATIVADA - SEGMENTOS REMOVIDOS
# @main_bp.route('/segmentos')
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
# @main_bp.route('/segmento/<int:segmento_id>')
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
# @main_bp.route('/empresa/<int:empresa_id>')
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

@main_bp.route('/gerenciar_usuarios')
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

@main_bp.route('/novo_usuario', methods=['GET', 'POST'])
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
            return redirect(url_for('main.novo_usuario'))
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
        return redirect(url_for('main.gerenciar_usuarios'))
    # Permissões padrão do tipo
    permissoes_tipo = {func: checar_permissao('operador', func) for cat, funclist in FUNCIONALIDADES_CATEGORIZADAS for func, _ in funclist}
    return render_template('admin/novo_usuario.html', empresas=empresas, funcionalidades_categorizadas=FUNCIONALIDADES_CATEGORIZADAS, permissoes_tipo=permissoes_tipo)

@main_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('main.gerenciar_usuarios'))
    empresas_permitidas = [e.id for e in usuario.empresas]
    # Permissões atuais (personalizadas ou herdadas)
    permissoes_usuario = {}
    for categoria, funcionalidades in FUNCIONALIDADES_CATEGORIZADAS:
        for func, _ in funcionalidades:
            permissoes_usuario[func] = checar_permissao_usuario(usuario.id, usuario.tipo, func)
    return render_template('admin/editar_usuario.html', usuario=usuario, empresas=empresas, empresas_permitidas=empresas_permitidas, funcionalidades_categorizadas=FUNCIONALIDADES_CATEGORIZADAS, permissoes_usuario=permissoes_usuario)

@main_bp.route('/gerenciar_empresas')
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

@main_bp.route('/nova_empresa', methods=['GET', 'POST'])
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

@main_bp.route('/editar_empresa/<int:id>', methods=['GET', 'POST'])
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

@main_bp.route('/deletar_usuario/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def deletar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário removido com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios'))

@main_bp.route('/deletar_empresa/<int:id>', methods=['POST'])
@permissao_requerida('supervisor', 'adm')
def deletar_empresa(id):
    """Deleta uma empresa após validações - verifica apenas se não há pendências"""
    print(f"\n{'='*50}")
    print(f"TENTATIVA DE EXCLUSÃO - Empresa ID: {id}")
    print(f"{'='*50}")
    
    empresa = Empresa.query.get_or_404(id)
    print(f"Empresa encontrada: {empresa.nome}")
    
    # Verificar APENAS se há pendências associadas
    total_pendencias = Pendencia.query.filter_by(empresa=empresa.nome).count()
    print(f"Total de pendências: {total_pendencias}")
    
    if total_pendencias > 0:
        print(f"BLOQUEADO: Empresa tem {total_pendencias} pendências")
        flash(f'Não é possível excluir a empresa "{empresa.nome}" pois ela possui {total_pendencias} pendência(s) associada(s). Exclua as pendências primeiro.', 'danger')
        return redirect(url_for('gerenciar_empresas'))
    
    # Usuários vinculados não impedem a exclusão
    # Remove manualmente os vínculos antes de deletar
    total_usuarios = len(empresa.usuarios) if empresa.usuarios else 0
    if total_usuarios > 0:
        print(f"INFO: Empresa tem {total_usuarios} usuários vinculados - removendo vínculos...")
        # Remove todos os vínculos com usuários
        empresa.usuarios.clear()
        db.session.commit()
        print(f"✅ Vínculos com {total_usuarios} usuário(s) removidos")
    
    # Pode deletar se não houver pendências
    nome_empresa = empresa.nome
    print(f"VALIDAÇÕES OK! Deletando empresa...")
    
    try:
        db.session.delete(empresa)
        db.session.commit()
        print(f"✅ Empresa '{nome_empresa}' excluída com sucesso!")
        if total_usuarios > 0:
            flash(f'Empresa "{nome_empresa}" removida com sucesso! Os vínculos com {total_usuarios} usuário(s) foram removidos.', 'success')
        else:
            flash(f'Empresa "{nome_empresa}" removida com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO ao excluir: {str(e)}")
        flash(f'Erro ao excluir empresa: {str(e)}', 'danger')
    
    return redirect(url_for('gerenciar_empresas'))

# ============================================================================
# ROTAS ADMINISTRATIVAS DE SEGMENTOS
# ============================================================================

@main_bp.route('/gerenciar_segmentos')
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

@main_bp.route('/novo_segmento', methods=['GET', 'POST'])
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

@main_bp.route('/editar_segmento/<int:id>', methods=['GET', 'POST'])
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

@main_bp.route('/deletar_segmento/<int:id>', methods=['POST'])
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

@main_bp.route('/deletar_pendencia/<int:id>', methods=['POST'])
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
    return redirect(url_for('main.dashboard', empresa=empresa, tipo_pendencia=tipo_pendencia, busca=busca))

@main_bp.route('/acesso_negado')
def acesso_negado():
    return render_template('acesso_negado.html'), 403

@main_bp.route('/log_suporte', methods=['POST'])
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

@main_bp.route('/baixar_anexo/<int:pendencia_id>')
@permissao_requerida('supervisor', 'adm', 'operador')
def baixar_anexo(pendencia_id):
    pendencia = Pendencia.query.get_or_404(pendencia_id)
    if not pendencia.nota_fiscal_arquivo:
        flash('Nenhum anexo encontrado para esta pendência.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Corrigido: usando send_from_directory que é mais robusto e seguro
    directory = os.path.join(current_app.static_folder, 'notas_fiscais')
    
    if not os.path.exists(os.path.join(directory, pendencia.nota_fiscal_arquivo)):
        flash('Arquivo não encontrado no servidor.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from flask import send_from_directory
    return send_from_directory(directory, pendencia.nota_fiscal_arquivo, as_attachment=True)

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

@main_bp.route('/gerenciar_permissoes', methods=['GET', 'POST'])
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

