import os
from app import create_app, db
from app.models.pendencia import Pendencia
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.services.business import obter_empresas_para_usuario
from flask import session

app = create_app()
with app.app_context():
    user = Usuario.query.filter_by(email='adm.pendencia@up380.com.br').first()
    if user:
        with app.test_request_context():
            session['usuario_id'] = user.id
            session['usuario_tipo'] = user.tipo
            session['usuario_email'] = user.email
            
            allowed = obter_empresas_para_usuario()
            all_pendencia_cos = [c[0] for c in db.session.query(Pendencia.empresa).distinct().all()]
            
            print(f"User Allowed Companies: {allowed[:5]} ...")
            print(f"Pendencia Table Companies: {all_pendencia_cos[:5]} ...")
            
            missing = [c for c in all_pendencia_cos if c not in allowed]
            print(f"\nCompanies with pendencies but NOT in allowed list ({len(missing)}):")
            for m in missing:
                count = Pendencia.query.filter_by(empresa=m).count()
                print(f"  - '{m}' ({count} pendencies)")
    else:
        print("User not found")
