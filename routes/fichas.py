from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from mysql.connector import Error as MySQLError
import models
from routes.auth import login_required, role_required

fichas_bp = Blueprint('fichas', __name__)


@fichas_bp.route('/')
@login_required
def index():
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except (ValueError, TypeError):
        page = 1
    search = request.args.get('q', '').strip() or None
    per_page = current_app.config['PER_PAGE']
    total = models.contar_fichas(search)
    total_paginas = max((total + per_page - 1) // per_page, 1)
    fichas = models.obtener_fichas_paginadas(page, per_page, search)
    return render_template('fichas/index.html', fichas=fichas,
                           page=page, total_paginas=total_paginas,
                           search=search or '', total=total)


@fichas_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        numero = request.form.get('numero', '').strip()
        programa_id = request.form.get('programa_id') or None
        colegio_id = request.form.get('colegio_id') or None
        jornada = request.form.get('jornada', 'Manana')
        fi = request.form.get('fecha_inicio') or None
        ff = request.form.get('fecha_fin') or None
        if not numero or not programa_id:
            flash('Numero y programa son obligatorios.', 'danger')
            return redirect(url_for('fichas.nuevo'))
        try:
            fid = models.crear_ficha(numero, int(programa_id), colegio_id, jornada, fi, ff)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'ficha', fid, numero, request.remote_addr)
            flash('Ficha creada.', 'success')
            return redirect(url_for('fichas.index'))
        except MySQLError as e:
            flash(f'Error: {e.msg}', 'danger')
        return redirect(url_for('fichas.nuevo'))
    return render_template('fichas/form.html', ficha=None, programas=models.listar_programas(), colegios=models.listar_colegios())


@fichas_bp.route('/editar/<int:fid>', methods=['GET', 'POST'])
@login_required
def editar(fid):
    ficha = models.obtener_ficha(fid)
    if not ficha:
        flash('Ficha no encontrada.', 'warning')
        return redirect(url_for('fichas.index'))
    if request.method == 'POST':
        numero = request.form.get('numero', '').strip()
        programa_id = request.form.get('programa_id') or None
        colegio_id = request.form.get('colegio_id') or None
        jornada = request.form.get('jornada', 'Manana')
        fi = request.form.get('fecha_inicio') or None
        ff = request.form.get('fecha_fin') or None
        try:
            models.actualizar_ficha(fid, numero, int(programa_id), colegio_id, jornada, fi, ff)
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'ficha', fid, numero, request.remote_addr)
            flash('Ficha actualizada.', 'success')
            return redirect(url_for('fichas.index'))
        except (MySQLError, ValueError, TypeError) as e:
            flash(f'Error: {e}', 'danger')
        return redirect(url_for('fichas.editar', fid=fid))
    return render_template('fichas/form.html', ficha=ficha, programas=models.listar_programas(), colegios=models.listar_colegios())


@fichas_bp.route('/eliminar/<int:fid>', methods=['POST'])
@login_required
@role_required('superadmin', 'admin')
def eliminar(fid):
    try:
        models.eliminar_ficha(fid)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'ELIMINAR', 'ficha', fid, None, request.remote_addr)
        flash('Ficha eliminada.', 'success')
    except MySQLError as e:
        flash(f'No se pudo eliminar: {e.msg}', 'danger')
    return redirect(url_for('fichas.index'))
