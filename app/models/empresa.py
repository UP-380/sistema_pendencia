from app.extensions import db

class Segmento(db.Model):
    """Modelo para segmentos de negócio (FUNERÁRIA, PROTEÇÃO VEICULAR, FARMÁCIA)"""
    __tablename__ = 'segmento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    cor = db.Column(db.String(20), default='#1F4E78')
    icone = db.Column(db.String(50), default='building')
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relacionamento com empresas (one-to-many)
    empresas = db.relationship('Empresa', backref='segmento', lazy=True)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    segmento_id = db.Column(db.Integer, db.ForeignKey('segmento.id'), nullable=True)
