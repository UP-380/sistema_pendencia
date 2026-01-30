from functools import wraps
from flask import session, redirect, url_for, flash

def permissao_requerida(*tipos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('auth.login'))
            if session.get('usuario_tipo') not in tipos:
                flash('Você não tem permissão para acessar esta página.', 'danger')
                # Redirecionar para dashboard ao invés de listar_segmentos
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('usuario_id'):
            return {'error': 'Não autenticado'}, 401
        return f(*args, **kwargs)
    return decorated_function

def api_permissao_requerida(*tipos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('usuario_id'):
                return {'error': 'Não autenticado'}, 401
            if session.get('usuario_tipo') not in tipos:
                return {'error': 'Acesso negado'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
