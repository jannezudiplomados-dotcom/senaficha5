import os
import base64
import binascii
import uuid
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from mysql.connector import Error as MySQLError
import models
from routes.auth import login_required, role_required

usuarios_bp = Blueprint('usuarios', __name__)


def _guardar_firma(firma_base64, firma_file, firma_actual=None):
    """Guarda la firma ya sea desde el canvas (base64) o desde un archivo subido.
    Da prioridad al archivo subido."""
    nombre = None
    datos = None

    if firma_file and firma_file.filename:
        # Validar tamaño (2MB)
        firma_file.seek(0, os.SEEK_END)
        size = firma_file.tell()
        firma_file.seek(0)
        if size > 2 * 1024 * 1024:
            raise ValueError("La imagen de la firma supera el tamaño máximo de 2MB.")
        
        datos = firma_file.read()
        ext = firma_file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ['png', 'jpg', 'jpeg']:
            ext = 'png'
        nombre = f'firma_{uuid.uuid4().hex}.{ext}'
    elif firma_base64:
        if ',' in firma_base64:
            firma_base64 = firma_base64.split(',', 1)[1]
        try:
            datos = base64.b64decode(firma_base64)
            nombre = f'firma_{uuid.uuid4().hex}.png'
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


def _form_aprendiz():
    """Extrae y normaliza los datos del formulario.
    Clave: ficha_id vacio -> None (evita el error 500 al actualizar)."""
    ficha_id = request.form.get('ficha_id') or None
    if ficha_id:
        ficha_id = int(ficha_id)
    return {
        'identificacion': request.form.get('identificacion', '').strip(),
        'tipo': request.form.get('tipo_documento', 'CC'),
        'nombres': request.form.get('nombres', '').strip(),
        'apellidos': request.form.get('apellidos', '').strip(),
        'correo': request.form.get('correo', '').strip() or None,
        'telefono': request.form.get('telefono', '').strip() or None,
        'direccion': request.form.get('direccion', '').strip() or None,
        'ficha_id': ficha_id,
        'estado': request.form.get('estado', 'Activo'),
    }


@usuarios_bp.route('/')
@login_required
def index():
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except (ValueError, TypeError):
        page = 1
    search = request.args.get('q', '').strip() or None
    per_page = current_app.config['PER_PAGE']
    total = models.contar_usuarios(search)
    total_paginas = max((total + per_page - 1) // per_page, 1)
    aprendices = models.obtener_usuarios_paginados(page, per_page, search)
    return render_template('usuarios/index.html', aprendices=aprendices,
                           page=page, total_paginas=total_paginas,
                           search=search or '', total=total)


@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        d = _form_aprendiz()
        if not d['identificacion'] or not d['nombres'] or not d['apellidos']:
            flash('Identificacion, nombres y apellidos son obligatorios.', 'danger')
            return redirect(url_for('usuarios.nuevo'))
        if models.usuario_existe(d['identificacion']):
            flash('Ya existe un aprendiz con esa identificacion.', 'danger')
            return redirect(url_for('usuarios.nuevo'))
        try:
            firma = _guardar_firma(request.form.get('firma_base64', ''), request.files.get('firma_imagen'))
            uid = models.crear_usuario(
                d['identificacion'], d['tipo'], d['nombres'], d['apellidos'],
                d['correo'], d['telefono'], d['direccion'], d['ficha_id'], firma, d['estado'])
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'usuario', uid,
                                 f"Aprendiz {d['nombres']} {d['apellidos']}", request.remote_addr)
            flash('Aprendiz creado correctamente.', 'success')
            return redirect(url_for('usuarios.index'))
        except ValueError as e:
            flash(str(e), 'danger')
        except MySQLError as e:
            current_app.logger.error('Error BD al crear aprendiz: %s', e)
            flash('Error de base de datos al crear el aprendiz.', 'danger')
        except Exception as e:
            current_app.logger.exception('Error al crear aprendiz')
            flash('Ha ocurrido un error inesperado.', 'danger')
        return redirect(url_for('usuarios.nuevo'))

    return render_template('usuarios/form.html', aprendiz=None,
                           fichas=models.listar_fichas())


@usuarios_bp.route('/editar/<int:uid>', methods=['GET', 'POST'])
@login_required
def editar(uid):
    aprendiz = models.obtener_usuario(uid)
    if not aprendiz:
        flash('Aprendiz no encontrado.', 'warning')
        return redirect(url_for('usuarios.index'))

    if request.method == 'POST':
        d = _form_aprendiz()
        if not d['identificacion'] or not d['nombres'] or not d['apellidos']:
            flash('Identificacion, nombres y apellidos son obligatorios.', 'danger')
            return redirect(url_for('usuarios.editar', uid=uid))
        if models.usuario_existe(d['identificacion'], excluir_id=uid):
            flash('Ya existe otro aprendiz con esa identificacion.', 'danger')
            return redirect(url_for('usuarios.editar', uid=uid))
        try:
            firma = _guardar_firma(request.form.get('firma_base64', ''), request.files.get('firma_imagen'), aprendiz.get('firma'))
            models.actualizar_usuario(
                uid, d['identificacion'], d['tipo'], d['nombres'], d['apellidos'],
                d['correo'], d['telefono'], d['direccion'], d['ficha_id'], firma, d['estado'])
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'usuario', uid,
                                 f"Aprendiz {d['nombres']} {d['apellidos']}", request.remote_addr)
            flash('Aprendiz actualizado correctamente.', 'success')
            return redirect(url_for('usuarios.index'))
        except ValueError as e:
            flash(str(e), 'danger')
        except MySQLError as e:
            current_app.logger.error('Error BD al actualizar aprendiz %s: %s', uid, e)
            flash('Error de base de datos al actualizar el aprendiz.', 'danger')
        except Exception as e:
            current_app.logger.exception('Error al actualizar aprendiz')
            flash('Ha ocurrido un error inesperado.', 'danger')
        return redirect(url_for('usuarios.editar', uid=uid))

    return render_template('usuarios/form.html', aprendiz=aprendiz,
                           fichas=models.listar_fichas())


@usuarios_bp.route('/eliminar/<int:uid>', methods=['POST'])
@login_required
@role_required('superadmin', 'admin')
def eliminar(uid):
    aprendiz = models.obtener_usuario(uid)
    if not aprendiz:
        flash('Aprendiz no encontrado.', 'warning')
        return redirect(url_for('usuarios.index'))
    try:
        if aprendiz.get('firma'):
            ruta = os.path.join(current_app.config['FIRMAS_FOLDER'], aprendiz['firma'])
            if os.path.exists(ruta):
                os.remove(ruta)
        models.eliminar_usuario(uid)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'ELIMINAR', 'usuario', uid,
                             f"Aprendiz {aprendiz['nombres']} {aprendiz['apellidos']}",
                             request.remote_addr)
        flash('Aprendiz eliminado.', 'success')
    except MySQLError as e:
        current_app.logger.error('Error eliminando aprendiz %s: %s', uid, e)
        flash('No se pudo eliminar el aprendiz.', 'danger')
    return redirect(url_for('usuarios.index'))


@usuarios_bp.route('/ver/<int:uid>')
@login_required
def ver(uid):
    aprendiz = models.obtener_usuario(uid)
    if not aprendiz:
        flash('Aprendiz no encontrado.', 'warning')
        return redirect(url_for('usuarios.index'))
    return render_template('usuarios/ver.html', aprendiz=aprendiz)
