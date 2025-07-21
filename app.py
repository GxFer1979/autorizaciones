from flask import Flask, request, jsonify, send_file, render_template
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY
import uuid
import base64
from datetime import datetime
import csv

app = Flask(__name__)
UPLOAD_FOLDER = 'autorizaciones'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
REGISTRO_CSV = os.path.join(UPLOAD_FOLDER, 'registro_autorizaciones.csv')
HISTORIAL_CSV = os.path.join(UPLOAD_FOLDER, 'historial_eventos.csv')

# Inicializar archivos CSV si no existen
def inicializar_archivos():
    # Archivo principal de autorizaciones
    if not os.path.exists(REGISTRO_CSV):
        with open(REGISTRO_CSV, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', 'Fecha_Generacion', 'Nombre_Padre', 'CI_Padre', 
                'Nombre_Menor', 'CI_Menor', 'Edad_Menor', 'Actividad',
                'Ciudad', 'Unidad', 'Jefe_Unidad', 'Fecha_Inicio',
                'Fecha_Fin', 'Hora_Regreso', 'Mes_Anio', 'Parentesco'
            ])
    
    # Archivo de historial por evento
    if not os.path.exists(HISTORIAL_CSV):
        with open(HISTORIAL_CSV, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Evento', 'Ciudad', 'Fecha_Inicio', 'Fecha_Fin',
                'Total_Autorizaciones', 'Ultima_Actualizacion'
            ])

inicializar_archivos()

@app.route('/')
def index():
    return render_template('formulario.html')

@app.route('/generar-autorizacion', methods=['POST'])
def generar_autorizacion():
    try:
        data = request.json
        id_unico = str(uuid.uuid4())[:8]
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Procesar firma
        firma_path = None
        if data['firma']:
            firma_data = base64.b64decode(data['firma'].split(',')[1])
            firma_path = os.path.join(UPLOAD_FOLDER, f"firma_{id_unico}.png")
            with open(firma_path, "wb") as f:
                f.write(firma_data)

        # Generar PDF
        pdf_path = os.path.join(UPLOAD_FOLDER, f"autorizacion_{id_unico}.pdf")
        crear_pdf_autorizacion(pdf_path, data, firma_path)
        
        # Registrar en CSV principal
        with open(REGISTRO_CSV, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                id_unico, fecha_actual,
                data['nombre_padre'], data['ci_padre'],
                data['nombre_menor'], data['ci_menor'],
                data['edad_menor'], data['actividad'],
                data['ciudad'], data['unidad'],
                data['jefe_unidad'], data['fecha_inicio'],
                data['fecha_fin'], data['hora_regreso'],
                data['mes_anio'], data['parentesco']
            ])

        # Actualizar historial de eventos
        actualizar_historial_eventos(
            data['actividad'],
            data['ciudad'],
            data['fecha_inicio'],
            data['fecha_fin']
        )

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def actualizar_historial_eventos(evento, ciudad, fecha_inicio, fecha_fin):
    evento_key = f"{evento}-{ciudad}-{fecha_inicio}"
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Leer historial existente
    eventos = []
    if os.path.exists(HISTORIAL_CSV):
        with open(HISTORIAL_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            eventos = list(reader)
    
    # Buscar si el evento ya existe
    encontrado = False
    for e in eventos:
        if f"{e['Evento']}-{e['Ciudad']}-{e['Fecha_Inicio']}" == evento_key:
            e['Total_Autorizaciones'] = str(int(e['Total_Autorizaciones']) + 1)
            e['Ultima_Actualizacion'] = fecha_actual
            encontrado = True
            break
    
    # Si no existe, agregarlo
    if not encontrado:
        eventos.append({
            'Evento': evento,
            'Ciudad': ciudad,
            'Fecha_Inicio': fecha_inicio,
            'Fecha_Fin': fecha_fin,
            'Total_Autorizaciones': '1',
            'Ultima_Actualizacion': fecha_actual
        })
    
    # Escribir de vuelta al archivo
    with open(HISTORIAL_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Evento', 'Ciudad', 'Fecha_Inicio', 'Fecha_Fin',
            'Total_Autorizaciones', 'Ultima_Actualizacion'
        ])
        writer.writeheader()
        writer.writerows(eventos)

def crear_pdf_autorizacion(pdf_path, data, firma_path=None):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Configuración de estilos
    estilo_justificado = ParagraphStyle(
        name='Justificado',
        alignment=TA_JUSTIFY,
        fontSize=12,
        fontName='Helvetica',
        leading=14,
        spaceAfter=12
    )
    
    estilo_titulo = ParagraphStyle(
        name='Titulo',
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=1,
        spaceAfter=20
    )
    
    # Título
    titulo = Paragraph("AUTORIZACIÓN", estilo_titulo)
    titulo.wrapOn(c, width, height)
    titulo.drawOn(c, 0, height-50)
    
    # Texto de la autorización
    texto = f"""
    YO {data['nombre_padre'].upper()}, autorizo a mi hijo/a {data['nombre_menor'].upper()}, 
    con C.I. N° {data['ci_menor']} de {data['edad_menor']} años de edad, a participar de la 
    actividad {data['actividad'].upper()}, a realizarse en la ciudad de {data['ciudad'].upper()}, 
    organizada por la Unidad de {data['unidad'].upper()} del Grupo Scout N° 9 "LA MERCED", 
    a cargo del Jefe de Unidad: {data['jefe_unidad'].upper()}. El inicio de la actividad está 
    prevista el día {data['fecha_inicio']}, y el regreso el día {data['fecha_fin']} a las 
    {data['hora_regreso']} horas aproximadamente. Se expide la presente autorización a los 
    {datetime.now().day} del mes de {data['mes_anio']}.
    """
    
    parrafo = Paragraph(texto, estilo_justificado)
    parrafo.wrapOn(c, width-100, height)
    parrafo.drawOn(c, 50, height-200)
    
    # Firma digital
    if firma_path:
        firma_img = ImageReader(firma_path)
        c.drawImage(firma_img, 100, 150, width=200, height=80, preserveAspectRatio=True)
    
    # Sección de firma
    c.line(100, 130, 300, 130)
    c.setFont("Helvetica", 10)
    c.drawString(100, 110, f"NOMBRE Y APELLIDO: {data['nombre_padre'].upper()}")
    c.drawString(100, 90, f"(aclarar si es padre, madre o Tutor Legal): {data['parentesco'].upper()}")
    c.drawString(100, 70, f"C.I. N°: {data['ci_padre']}")
    
    c.save()

@app.route('/listado-autorizaciones')
def listado_autorizaciones():
    try:
        with open(REGISTRO_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            autorizaciones = list(reader)
        return jsonify(autorizaciones)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/historial-eventos')
def historial_eventos():
    try:
        with open(HISTORIAL_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            eventos = list(reader)
        
        # Ordenar por fecha más reciente
        eventos_ordenados = sorted(
            eventos,
            key=lambda x: x['Ultima_Actualizacion'],
            reverse=True
        )
        
        return jsonify(eventos_ordenados)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)