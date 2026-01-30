from app.extensions import db
from datetime import datetime
import secrets

class Pendencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(50), nullable=False, index=True)
    tipo_pendencia = db.Column(db.String(30), nullable=False, index=True)
    banco = db.Column(db.String(50), nullable=True)
    data = db.Column(db.Date, nullable=True)  # Data da Pendência (informada pelo usuário)
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)  # Data de Abertura (automática)
    fornecedor_cliente = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.String(300), default='DO QUE SE TRATA?')
    resposta_cliente = db.Column(db.String(300))
    email_cliente = db.Column(db.String(120), nullable=True, index=True)
    status = db.Column(db.String(50), default='PENDENTE CLIENTE', index=True)
    token_acesso = db.Column(db.String(100), unique=True, default=lambda: secrets.token_urlsafe(16), index=True)
    data_resposta = db.Column(db.DateTime)
    modificado_por = db.Column(db.String(50))
    nota_fiscal_arquivo = db.Column(db.String(300))  # Caminho do arquivo da nota fiscal
    natureza_operacao = db.Column(db.String(500))  # Campo para Natureza de Operação
    motivo_recusa = db.Column(db.String(500))  # Campo para motivo da recusa pelo operador
    motivo_recusa_supervisor = db.Column(db.String(500))  # Campo para motivo da recusa pelo supervisor
    # Novos campos para tipos especializados
    codigo_lancamento = db.Column(db.String(64), nullable=True)
    data_competencia = db.Column(db.Date, nullable=True)
    data_baixa = db.Column(db.Date, nullable=True)
    natureza_sistema = db.Column(db.String(120), nullable=True)
    # Campo para Lançamento Não Encontrado em Sistema
    tipo_credito_debito = db.Column(db.String(10), nullable=True, index=True)  # 'CREDITO' ou 'DEBITO'
    
    # Índices compostos para performance
    __table_args__ = (
        db.Index('idx_pendencia_empresa_status', 'empresa', 'status'),
        db.Index('idx_pendencia_status_tipo', 'status', 'tipo_pendencia'),
    )


class LogAlteracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pendencia_id = db.Column(db.Integer, db.ForeignKey('pendencia.id'), nullable=False)
    usuario = db.Column(db.String(120), nullable=False)
    tipo_usuario = db.Column(db.String(50), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    campo_alterado = db.Column(db.String(100))
    valor_anterior = db.Column(db.String(300))
    valor_novo = db.Column(db.String(300))

class Importacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(120), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    mensagem_erro = db.Column(db.String(500))
