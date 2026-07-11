from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from mysql.connector import Error as MySQLError
import models
from routes.auth import login_required, role_required

programas_bp = Blueprint('programas', __name__)


@programas_bp.route('/')
@login_required
def index():
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except (ValueError, TypeError):
        page = 1
    search = request.args.get('q', '').strip() or None
    per_page = current_app.config['PER_PAGE']
    total = models.contar_programas(search)
    total_paginas = max((total + per_page - 1) // per_page, 1)
    programas = models.obtener_programas_paginados(page, per_page, search)
    return render_template('programas/index.html', programas=programas,
                           page=page, total_paginas=total_paginas,
                           search=search or '', total=total)


@programas_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        duracion = request.form.get('duracion_meses') or 0
        fecha_inicio = request.form.get('fecha_inicio') or None
        fecha_fin = request.form.get('fecha_fin') or None
        if not codigo or not nombre:
            flash('Codigo y nombre son obligatorios.', 'danger')
            return redirect(url_for('programas.nuevo'))
        try:
            pid = models.crear_programa(codigo, nombre, descripcion, int(duracion), fecha_inicio, fecha_fin)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'programa', pid, nombre, request.remote_addr)
            flash('Programa creado.', 'success')
            return redirect(url_for('programas.index'))
        except MySQLError as e:
            current_app.logger.error('Error creando programa: %s', e)
            flash('Error al crear el programa. Verifica que el codigo no exista.', 'danger')
        return redirect(url_for('programas.nuevo'))
    return render_template('programas/form.html', programa=None)


@programas_bp.route('/editar/<int:pid>', methods=['GET', 'POST'])
@login_required
def editar(pid):
    programa = models.obtener_programa(pid)
    if not programa:
        flash('Programa no encontrado.', 'warning')
        return redirect(url_for('programas.index'))
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        duracion = request.form.get('duracion_meses') or 0
        fecha_inicio = request.form.get('fecha_inicio') or None
        fecha_fin = request.form.get('fecha_fin') or None
        try:
            models.actualizar_programa(pid, codigo, nombre, descripcion, int(duracion), fecha_inicio, fecha_fin)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'programa', pid, nombre, request.remote_addr)
            flash('Programa actualizado.', 'success')
            return redirect(url_for('programas.index'))
        except MySQLError as e:
            current_app.logger.error('Error actualizando programa %s: %s', pid, e)
            flash('Error al actualizar el programa.', 'danger')
        return redirect(url_for('programas.editar', pid=pid))
    return render_template('programas/form.html', programa=programa)


@programas_bp.route('/eliminar/<int:pid>', methods=['POST'])
@login_required
@role_required('superadmin', 'admin')
def eliminar(pid):
    try:
        models.eliminar_programa(pid)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'ELIMINAR', 'programa', pid, None, request.remote_addr)
        flash('Programa eliminado.', 'success')
    except MySQLError as e:
        current_app.logger.error('Error eliminando programa %s: %s', pid, e)
        flash('No se pudo eliminar el programa.', 'danger')
    return redirect(url_for('programas.index'))
