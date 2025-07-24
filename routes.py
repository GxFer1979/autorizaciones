from flask import Blueprint, current_app
import os
from datetime import datetime
import csv

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('formulario.html')

# ... (todas tus otras rutas aquí)
