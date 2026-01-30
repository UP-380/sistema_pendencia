#!/usr/bin/env python3
"""
Script para criar usuário de teste: luiz.marcelo@up380.com.br
"""

from app import app, db, Usuario
from werkzeug.security import generate_password_hash

def criar_usuario_teste():
    """Cria o usuário de teste solicitado"""
    with app.app_context():
        email = 'luiz.marcelo@up380.com.br'
        senha = 'Finance.@2'
        tipo = 'adm'
        
        # Verificar se já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            print(f"⚠️  Usuário {email} já existe!")
            print(f"   ID: {usuario_existente.id}")
            print(f"   Tipo: {usuario_existente.tipo}")
            print(f"   Ativo: {getattr(usuario_existente, 'ativo', True)}")
            
            # Atualizar senha e tipo se necessário
            usuario_existente.senha_hash = generate_password_hash(senha)
            usuario_existente.tipo = tipo
            if hasattr(usuario_existente, 'ativo'):
                usuario_existente.ativo = True
            db.session.commit()
            print(f"✅ Usuário atualizado com sucesso!")
        else:
            # Criar novo usuário
            novo_usuario = Usuario(
                email=email,
                senha_hash=generate_password_hash(senha),
                tipo=tipo,
                ativo=True
            )
            db.session.add(novo_usuario)
            db.session.commit()
            print(f"✅ Usuário criado com sucesso!")
            print(f"   Email: {email}")
            print(f"   Tipo: {tipo}")
            print(f"   Senha: {senha}")
        
        print("\n📋 Credenciais de acesso:")
        print(f"   Email: {email}")
        print(f"   Senha: {senha}")
        print(f"   Tipo: {tipo}")

if __name__ == '__main__':
    print("=" * 60)
    print("CRIAR USUÁRIO DE TESTE")
    print("=" * 60)
    criar_usuario_teste()
    print("=" * 60)




