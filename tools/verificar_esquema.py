from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    i = inspect(db.engine)
    columns = [c['name'] for c in i.get_columns('pendencia')]
    print("Columns in 'pendencia' table:")
    for col in columns:
        print(f"  - {col}")
