from flask import Flask, session, request
import app.routes.api as api_module
from app.extensions import db
from app.models import Usuario, Pendencia
from config import Config
from sqlalchemy import func, and_

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Register blueprint to test route behavior? Or just import function? 
# Route functions are just functions if not decorating. 
# But they use request/session proxies.

def test_api():
    with app.test_request_context('/api/dashboard/metrics?empresas=todas'):
        # Mock session
        session['usuario_id'] = 1 # Admin ID usually
        session['usuario_tipo'] = 'adm'
        
        try:
            # We need to manually call the logic inside api_dashboard_metrics 
            # or replicate the query construction to fail it.
            
            # Replicating logic partially for debug
            base_clauses = [Pendencia.empresa.in_(['TESTE'])]
            
             # Case 1: No dates
            print("Testing validation logic...")
            
            # Case 2: Run the actual query construction
            print("Testing Query Construction...")
            
            # Let's try to run the actual function if possible, but decorators might get in the way.
            # We can use the test_client to hit the endpoint.
            
        except Exception as e:
            print(e)

if __name__ == "__main__":
    # Use test client to hit the actual route
    app.register_blueprint(api_module.api_bp)
    
    with app.app_context():
        # Find a supervisor user
        u = Usuario.query.filter_by(tipo='supervisor').first()
        if not u:
            print("No supervisor user found")
            try:
                 u = Usuario.query.filter_by(tipo='adm').first()
                 print(f"Fallback to admin: {u.email}")
            except:
                exit(1)
        else:
             print(f"Using user: {u.email} (Type: {u.tipo})")
        
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['usuario_id'] = u.id
            sess['usuario_tipo'] = u.tipo
            
        print("Sending request...")
        # Simulating what frontend sends: ?empresas=todas (or specific list)
        # Note: if supervisor, frontend might send ?empresas=EmpresaA,EmpresaB if 'todas' is selected but JS resolves to list?
        # Actually my JS sends 'todas' if all selected.
        resp = client.get('/api/dashboard/metrics?empresas=todas')
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error Data: {resp.get_data(as_text=True)}")
        else:
             # Check if JSON is valid
             print("JSON Response keys:", resp.json.keys())
