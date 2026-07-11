from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from mysql.connector import Error as MySQLError
import models
from routes.auth import login_required, role_required

colegios_bp = Blueprint('colegios', __name__)

@colegios_bp.route('/')
@login_required
def index():
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except (ValueError, TypeError):
        page = 1
    search = request.args.get('q', '').strip() or None
    per_page = current_app.config['PER_PAGE']
    total = models.contar_colegios(search)
    total_paginas = max((total + per_page - 1) // per_page, 1)
    colegios = models.obtener_colegios_paginados(page, per_page, search)
    return render_template('colegios/index.html', colegios=colegios,
                           page=page, total_paginas=total_paginas,
                           search=search or '', total=total)

@colegios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre_colegio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        if not nombre:
            flash('El nombre del colegio es obligatorio.', 'danger')
            return redirect(url_for('colegios.nuevo'))
        try:
            cid = models.crear_colegio(nombre, descripcion)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'colegio', cid, nombre, request.remote_addr)
            flash('Colegio creado exitosamente.', 'success')
            return redirect(url_for('colegios.index'))
        except MySQLError as e:
            current_app.logger.error('Error creando colegio: %s', e)
            flash('Error al crear el colegio.', 'danger')
        return redirect(url_for('colegios.nuevo'))
    return render_template('colegios/form.html', colegio=None)

@colegios_bp.route('/editar/<int:cid>', methods=['GET', 'POST'])
@login_required
def editar(cid):
    colegio = models.obtener_colegio(cid)
    if not colegio:
        flash('Colegio no encontrado.', 'warning')
        return redirect(url_for('colegios.index'))
        
    if request.method == 'POST':
        nombre = request.form.get('nombre_colegio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        if not nombre:
            flash('El nombre del colegio es obligatorio.', 'danger')
            return redirect(url_for('colegios.editar', cid=cid))
            
        try:
            models.actualizar_colegio(cid, nombre, descripcion)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'colegio', cid, nombre, request.remote_addr)
            flash('Colegio actualizado correctamente.', 'success')
            return redirect(url_for('colegios.index'))
        except MySQLError as e:
            current_app.logger.error('Error actualizando colegio %s: %s', cid, e)
            flash('Error al actualizar el colegio.', 'danger')
        return redirect(url_for('colegios.editar', cid=cid))
    return render_template('colegios/form.html', colegio=colegio)

@colegios_bp.route('/eliminar/<int:cid>', methods=['POST'])
@login_required
@role_required('superadmin', 'admin')
def eliminar(cid):
    try:
        models.eliminar_colegio(cid)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'ELIMINAR', 'colegio', cid, None, request.remote_addr)
        flash('Colegio eliminado.', 'success')
    except MySQLError as e:
        current_app.logger.error('Error eliminando colegio %s: %s', cid, e)
        flash('No se pudo eliminar el colegio.', 'danger')
    return redirect(url_for('colegios.index'))
