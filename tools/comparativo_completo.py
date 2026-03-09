import os
from app import create_app, db
from app.models.pendencia import Pendencia
from app.models.empresa import Empresa

app = create_app()
with app.app_context():
    pendencia_cos = [c[0] for c in db.session.query(Pendencia.empresa, db.func.count(Pendencia.id)).group_by(Pendencia.empresa).all()]
    empresa_cos = [e.nome for e in Empresa.query.all()]
    
    print("Full Comparison:")
    for pc in pendencia_cos:
        status = "[MATCH]" if pc in empresa_cos else "[MISMATCH]"
        print(f"  - {status} '{pc}'")
