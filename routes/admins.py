import re
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from mysql.connector import Error as MySQLError
import models
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
        if not username or not password or not nombre:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('admins.nuevo'))
        error_pw = _validar_password(password)
        if error_pw:
            flash(error_pw, 'danger')
            return redirect(url_for('admins.nuevo'))
        try:
            aid = models.crear_admin(username, generate_password_hash(password), nombre, rol)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'admin', aid, username, request.remote_addr)
            flash('Administrador creado.', 'success')
            return redirect(url_for('admins.index'))
        except MySQLError as e:
            current_app.logger.error('Error creando admin: %s', e)
            flash('Error al crear el administrador. Verifica que el usuario no exista.', 'danger')
        return redirect(url_for('admins.nuevo'))
    return render_template('admins/form.html', admin=None)


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
        activo = 1 if request.form.get('activo') == 'on' else 0
        password = request.form.get('password', '')
        if password:
            error_pw = _validar_password(password)
            if error_pw:
                flash(error_pw, 'danger')
                return redirect(url_for('admins.editar', aid=aid))
        try:
            models.actualizar_admin(aid, nombre, rol, activo,
                                    generate_password_hash(password) if password else None)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'admin', aid, admin['username'], request.remote_addr)
            flash('Administrador actualizado.', 'success')
            return redirect(url_for('admins.index'))
        except MySQLError as e:
            current_app.logger.error('Error actualizando admin %s: %s', aid, e)
            flash('Error al actualizar el administrador.', 'danger')
        return redirect(url_for('admins.editar', aid=aid))
    return render_template('admins/form.html', admin=admin)


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
