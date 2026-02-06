import os
from app import create_app, db
from app.models.usuario import Usuario
from app.services.business import obter_empresas_para_usuario
from flask import session

app = create_app()
with app.app_context():
    user = Usuario.query.filter_by(email='adm.pendencia@up380.com.br').first()
    if user:
        print(f"User found: ID={user.id}, Email={user.email}, Tipo={user.tipo}")
        
        # Mock session
        with app.test_request_context():
            session['usuario_id'] = user.id
            session['usuario_tipo'] = user.tipo
            session['usuario_email'] = user.email
            
            companies = obter_empresas_para_usuario()
            print(f"Companies for user (count={len(companies)}):")
            print(companies[:10], "... [truncated]")
            
            # Check if these companies have pendencies
            from app.models.pendencia import Pendencia
            from sqlalchemy import and_
            
            count = Pendencia.query.filter(Pendencia.empresa.in_(companies)).count()
            print(f"Total Pendencies accessible for these companies: {count}")
    else:
        print("User not found!")
