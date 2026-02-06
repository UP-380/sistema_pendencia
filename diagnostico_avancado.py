import os
from app import create_app, db
from app.models.pendencia import Pendencia
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from flask import session

app = create_app()
with app.app_context():
    print("--- Detailed Diagnostic ---")
    
    # 1. Total Pendencies
    total = Pendencia.query.count()
    print(f"Total Pendencies in DB: {total}")
    
    # 2. Unique company names in Pendencia table
    pendencia_companies = db.session.query(Pendencia.empresa).distinct().all()
    pendencia_companies = [c[0] for c in pendencia_companies]
    print(f"Companies with pendencies in DB: {pendencia_companies}")
    
    # 3. Companies in Empresa table
    empresa_table_names = [e.nome for e in Empresa.query.all()]
    print(f"Companies in Empresa table: {empresa_table_names}")
    
    # 4. Check for case/whitespace mismatches
    print("\nMismatch Check:")
    for pc in pendencia_companies:
        if pc not in empresa_table_names:
            print(f"  WARNING: Company '{pc}' in Pendencias but NOT in Empresa table!")
            
    # 5. Check user access (simulating a login if possible or just checking a user)
    # Since I don't have the active session, I'll check all users or a specific one if I can find an admin
    admin = Usuario.query.filter_by(tipo='adm').first()
    if admin:
        print(f"\nExample User: {admin.email} ({admin.tipo})")
        # In a real session, obter_empresas_para_usuario uses session['usuario_email']
        # Let's see what that would return for this user
        # Note: I'll manually check the linkage if I have the code for obter_empresas_para_usuario
    
    # 6. Sample Pendency Data
    if total > 0:
        p = Pendencia.query.first()
        print(f"\nSample Pendency:")
        print(f"  ID: {p.id}")
        print(f"  Empresa: '{p.empresa}'")
        print(f"  Status: {p.status}")
        print(f"  Data Abertura: {p.data_abertura}")
