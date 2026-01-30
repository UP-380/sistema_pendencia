from flask import Flask
from config import Config
from app.extensions import db, mail, migrate
from app.utils.filters import datetime_local_filter, nome_tipo_usuario_filter
from flask_cors import CORS

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS for development (Vite runs on 5173)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    # Register Template Filters
    app.template_filter('datetime_local')(datetime_local_filter)
    app.template_filter('nome_tipo_usuario')(nome_tipo_usuario_filter)
    
    # Register global context processors (if any needed besides blueprints)
    # main_bp already registers logic-specific ones.

    from flask_wtf.csrf import CSRFProtect
    from flask_talisman import Talisman
    
    CSRFProtect(app)
    
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "cdn.jsdelivr.net", "app-cdn.clickup.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
        'font-src': ["'self'", "cdn.jsdelivr.net", "fonts.gstatic.com"],
        'img-src': ["'self'", "data:"],
        'frame-src': ["forms.clickup.com"],
        'connect-src': ["'self'", "cdn.jsdelivr.net"]
    }
    
    Talisman(
        app,
        force_https=False,  # Set to True in production
        strict_transport_security=False,
        content_security_policy=csp,
        content_security_policy_nonce_in=[]
    )

    return app
