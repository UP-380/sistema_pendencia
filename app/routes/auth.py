from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.models.usuario import Usuario

from app.extensions import csrf

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        print(f"DEBUG: Tentativa de login para {email}")
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            print(f"DEBUG: Usuário encontrado: {usuario.email}, Tipo: {usuario.tipo}")
            # Tenta ambos os campos (senha_hash e senha) para compatibilidade
            senha_valida = False
            if hasattr(usuario, 'senha_hash') and usuario.senha_hash:
                senha_valida = check_password_hash(usuario.senha_hash, senha)
                print(f"DEBUG: check_password_hash senha_hash: {senha_valida}")
            
            if not senha_valida and hasattr(usuario, 'senha') and usuario.senha:
                # Fallback para senha antiga se existir (apenas segurança)
                senha_valida = check_password_hash(usuario.senha, senha)
                print(f"DEBUG: check_password_hash senha (fallback): {senha_valida}")
            
            if senha_valida:
                print("DEBUG: Senha válida! Configurando sessão...")
                # Configurar sessão permanente
                session.permanent = True
                session['usuario_id'] = usuario.id
                session['usuario_email'] = usuario.email
                session['usuario_tipo'] = usuario.tipo
                print(f"DEBUG: Sessão configurada: {session}")
                
                # Redirecionamento condicional baseado no perfil
                if usuario.tipo in ['cliente', 'cliente_supervisor']:
                    return redirect(url_for('main.pre_dashboard'))
                
                return redirect(url_for('main.dashboard_gerencial'))
            else:
                print("DEBUG: Senha INVÁLIDA.")
        else:
            print("DEBUG: Usuário NÃO encontrado.")
        
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('auth.login'))
