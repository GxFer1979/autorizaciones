from flask import Flask
from .extensions import db  # Importa extensiones

def create_app():
    app = Flask(__name__)
    
    # Configuración (usa variables de entorno en Render)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-fallback')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    
    # Inicializa extensiones CON la app
    db.init_app(app)
    
    # Registra blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
