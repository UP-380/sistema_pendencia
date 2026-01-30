import os
import secrets
from datetime import timedelta

class Config:
    # Segredo (Estático para evitar erro de CSRF/Sessão inválida ao reiniciar)
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_secreta_fixa_para_desenvolvimento_local_up380')
    
    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pendencias.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Segurança de Sessão
    SESSION_COOKIE_SECURE = False # Localhost sem HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Upload Seguro
    MAX_CONTENT_LENGTH = 128 * 1024 * 1024  # 128 MB (Aumentado)
    UPLOAD_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls'}
    
    # E-mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # Webhook Teams
    TEAMS_WEBHOOK_URL = "https://upfinance.webhook.office.com/webhookb2/7c8dacfa-6413-4b34-9659-5be33e876493@62d96e16-cfeb-4bad-8803-4a764ac7339a/IncomingWebhook/a6612b3a144d4915bf9bc1171093c8c9/9cdf59ae-5ee6-4c43-8604-31390b2d5425/V21glDBnmGcX-HxLgk_gJxnhqHC79TV9BLey3t5_DzMbU1"
