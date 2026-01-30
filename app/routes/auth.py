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
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Tenta ambos os campos (senha_hash e senha) para compatibilidade
            senha_valida = False
            if hasattr(usuario, 'senha_hash'):
                senha_valida = check_password_hash(usuario.senha_hash, senha)
            elif hasattr(usuario, 'senha'):
                # Fallback para senha antiga se existir (apenas segurança)
                senha_valida = check_password_hash(usuario.senha, senha)
            
            if senha_valida:
                # Configurar sessão permanente
                session.permanent = True
                session['usuario_id'] = usuario.id
                session['usuario_email'] = usuario.email
                session['usuario_tipo'] = usuario.tipo
                
                # Redirecionar para a tela de segmentos (no blueprint main)
                return redirect(url_for('main.listar_segmentos'))
        
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('auth.login'))
