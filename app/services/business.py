from flask import session
import requests
import os
from app.extensions import db
from app.models import Usuario, Empresa, LogAlteracao, Segmento, usuario_empresas
from app.utils.helpers import now_brazil

EMPRESAS_CACHE = [] # Fallback or keep logical ref if needed, but preferable to query DB

def obter_empresas_para_usuario():
    """
    Retorna a lista de empresas baseada no tipo de usuário e permissões.
    Para adm: todas as empresas
    Para supervisor/operador/cliente: apenas empresas permitidas vinculadas no cadastro
    """
    tipo_usuario = session.get('usuario_tipo')
    
    if tipo_usuario == 'adm':
        # Apenas Admin vê todas as empresas globalmente
        return [empresa.nome for empresa in Empresa.query.order_by(Empresa.nome).all()]
    else:
        # Supervisor, Operador e cliente veem apenas suas empresas vinculadas
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return []
            
        usuario = Usuario.query.get(usuario_id)
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

def usuario_tem_acesso(email_usuario, empresa_id):
    """
    Verifica se um usuário tem acesso a uma empresa específica.
    Admin tem acesso a todas as empresas.
    Supervisor, Operador e cliente têm acesso apenas às empresas vinculadas.
    """
    if not email_usuario:
        return False
    
    usuario = Usuario.query.filter_by(email=email_usuario).first()
    if not usuario:
        return False
    
    # Admin tem acesso a todas as empresas globalmente
    if usuario.tipo == 'adm':
        return True
    
    # Supervisor, Operador e cliente precisam ter a empresa vinculada
    if usuario.tipo in ['supervisor', 'operador', 'cliente']:
        empresa = Empresa.query.get(empresa_id)
        if empresa and empresa in usuario.empresas:
            return True
    
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
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao enviar notificação Teams: {e}")

def integrar_nova_empresa(empresa):
    """
    Função automatizada para integrar uma nova empresa em todo o sistema.
    Esta função garante que a nova empresa seja automaticamente disponível
    em todos os filtros, painéis e funcionalidades do sistema.
    """
    try:
        # Lógica original atualizava lista global EMPRESAS, mas agora usamos DB.
        # Mantemos log e notificação.
        
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
