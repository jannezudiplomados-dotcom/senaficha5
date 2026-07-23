from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from mysql.connector import Error as MySQLError
import models
from routes.auth import login_required, role_required
import os

justificaciones_bp = Blueprint('justificaciones', __name__)

@justificaciones_bp.route('/')
@login_required
@role_required('superadmin', 'admin', 'instructor')
def index():
    justificaciones = models.obtener_justificaciones_admin()
    return render_template('justificaciones/index.html', justificaciones=justificaciones)

@justificaciones_bp.route('/estado/<int:jid>', methods=['POST'])
@login_required
@role_required('superadmin', 'admin', 'instructor')
def cambiar_estado(jid):
    estado = request.form.get('estado')
    comentario = request.form.get('comentario_revision', '').strip()
    
    if estado not in ['aprobada', 'rechazada']:
        flash('Estado no válido.', 'danger')
        return redirect(url_for('justificaciones.index'))
        
    try:
        models.actualizar_estado_justificacion(jid, estado, session.get('admin_id'), comentario)
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'EDITAR', 'justificaciones', jid, estado, request.remote_addr)
        flash(f'Justificación {estado} correctamente.', 'success')
    except MySQLError as e:
        current_app.logger.error('Error actualizando justificacion %s: %s', jid, e)
        flash('Ocurrió un error al actualizar la justificación.', 'danger')
        
    return redirect(url_for('justificaciones.index'))
