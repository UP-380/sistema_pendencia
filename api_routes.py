"""
Rotas de API REST para o frontend React
Todas as rotas retornam JSON ao invés de renderizar templates

IMPORTANTE: Este arquivo deve ser importado no final do app.py, após todos os modelos estarem definidos
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

# Criar blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Helper para verificar autenticação
def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('usuario_id'):
            return jsonify({'error': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper para verificar permissão
def api_permissao_requerida(*tipos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('usuario_id'):
                return jsonify({'error': 'Não autenticado'}), 401
            if session.get('usuario_tipo') not in tipos:
                return jsonify({'error': 'Acesso negado'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# ROTAS DE AUTENTICAÇÃO
# ============================================================================

# Nota: A rota /auth/login é implementada diretamente no app.py
# para ter acesso aos modelos Usuario e check_password_hash

@api.route('/auth/logout', methods=['POST'])
@api_auth_required
def api_logout():
    """API de logout"""
    session.clear()
    return jsonify({'success': True})

@api.route('/auth/check', methods=['GET'])
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

# ============================================================================
# ROTAS DE EMPRESAS
# ============================================================================

# Nota: A rota /empresas e outras rotas são implementadas diretamente no app.py
# após importar este blueprint, para ter acesso aos modelos
