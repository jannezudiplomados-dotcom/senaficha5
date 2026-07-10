import os
import uuid
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from werkzeug.utils import secure_filename
import models
from routes.auth import login_required, role_required

plantillas_bp = Blueprint('plantillas', __name__)

def _permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ('docx', 'xlsx')

@plantillas_bp.route('/')
@login_required
def index():
    plantillas_todas = models.listar_plantillas()
    programas = models.listar_programas()

    return render_template('plantillas/index.html',
                           plantillas=plantillas_todas,
                           programas=programas)

@plantillas_bp.route('/subir', methods=['POST'])
@login_required
def subir():
    archivo = request.files.get('plantilla')
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    programa_id = request.form.get('programa_id', type=int)
    tipo_generacion = request.form.get('tipo_generacion', 'ambos')
    
    if not archivo or archivo.filename == '' or not _permitido(archivo.filename):
        flash('Debes subir un archivo .docx o .xlsx valido.', 'danger')
        return redirect(url_for('plantillas.index'))
        
    if not programa_id:
        flash('Debes seleccionar un programa.', 'danger')
        return redirect(url_for('plantillas.index'))
        
    fname = f'{uuid.uuid4().hex}_{secure_filename(archivo.filename)}'
    archivo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
    pid = models.crear_plantilla(nombre or archivo.filename, fname, descripcion, programa_id, tipo_generacion)
    models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                         'CREAR', 'plantilla', pid, nombre, request.remote_addr)
    flash('Plantilla subida y asociada al programa.', 'success')
    return redirect(url_for('plantillas.index'))


@plantillas_bp.route('/eliminar/<int:pid>', methods=['POST'])
@login_required
@role_required('superadmin', 'admin')
def eliminar(pid):
    plantilla = models.obtener_plantilla(pid)
    if plantilla:
        ruta = os.path.join(current_app.config['UPLOAD_FOLDER'], plantilla['archivo'])
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass
        models.eliminar_plantilla(pid)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'ELIMINAR', 'plantilla', pid, None, request.remote_addr)
        flash('Plantilla eliminada.', 'success')
    return redirect(url_for('plantillas.index'))
