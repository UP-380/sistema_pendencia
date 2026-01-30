from app.extensions import db

# Tabela de associação para Many-to-Many entre Usuario e Empresa
usuario_empresas = db.Table('usuario_empresas',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('empresa_id', db.Integer, db.ForeignKey('empresa.id'))
)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'adm', 'operador', 'cliente'
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    # Importação atrasada ou string para evitar ciclo se necessário, mas 'Empresa' funciona se importada ou via string (se suportado pelo flask-sqlalchemy com registry, mas aqui usamos db.Model compartilhado)
    # Usando string 'Empresa' assume que o modelo foi registrado no metadata.
    empresas = db.relationship('Empresa', secondary=usuario_empresas, backref='usuarios')

class PermissaoUsuarioTipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_usuario = db.Column(db.String(20), nullable=False)
    funcionalidade = db.Column(db.String(50), nullable=False)
    permitido = db.Column(db.Boolean, default=True)

class PermissaoUsuarioPersonalizada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    funcionalidade = db.Column(db.String(50), nullable=False)
    permitido = db.Column(db.Boolean, default=True)
