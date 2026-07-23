from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
import os
from werkzeug.utils import secure_filename

from servicios import bam_models
import models

bp = Blueprint('bitacoras_art_media', __name__, template_folder='templates')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Por favor inicie sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    return render_template('bitacoras_art_media/index.html')

@bp.route('/historial')
@login_required
def historial():
    bitacoras = bam_models.listar_bitacoras()
    return render_template('bitacoras_art_media/historial.html', bitacoras=bitacoras)

@bp.route('/nueva')
@login_required
def nueva_bitacora():
    return render_template('bitacoras_art_media/index.html')

@bp.route('/plantillas', methods=['GET', 'POST'])
@login_required
def plantillas_list():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        hoja_objetivo = request.form.get('hoja_objetivo', 'Formato Bitácora Art. Media')
        archivo = request.files.get('archivo_excel')
        
        if not archivo or not archivo.filename.endswith('.xlsx'):
            flash('Debe subir un archivo válido (.xlsx)', 'danger')
            return redirect(url_for('bitacoras_art_media.plantillas_list'))
            
        filename = secure_filename(archivo.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'plantillas')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        archivo.save(file_path)
        
        rel_path = os.path.join('static', 'uploads', 'plantillas', filename)
        
        bam_models.crear_plantilla(
            nombre=nombre,
            archivo_ruta=rel_path,
            hoja_objetivo=hoja_objetivo,
            creado_por=None
        )
        
        flash('Plantilla subida y registrada exitosamente', 'success')
        return redirect(url_for('bitacoras_art_media.plantillas_list'))

    plantillas = bam_models.listar_plantillas()
    return render_template('bitacoras_art_media/plantillas_list.html', plantillas=plantillas)

@bp.route('/plantillas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_plantilla_route(id):
    plantilla = bam_models.obtener_plantilla(id)
    if plantilla:
        ruta_archivo = plantilla.get('archivo_ruta')
        
        try:
            # Primero intentar eliminar de la base de datos
            bam_models.eliminar_plantilla(id)
            
            # Si se elimina de la BD correctamente, borrar el archivo físico
            if ruta_archivo:
                abs_path = os.path.join(current_app.root_path, ruta_archivo.replace('/', os.sep).replace('\\', os.sep))
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                    except Exception as e:
                        print(f"Error al eliminar archivo físico de plantilla: {e}")
            
            flash('Plantilla y archivo físico eliminados correctamente.', 'success')
        except Exception as e:
            print(f"Error BD al eliminar plantilla: {e}")
            flash('Error al eliminar la plantilla. Es posible que existan bitácoras asociadas a esta plantilla.', 'danger')
    else:
        flash('Plantilla no encontrada.', 'danger')
        
    return redirect(url_for('bitacoras_art_media.plantillas_list'))

@bp.route('/detalle/<int:id>')
@login_required
def ver_detalle(id):
    bitacora = bam_models.obtener_bitacora(id)
    if not bitacora:
        flash('Bitácora no encontrada.', 'danger')
        return redirect(url_for('bitacoras_art_media.historial'))
    
    # Obtener relaciones
    aprendices = bam_models.obtener_aprendices_bitacora(id)
    actividades = bam_models.obtener_actividades_bitacora(id)
    
    return render_template('bitacoras_art_media/detalle.html', bitacora=bitacora, aprendices=aprendices, actividades=actividades)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    bam_models.eliminar_bitacora(id)
    flash('Bitácora eliminada correctamente.', 'success')
    return redirect(url_for('bitacoras_art_media.historial'))

@bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if request.method == 'POST':
        config_data = {
            'entidad_nombre': request.form.get('entidad_nombre'),
            'entidad_nit': request.form.get('entidad_nit'),
            'entidad_direccion': request.form.get('entidad_direccion')
        }
        bam_models.actualizar_config(config_data)
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('.configuracion'))
        
    configuracion_actual = bam_models.obtener_config()
    return render_template('bitacoras_art_media/config.html', config=configuracion_actual)
