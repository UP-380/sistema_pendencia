from app.extensions import db

class Segmento(db.Model):
    """Modelo para segmentos de negócio (FUNERÁRIA, PROTEÇÃO VEICULAR, FARMÁCIA)"""
    __tablename__ = 'segmento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relacionamento com empresas (one-to-many)
    empresas = db.relationship('Empresa', backref='segmento', lazy=True)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    segmento_id = db.Column(db.Integer, db.ForeignKey('segmento.id'), nullable=True)
