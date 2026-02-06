import os
from app import create_app, db
from app.models.pendencia import Pendencia
from app.models.empresa import Empresa
from sqlalchemy import func

app = create_app()
with app.app_context():
    print("--- Diagnostic Report ---")
    total = Pendencia.query.count()
    print(f"Total Pendencies: {total}")
    
    if total > 0:
        latest = Pendencia.query.order_by(Pendencia.data_abertura.desc()).first()
        print(f"Latest Pendency Date Abertura: {latest.data_abertura}")
        print(f"Latest Pendency Date (Document): {latest.data}")
        
        # Count by company
        by_company = db.session.query(Pendencia.empresa, func.count(Pendencia.id)).group_by(Pendencia.empresa).all()
        print("Count by Company:")
        for company, count in by_company:
            print(f"  - {company}: {count}")
            
        # Check some names
        all_companies = [e.nome for e in Empresa.query.all()]
        print(f"Companies in system: {all_companies}")
    else:
        print("No pendencies found in the database!")
