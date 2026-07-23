from flask import Blueprint, jsonify, request, session
from functools import wraps

import models
from servicios import bam_models

bp = Blueprint('bitacoras_art_media_api', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/programas', methods=['GET'])
@login_required
def get_programas():
    # En este modulo, queremos los programas activos (que tienen fichas, etc)
    programas = models.listar_programas()
    return jsonify(programas)

@bp.route('/fichas', methods=['GET'])
@login_required
def get_fichas():
    programa_id = request.args.get('programa_id')
    if not programa_id:
        return jsonify([])
    fichas = models.fichas_por_programa(programa_id)
    return jsonify(fichas)

@bp.route('/plantillas', methods=['GET'])
@login_required
def get_plantillas():
    tipo = request.args.get('tipo', 'grupal')
    activa = int(request.args.get('activa', 1))
    plantillas = bam_models.obtener_plantillas_por_tipo(tipo=tipo, activa=activa)
    return jsonify(plantillas)

@bp.route('/aprendices', methods=['GET'])
@login_required
def get_aprendices():
    ficha_id = request.args.get('ficha_id')
    if not ficha_id:
        return jsonify([])
    aprendices = models.usuarios_por_ficha(ficha_id)
    return jsonify(aprendices)

@bp.route('/aprendiz/<int:id>', methods=['GET'])
@login_required
def get_aprendiz(id):
    aprendiz = models.obtener_usuario(id)
    if not aprendiz:
        return jsonify({'error': 'No encontrado'}), 404
    
    # Extraer los datos requeridos para el autocompletado
    data = {
        'id': aprendiz.get('id'),
        'nombres': aprendiz.get('nombres'),
        'apellidos': aprendiz.get('apellidos'),
        'tipo_documento': aprendiz.get('tipo_documento'),
        'identificacion': aprendiz.get('identificacion'),
        'telefono': aprendiz.get('telefono'),
        'correo_institucional': aprendiz.get('correo_institucional'),
        'correo_personal': aprendiz.get('correo'),
        'direccion': aprendiz.get('direccion'),
        'url_firma_png': aprendiz.get('firma') # Asumiendo que es el nombre del archivo de la firma en DB
    }
    return jsonify(data)

@bp.route('/generar', methods=['POST'])
@login_required
def generar():
    from flask import current_app
    import os
    import time
    from servicios import bam_writer, bam_pdf
    import models

    try:
        # Extraer datos principales
        form = request.form
        
        # 1. Crear el registro base de la bitácora
        bitacora_data = {
            'plantilla_id': form.get('plantilla_id'),
            'ficha_id': form.get('ficha_id'),
            'programa_id': form.get('programa_id'),
            'numero_bitacora': form.get('numero_bitacora'),
            'periodo_desde': form.get('periodo_desde'),
            'periodo_hasta': form.get('periodo_hasta'),
            'modalidad_formacion': form.get('modalidad_formacion'),
            'modalidad_ejecucion': form.get('modalidad_ejecucion'),
            'alternativa_etapa': form.get('alternativa_etapa'),
            'entidad_nombre': form.get('entidad_nombre'),
            'entidad_nit': form.get('entidad_nit'),
            'entidad_direccion': form.get('entidad_direccion'),
            'jefe_nombre': form.get('jefe_nombre'),
            'jefe_cargo': form.get('jefe_cargo'),
            'jefe_telefono': form.get('jefe_telefono'),
            'jefe_correo': form.get('jefe_correo'),
            'seguimiento_nombre': '',
            'seguimiento_correo': '',
            'fecha_entrega': form.get('fecha_entrega'),
            'estado': 'borrador',
            'creado_por': session.get('admin_id')
        }
        
        bitacora_id = bam_models.crear_bitacora(bitacora_data)
        
        # 2. Agregar actividades
        descripciones = form.getlist('act_desc[]')
        competencias = form.getlist('act_comp[]')
        finicios = form.getlist('act_fini[]')
        ffines = form.getlist('act_ffin[]')
        evidencias = form.getlist('act_evid[]')
        observaciones = form.getlist('act_obs[]')
        
        actividades_dict_list = []
        for i, desc in enumerate(descripciones):
            if desc.strip():
                bam_models.agregar_actividad_bitacora(
                    bitacora_id, i+1, desc, competencias[i], finicios[i], ffines[i], evidencias[i], observaciones[i]
                )
                actividades_dict_list.append({
                    "descripcion": desc,
                    "competencias": competencias[i],
                    "fecha_inicio": finicios[i],
                    "fecha_fin": ffines[i],
                    "evidencia": evidencias[i],
                    "observaciones": observaciones[i]
                })

        # 3. Agregar aprendices y construir info para bam_writer
        aprendices_ids = form.getlist('aprendices[]')
        arl_afil = form.getlist('arl_afil[]')
        arl_riesgo = form.getlist('arl_riesgo[]')
        arl_corr = form.getlist('arl_corr[]')
        arl_epp = form.getlist('arl_epp[]')
        
        aprendices_dict_list = []
        for i, aid in enumerate(aprendices_ids):
            if aid:
                bam_models.agregar_aprendiz_bitacora(
                    bitacora_id, aid, i+1, arl_afil[i], arl_riesgo[i], arl_corr[i], arl_epp[i]
                )
                # Cargar info completa del aprendiz
                u = models.obtener_usuario(aid)
                aprendiz_dict = {
                    "nombres": u.get('nombres', ''),
                    "apellidos": u.get('apellidos', ''),
                    "tipo_documento": u.get('tipo_documento', ''),
                    "identificacion": u.get('identificacion', ''),
                    "telefono": u.get('telefono', ''),
                    "correo_institucional": u.get('correo_institucional', ''),
                    "correo_personal": u.get('correo', ''),
                    "direccion": u.get('direccion', ''),
                    "arl_afiliado": arl_afil[i],
                    "arl_nivel_riesgo": int(arl_riesgo[i]),
                    "arl_corresponde": arl_corr[i],
                    "arl_epp": arl_epp[i]
                }
                
                # Firma del aprendiz
                if u.get('firma'):
                    firma_path = os.path.join(current_app.config['FIRMAS_FOLDER'], u['firma'])
                    if os.path.exists(firma_path):
                        aprendiz_dict['firma_path'] = firma_path
                    else:
                        aprendiz_dict['firma_path'] = None
                else:
                    aprendiz_dict['firma_path'] = None
                    
                aprendices_dict_list.append(aprendiz_dict)

        # 4. Construir diccionario de datos para bam_writer
        ficha_db = models.obtener_ficha(form.get('ficha_id'))
        prog_db = models.query('SELECT nombre FROM programas WHERE id=%s', (form.get('programa_id'),), fetchone=True)
        plantilla = bam_models.obtener_plantilla(form.get('plantilla_id'))
        
        template_path = os.path.join(current_app.config['BASE_DIR'], plantilla['archivo_ruta'])
        
        # Firma coformador (instructor)
        admin = models.obtener_admin(session.get('admin_id'))
        firma_coformador = None
        if admin and admin.get('firma'):
            f_path = os.path.join(current_app.config['FIRMAS_FOLDER'], admin['firma'])
            if os.path.exists(f_path):
                firma_coformador = f_path

        data_writer = {
            "numero_bitacora": form.get('numero_bitacora'),
            "periodo_desde": form.get('periodo_desde'),
            "periodo_hasta": form.get('periodo_hasta'),
            "aprendices": aprendices_dict_list,
            "ficha_numero": ficha_db['numero'] if ficha_db else '',
            "modalidad_formacion": form.get('modalidad_formacion'),
            "programa_nombre": prog_db['nombre'] if prog_db else '',
            "modalidad_ejecucion": form.get('modalidad_ejecucion'),
            "entidad_nombre": form.get('entidad_nombre'),
            "entidad_nit": form.get('entidad_nit'),
            "entidad_direccion": form.get('entidad_direccion'),
            "jefe_nombre": form.get('jefe_nombre'),
            "jefe_cargo": form.get('jefe_cargo'),
            "jefe_telefono": form.get('jefe_telefono'),
            "jefe_correo": form.get('jefe_correo'),
            "seguimiento_nombre": "",
            "seguimiento_correo": "",
            "alternativa_etapa": form.get('alternativa_etapa'),
            "actividades": actividades_dict_list,
            "fecha_entrega": form.get('fecha_entrega'),
            "firma_ente_coformador_path": firma_coformador
        }

        # 5. Generar Excel
        out_excel = bam_writer.generar_excel_bitacora(template_path, data_writer)
        
        # 6. Generar PDF
        out_pdf = bam_pdf.convertir_excel_a_pdf(out_excel)
        
        # 7. Actualizar estado y ruta PDF en BD
        pdf_rel_path = f"generados/{os.path.basename(out_pdf)}"
        models.execute('UPDATE bam_bitacoras SET estado=%s, pdf_ruta=%s WHERE id=%s', 
                       ('generada', pdf_rel_path, bitacora_id))
        
        # Limpiar excel temporal si se desea
        # if os.path.exists(out_excel):
        #     os.remove(out_excel)

        return jsonify({'status': 'success', 'message': 'Bitácora generada exitosamente y PDF creado.'})

    except Exception as e:
        current_app.logger.error(f"Error generando bitacora: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

