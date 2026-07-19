import os
import re
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


def _guardar_foto(foto_base64, foto_file, foto_actual=None):
    """Guarda la foto retornando un string Base64 para almacenar en la BD."""
    if foto_file and foto_file.filename:
        foto_file.seek(0, os.SEEK_END)
        size = foto_file.tell()
        foto_file.seek(0)
        if size > 5 * 1024 * 1024:
            raise ValueError("La foto supera el tamaño máximo de 5MB.")
        
        datos = foto_file.read()
        
        # Comprimir usando Pillow para asegurar tamaño mínimo en la base de datos
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(datos))
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        max_width = 400
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        out_io = io.BytesIO()
        img.save(out_io, format='JPEG', quality=70)
        encoded = base64.b64encode(out_io.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"
        
    elif foto_base64:
        # Ya viene desde la cámara en formato data URI
        return foto_base64
    
    return foto_actual



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
        'correo_institucional': request.form.get('correo_institucional', '').strip() or None,
        'telefono': request.form.get('telefono', '').strip() or None,
        'direccion': request.form.get('direccion', '').strip() or None,
        'portafolio_url': request.form.get('portafolio_url', '').strip() or None,
        'ficha_id': ficha_id,
        'estado': request.form.get('estado', 'Activo'),
    }


def _form_acudiente():
    """Extrae datos del acudiente del formulario.
    Retorna dict o None si no se diligencio el bloque."""
    nombres = request.form.get('acudiente_nombres', '').strip()
    if not nombres:
        return None
    return {
        'identificacion': request.form.get('acudiente_identificacion', '').strip() or None,
        'nombres_completos': nombres,
        'correo': request.form.get('acudiente_correo', '').strip() or None,
        'telefono': request.form.get('acudiente_telefono', '').strip() or None,
        'parentesco': request.form.get('acudiente_parentesco', '').strip() or None,
    }


def _validar_campos_nuevos(d, acud):
    """Valida correo institucional, portafolio y datos del acudiente.
    Retorna lista de mensajes de error (vacía si todo OK)."""
    errores = []

    # Correo institucional: validación de formato general
    ci = d.get('correo_institucional')
    if ci:
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', ci):
            errores.append('El correo institucional no tiene un formato válido.')

    # Portafolio URL: si viene, debe ser http(s)://
    pu = d.get('portafolio_url')
    if pu:
        if not re.match(r'^https?://', pu, re.IGNORECASE):
            errores.append('El enlace del portafolio debe comenzar con http:// o https://')

    # Validaciones del acudiente
    if acud:
        ac = acud.get('correo')
        if ac and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', ac):
            errores.append('El correo del acudiente no tiene un formato válido.')
        at = acud.get('telefono')
        if at and not re.match(r'^[\d\s\+\-]+$', at):
            errores.append('El teléfono del acudiente solo puede contener dígitos, espacios, + y -.')

    return errores


def _guardar_acudiente(acud):
    """Upsert del acudiente y retorna su id."""
    if not acud:
        return None
    try:
        acudiente_id = models.upsert_acudiente(
            acud['identificacion'], acud['nombres_completos'],
            acud['correo'], acud['telefono'], acud['parentesco'])
        return acudiente_id
    except MySQLError as e:
        current_app.logger.error('Error al guardar acudiente: %s', e)
        raise


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
        acud = _form_acudiente()

        if not d['identificacion'] or not d['nombres'] or not d['apellidos']:
            flash('Identificacion, nombres y apellidos son obligatorios.', 'danger')
            return redirect(url_for('usuarios.nuevo'))
        if models.usuario_existe(d['identificacion']):
            flash('Ya existe un aprendiz con esa identificacion.', 'danger')
            return redirect(url_for('usuarios.nuevo'))

        # Validar campos nuevos
        errores_val = _validar_campos_nuevos(d, acud)
        if errores_val:
            for msg in errores_val:
                flash(msg, 'danger')
            return redirect(url_for('usuarios.nuevo'))

        try:
            firma = _guardar_firma(request.form.get('firma_base64', ''), request.files.get('firma_imagen'))
            foto = _guardar_foto(request.form.get('foto_base64', ''), request.files.get('foto_imagen'))

            # Guardar acudiente (upsert) si hay datos
            acudiente_id = _guardar_acudiente(acud)

            uid = models.crear_usuario(
                d['identificacion'], d['tipo'], d['nombres'], d['apellidos'],
                d['correo'], d['telefono'], d['direccion'], d['ficha_id'], firma, d['estado'],
                correo_institucional=d['correo_institucional'],
                portafolio_url=d['portafolio_url'],
                acudiente_id=acudiente_id, foto=foto)

            # Auditoría
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'CREAR', 'usuario', uid,
                                 f"Aprendiz {d['nombres']} {d['apellidos']}", request.remote_addr)
            if acud and acudiente_id:
                models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                     'UPSERT', 'acudientes', acudiente_id,
                                     f"Acudiente {acud['nombres_completos']} (aprendiz id={uid})",
                                     request.remote_addr)

            flash('Aprendiz creado correctamente.', 'success')
            return redirect(url_for('usuarios.index'))
        except ValueError as e:
            flash(str(e), 'danger')
        except MySQLError as e:
            # Detectar duplicado de portafolio_url
            if e.errno == 1062 and 'portafolio_url' in str(e):
                flash('Este enlace de portafolio ya está registrado por otro aprendiz.', 'danger')
            else:
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
        acud = _form_acudiente()

        if not d['identificacion'] or not d['nombres'] or not d['apellidos']:
            flash('Identificacion, nombres y apellidos son obligatorios.', 'danger')
            return redirect(url_for('usuarios.editar', uid=uid))
        if models.usuario_existe(d['identificacion'], excluir_id=uid):
            flash('Ya existe otro aprendiz con esa identificacion.', 'danger')
            return redirect(url_for('usuarios.editar', uid=uid))

        # Validar campos nuevos
        errores_val = _validar_campos_nuevos(d, acud)
        if errores_val:
            for msg in errores_val:
                flash(msg, 'danger')
            return redirect(url_for('usuarios.editar', uid=uid))

        try:
            firma = _guardar_firma(request.form.get('firma_base64', ''), request.files.get('firma_imagen'), aprendiz.get('firma'))
            foto = _guardar_foto(request.form.get('foto_base64', ''), request.files.get('foto_imagen'), aprendiz.get('foto'))

            # Guardar acudiente (upsert) si hay datos
            acudiente_id = _guardar_acudiente(acud)
            # Si no se diligenciaron datos de acudiente, mantener el actual
            if acudiente_id is None:
                acudiente_id = aprendiz.get('acudiente_id')

            models.actualizar_usuario(
                uid, d['identificacion'], d['tipo'], d['nombres'], d['apellidos'],
                d['correo'], d['telefono'], d['direccion'], d['ficha_id'], firma, d['estado'],
                correo_institucional=d['correo_institucional'],
                portafolio_url=d['portafolio_url'],
                acudiente_id=acudiente_id, foto=foto)

            # Auditoría
            models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                 'EDITAR', 'usuario', uid,
                                 f"Aprendiz {d['nombres']} {d['apellidos']}", request.remote_addr)
            if acud and acudiente_id:
                models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                                     'UPSERT', 'acudientes', acudiente_id,
                                     f"Acudiente {acud['nombres_completos']} (aprendiz id={uid})",
                                     request.remote_addr)

            flash('Aprendiz actualizado correctamente.', 'success')
            return redirect(url_for('usuarios.index'))
        except ValueError as e:
            flash(str(e), 'danger')
        except MySQLError as e:
            if e.errno == 1062 and 'portafolio_url' in str(e):
                flash('Este enlace de portafolio ya está registrado por otro aprendiz.', 'danger')
            else:
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
        if aprendiz.get('foto') and not aprendiz['foto'].startswith('data:'):
            ruta_foto = os.path.join(current_app.config['FOTOS_FOLDER'], aprendiz['foto'])
            if os.path.exists(ruta_foto):
                os.remove(ruta_foto)
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
