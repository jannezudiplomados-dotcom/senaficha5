import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, abort
from servicios.acu_auth import acudiente_required, verificar_pertenencia, enmascarar_documento
import servicios.acu_models as acu_models

bp = Blueprint('acudiente', __name__, template_folder='templates')

@bp.before_request
@acudiente_required
def before_request():
    pass

@bp.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com;"
    return response

@bp.route('/portal')
def portal():
    # Check if password change is required
    if session.get('requiere_cambio_password'):
        flash("Debes cambiar tu contraseña antes de continuar.", "warning")
        return redirect(url_for('acudiente.cambiar_password'))
        
    usuario_id = session.get('admin_id')
    aprendices = acu_models.listar_aprendices_de_acudiente(usuario_id)
    
    if len(aprendices) == 1:
        return redirect(url_for('acudiente.informe_aprendiz', id=aprendices[0]['aprendiz_id']))
        
    # Enmascarar documentos para la vista de tarjetas
    for a in aprendices:
        a['numero_documento_enmascarado'] = enmascarar_documento(a['numero_documento'])
        
    return render_template('acudiente/portal.html', aprendices=aprendices)

@bp.route('/aprendiz/<int:id>')
def informe_aprendiz(id):
    if session.get('requiere_cambio_password'):
        return redirect(url_for('acudiente.cambiar_password'))
        
    usuario_id = session.get('admin_id')
    if not verificar_pertenencia(usuario_id, id):
        abort(404)
        
    mes = request.args.get('mes')
    if not mes:
        mes = datetime.date.today().strftime('%Y-%m')
        
    resumen = acu_models.obtener_resumen_academico(id, mes)
    asistencias = acu_models.obtener_asistencias(id, mes)
    
    # Obtener el nombre del aprendiz (haciendo uso de la lista)
    aprendices = acu_models.listar_aprendices_de_acudiente(usuario_id)
    aprendiz_info = next((a for a in aprendices if a['aprendiz_id'] == id), None)
    
    return render_template('acudiente/informe_aprendiz.html', 
                           aprendiz=aprendiz_info, 
                           mes_actual=mes, 
                           resumen=resumen, 
                           asistencias=asistencias)

@bp.route('/api/aprendiz/<int:id>/justificar', methods=['POST'])
def api_justificar(id):
    usuario_id = session.get('admin_id')
    if not verificar_pertenencia(usuario_id, id):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para este aprendiz.'}), 404
        
    data = request.json
    if not data:
        data = request.form
        
    fecha_falla = data.get('fecha')
    motivo = data.get('motivo')
    
    if not fecha_falla or not motivo:
        return jsonify({'status': 'error', 'message': 'Faltan datos obligatorios.'}), 400
        
    # No manejamos subida de archivos en este endpoint de momento a menos que se envíe via multipart/form-data
    archivo_ruta = None
    
    try:
        acu_models.registrar_justificacion(usuario_id, id, fecha_falla, motivo, archivo_ruta)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/password', methods=['GET', 'POST'])
def cambiar_password():
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')
        confirmar_password = request.form.get('confirmar_password')
        
        if not nueva_password or len(nueva_password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for('acudiente.cambiar_password'))
            
        if nueva_password != confirmar_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('acudiente.cambiar_password'))
            
        usuario_id = session.get('admin_id')
        acu_models.cambiar_password_acudiente(usuario_id, nueva_password)
        
        session.pop('requiere_cambio_password', None)
        flash("Contraseña actualizada con éxito.", "success")
        return redirect(url_for('acudiente.portal'))
        
    return render_template('acudiente/password.html')
