import os
from app import create_app, db
from app.models.pendencia import Pendencia
from app.models.empresa import Empresa

app = create_app()
with app.app_context():
    pendencia_companies = [c[0] for c in db.session.query(Pendencia.empresa).distinct().all()]
    empresa_companies = [e.nome for e in Empresa.query.all()]
    
    print("Inconsistent Company Names Mapping:")
    mismatches = []
    for pc in pendencia_companies:
        if pc not in empresa_companies:
            # Try to find a match where pc is a substring of ec or vice versa
            potential_matches = [ec for ec in empresa_companies if pc.lower() in ec.lower() or ec.lower() in pc.lower()]
            mismatches.append({
                'pendencia_name': pc,
                'potential_matches': potential_matches,
                'count': Pendencia.query.filter_by(empresa=pc).count()
            })
            
    for m in mismatches:
        print(f"  - '{m['pendencia_name']}' ({m['count']} items) -> Potential matches: {m['potential_matches']}")

    if not mismatches:
        print("No mismatches found!")
