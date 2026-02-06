import os
from app import create_app, db
from app.models.pendencia import Pendencia
from app.models.empresa import Empresa

app = create_app()
with app.app_context():
    print("--- Harmonizing Company Names ---")
    pendencia_companies = [c[0] for c in db.session.query(Pendencia.empresa).distinct().all()]
    empresa_companies = [e.nome for e in Empresa.query.all()]
    
    corrections = 0
    for pc in pendencia_companies:
        if pc not in empresa_companies:
            # Try to find exactly ONE match where pc is a prefix or substring
            matches = [ec for ec in empresa_companies if pc.lower() in ec.lower()]
            
            if len(matches) == 1:
                target = matches[0]
                count = Pendencia.query.filter_by(empresa=pc).count()
                print(f"  Fixing '{pc}' -> '{target}' ({count} records)")
                Pendencia.query.filter_by(empresa=pc).update({Pendencia.empresa: target})
                corrections += count
            elif len(matches) > 1:
                print(f"  AMBIGUOUS: '{pc}' matches multiple companies {matches}. Skipping.")
            else:
                print(f"  NOT FOUND: No company in Empresa table matches '{pc}'.")
    
    db.session.commit()
    print(f"\nTotal corrections applied: {corrections}")
    print("Cleanup finished!")
