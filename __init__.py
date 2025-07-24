from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    # Configuración para Render
    app.config['UPLOAD_FOLDER'] = '/var/data/autorizaciones'  # Ruta persistente
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Importa y registra blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
