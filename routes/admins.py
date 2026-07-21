import re
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from mysql.connector import Error as MySQLError
import models
import os
import uuid
import base64
import binascii
from werkzeug.security import generate_password_hash
from routes.auth import login_required, role_required

admins_bp = Blueprint('admins', __name__)


def _validar_password(password):
    """Valida complejidad minima de contrasena.
    Retorna None si es valida, o un mensaje de error."""
    if len(password) < 8:
        return 'La contrasena debe tener al menos 8 caracteres.'
    if not re.search(r'[A-Z]', password):
        return 'La contrasena debe incluir al menos una letra mayuscula.'
    if not re.search(r'[0-9]', password):
        return 'La contrasena debe incluir al menos un numero.'
    return None

def _guardar_firma(firma_base64, firma_file, firma_actual=None):
    """Guarda la firma ya sea desde el canvas (base64) o desde un archivo subido.
    Da prioridad al archivo subido."""
    nombre = None
    datos = None

    if firma_file and firma_file.filename:
        firma_file.seek(0, os.SEEK_END)
        size = firma_file.tell()
        firma_file.seek(0)
        if size > 2 * 1024 * 1024:
            raise ValueError("La imagen de la firma supera el tamaño máximo de 2MB.")
        
        datos = firma_file.read()
        ext = firma_file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ['png', 'jpg', 'jpeg']:
            ext = 'png'
        nombre = f'firma_admin_{uuid.uuid4().hex}.{ext}'
    elif firma_base64:
        if ',' in firma_base64:
            firma_base64 = firma_base64.split(',', 1)[1]
        try:
            datos = base64.b64decode(firma_base64)
            nombre = f'firma_admin_{uuid.uuid4().hex}.png'
        except (binascii.Error, ValueError):
            raise ValueError('La firma desde el lienzo no es válida.')
    
    if not nombre or not datos:
        return firma_actual

    ruta = os.path.join(current_app.config['FIRMAS_FOLDER'], nombre)
    with open(ruta, 'wb') as fh:
        fh.write(datos)

    if firma_actual:
        anterior = os.path.join(current_app.config['FIRMAS_FOLDER'], firma_actual)
        if os.path.exists(anterior):
            try:
                os.remove(anterior)
            except OSError:
                pass
    return nombre


@admins_bp.route('/')
@login_required
@role_required('superadmin')
def index():
    return render_template('admins/index.html', admins=models.listar_admins())


@admins_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def nuevo():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nombre = request.form.get('nombre', '').strip()
        rol = request.form.get('rol', 'admin')
        programa_id = request.form.get('programa_id')
        if programa_id and programa_id.isdigit():
            programa_id = int(programa_id)
        else:
            programa_id = None
            
        if not username or not password or not nombre:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('admins.nuevo'))
        error_pw = _validar_password(password)
        if error_pw:
            flash(error_pw, 'danger')
            return redirect(url_for('admins.nuevo'))
        try:
            firma = _guardar_firma(request.form.get('firma_base64', ''), request.files.get('firma_imagen'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('admins.nuevo'))

        try:
            aid = models.crear_admin(username, generate_password_hash(password), nombre, rol, programa_id, firma)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'admin', aid, username, request.remote_addr)
            flash('Administrador creado.', 'success')
            return redirect(url_for('admins.index'))
        except MySQLError as e:
            current_app.logger.error('Error creando admin: %s', e)
            flash('Error al crear el administrador. Verifica que el usuario no exista.', 'danger')
        return redirect(url_for('admins.nuevo'))
    programas = models.listar_programas()
    return render_template('admins/form.html', admin=None, programas=programas)


@admins_bp.route('/editar/<int:aid>', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def editar(aid):
    admin = models.obtener_admin(aid)
    if not admin:
        flash('Administrador no encontrado.', 'warning')
        return redirect(url_for('admins.index'))
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        rol = request.form.get('rol', 'admin')
        programa_id = request.form.get('programa_id')
        if programa_id and programa_id.isdigit():
            programa_id = int(programa_id)
        else:
            programa_id = None
            
        activo = 1 if request.form.get('activo') == 'on' else 0
        password = request.form.get('password', '')
        if password:
            error_pw = _validar_password(password)
            if error_pw:
                flash(error_pw, 'danger')
                return redirect(url_for('admins.editar', aid=aid))
        try:
            firma = _guardar_firma(request.form.get('firma_base64', ''), request.files.get('firma_imagen'), admin.get('firma'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('admins.editar', aid=aid))

        try:
            models.actualizar_admin(aid, nombre, rol, activo, programa_id,
                                    generate_password_hash(password) if password else None, firma)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'admin', aid, admin['username'], request.remote_addr)
            flash('Administrador actualizado.', 'success')
            return redirect(url_for('admins.index'))
        except MySQLError as e:
            current_app.logger.error('Error actualizando admin %s: %s', aid, e)
            flash('Error al actualizar el administrador.', 'danger')
        return redirect(url_for('admins.editar', aid=aid))
    programas = models.listar_programas()
    return render_template('admins/form.html', admin=admin, programas=programas)


@admins_bp.route('/eliminar/<int:aid>', methods=['POST'])
@login_required
@role_required('superadmin')
def eliminar(aid):
    if aid == session.get('admin_id'):
        flash('No puedes eliminar tu propia cuenta.', 'warning')
        return redirect(url_for('admins.index'))
    try:
        models.eliminar_admin(aid)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'ELIMINAR', 'admin', aid, None, request.remote_addr)
        flash('Administrador eliminado.', 'success')
    except MySQLError as e:
        current_app.logger.error('Error eliminando admin %s: %s', aid, e)
        flash('No se pudo eliminar el administrador.', 'danger')
    return redirect(url_for('admins.index'))
