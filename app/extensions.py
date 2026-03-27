from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Convenção de nomenclatura padrão para o SQLAlchemy
# Isso ensina o banco e o Alembic a darem os mesmos nomes para as restrições, matando o bug de "fantasmas"
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)

# Listener para ativar as Foreign Keys no SQLite (PRAGMA foreign_keys=ON)
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Verifica se a conexão é do SQLite antes de aplicar
    if type(dbapi_connection).__name__ == "Connection":
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except:
            pass

mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
