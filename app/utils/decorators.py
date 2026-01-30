from functools import wraps
from flask import session, redirect, url_for, flash, request

def permissao_requerida(*tipos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"DEBUG: Verificando permissao para rota {f.__name__}. Session keys: {list(session.keys())}")
            print(f"DEBUG: Cookies recebidos: {request.cookies}")
            if 'usuario_id' not in session:
                print("DEBUG: usuario_id nao encontrado na sessao. Redirecionando para login.")
                return redirect(url_for('auth.login'))
            if session.get('usuario_tipo') not in tipos:
                print(f"DEBUG: Tipo de usuario {session.get('usuario_tipo')} nao permitido. Esperado: {tipos}")
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
