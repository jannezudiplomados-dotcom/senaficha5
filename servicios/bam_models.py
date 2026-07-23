import models

# ---------- CONFIGURACIÓN ----------
def obtener_config():
    rows = models.query('SELECT clave, valor FROM bam_config')
    return {row['clave']: row['valor'] for row in rows}

def actualizar_config(config_dict):
    for clave, valor in config_dict.items():
        models.execute('UPDATE bam_config SET valor=%s WHERE clave=%s', (valor, clave))

# ---------- PLANTILLAS ----------
def listar_plantillas():
    return models.query('SELECT * FROM bam_plantillas ORDER BY creado_en DESC')

def obtener_plantilla(pid):
    return models.query('SELECT * FROM bam_plantillas WHERE id=%s', (pid,), fetchone=True)

def obtener_plantillas_por_tipo(tipo='grupal', activa=1):
    return models.query('SELECT * FROM bam_plantillas WHERE tipo_generacion=%s AND activa=%s ORDER BY creado_en DESC', (tipo, activa))

def crear_plantilla(nombre, archivo_ruta, hoja_objetivo='Formato Bitácora Art. Media', tipo='grupal', max_aprendices=5, creado_por=None):
    return models.execute('''INSERT INTO bam_plantillas
        (nombre, archivo_ruta, hoja_objetivo, tipo_generacion, max_aprendices, creado_por)
        VALUES (%s, %s, %s, %s, %s, %s)''',
        (nombre, archivo_ruta, hoja_objetivo, tipo, max_aprendices, creado_por))

def desactivar_plantilla(pid):
    models.execute('UPDATE bam_plantillas SET activa=0 WHERE id=%s', (pid,))

def eliminar_plantilla(pid):
    models.execute('DELETE FROM bam_plantillas WHERE id=%s', (pid,))

# ---------- BITÁCORAS ----------
def listar_bitacoras():
    return models.query('''SELECT b.*, p.nombre AS plantilla_nombre, f.numero AS ficha_numero, pr.nombre AS programa_nombre
        FROM bam_bitacoras b
        JOIN bam_plantillas p ON b.plantilla_id = p.id
        JOIN fichas f ON b.ficha_id = f.id
        JOIN programas pr ON b.programa_id = pr.id
        ORDER BY b.creado_en DESC''')

def obtener_bitacora(bid):
    return models.query('SELECT * FROM bam_bitacoras WHERE id=%s', (bid,), fetchone=True)

def crear_bitacora(data):
    sql = '''INSERT INTO bam_bitacoras
        (plantilla_id, ficha_id, programa_id, numero_bitacora, periodo_desde, periodo_hasta,
         modalidad_formacion, modalidad_ejecucion, alternativa_etapa, entidad_nombre, entidad_nit,
         entidad_direccion, jefe_nombre, jefe_cargo, jefe_telefono, jefe_correo,
         seguimiento_nombre, seguimiento_correo, fecha_entrega, estado, creado_por)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    return models.execute(sql, (
        data['plantilla_id'], data['ficha_id'], data['programa_id'], data.get('numero_bitacora'),
        data.get('periodo_desde'), data.get('periodo_hasta'), data.get('modalidad_formacion'),
        data.get('modalidad_ejecucion'), data.get('alternativa_etapa'), data.get('entidad_nombre'),
        data.get('entidad_nit'), data.get('entidad_direccion'), data.get('jefe_nombre'),
        data.get('jefe_cargo'), data.get('jefe_telefono'), data.get('jefe_correo'),
        data.get('seguimiento_nombre'), data.get('seguimiento_correo'), data.get('fecha_entrega'),
        data.get('estado', 'borrador'), data.get('creado_por')
    ))

def actualizar_bitacora(bid, data):
    sql = '''UPDATE bam_bitacoras SET
        numero_bitacora=%s, periodo_desde=%s, periodo_hasta=%s, modalidad_formacion=%s,
        modalidad_ejecucion=%s, alternativa_etapa=%s, entidad_nombre=%s, entidad_nit=%s,
        entidad_direccion=%s, jefe_nombre=%s, jefe_cargo=%s, jefe_telefono=%s, jefe_correo=%s,
        seguimiento_nombre=%s, seguimiento_correo=%s, fecha_entrega=%s, estado=%s, pdf_ruta=%s
        WHERE id=%s'''
    models.execute(sql, (
        data.get('numero_bitacora'), data.get('periodo_desde'), data.get('periodo_hasta'),
        data.get('modalidad_formacion'), data.get('modalidad_ejecucion'), data.get('alternativa_etapa'),
        data.get('entidad_nombre'), data.get('entidad_nit'), data.get('entidad_direccion'),
        data.get('jefe_nombre'), data.get('jefe_cargo'), data.get('jefe_telefono'), data.get('jefe_correo'),
        data.get('seguimiento_nombre'), data.get('seguimiento_correo'), data.get('fecha_entrega'),
        data.get('estado'), data.get('pdf_ruta'), bid
    ))

def eliminar_bitacora(bid):
    models.execute('DELETE FROM bam_bitacoras WHERE id=%s', (bid,))

# ---------- APRENDICES POR BITÁCORA ----------
def agregar_aprendiz_bitacora(bitacora_id, aprendiz_id, orden, arl_afiliado='SI', arl_nivel=1, arl_corresponde='SI', arl_epp='SI'):
    return models.execute('''INSERT INTO bam_bitacora_aprendices
        (bitacora_id, aprendiz_id, orden, arl_afiliado, arl_nivel_riesgo, arl_corresponde, arl_epp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (bitacora_id, aprendiz_id, orden, arl_afiliado, arl_nivel, arl_corresponde, arl_epp))

def obtener_aprendices_bitacora(bitacora_id):
    return models.query('''SELECT ba.*, u.nombres, u.apellidos, u.identificacion, u.tipo_documento,
        u.telefono, u.correo, u.correo_institucional, u.direccion, u.firma
        FROM bam_bitacora_aprendices ba
        JOIN usuarios u ON ba.aprendiz_id = u.id
        WHERE ba.bitacora_id = %s ORDER BY ba.orden''', (bitacora_id,))

# ---------- ACTIVIDADES POR BITÁCORA ----------
def agregar_actividad_bitacora(bitacora_id, orden, descripcion, competencias, fecha_inicio, fecha_fin, evidencia, observaciones):
    return models.execute('''INSERT INTO bam_bitacora_actividades
        (bitacora_id, orden, descripcion, competencias, fecha_inicio, fecha_fin, evidencia, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
        (bitacora_id, orden, descripcion, competencias, fecha_inicio, fecha_fin, evidencia, observaciones))

def obtener_actividades_bitacora(bitacora_id):
    return models.query('SELECT * FROM bam_bitacora_actividades WHERE bitacora_id = %s ORDER BY orden', (bitacora_id,))
