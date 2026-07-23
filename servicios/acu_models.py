import models
from werkzeug.security import generate_password_hash

def listar_aprendices_de_acudiente(usuario_id: int):
    """Retorna la lista de aprendices activos vinculados al acudiente."""
    query = """
        SELECT *
        FROM v_acudiente_aprendices_activos
        WHERE usuario_id = %s
    """
    return models.query(query, (usuario_id,))

def obtener_resumen_academico(aprendiz_id: int, mes=None):
    """
    Trae:
    - Total de fallas (estado != 'A' ni 'LIC')
    - Promedio de notas (Placeholder)
    - Observaciones recientes (desde asistencias u otras tablas)
    """
    resumen = {
        'total_fallas': 0,
        'promedio_notas': 'N/A', # Placeholder, no hay tabla de notas
        'observaciones': []
    }
    
    # Contar fallas (Inasistencia, Evasión, Retardo que no sean A, LIC, INC)
    # Estados de asistencia: 'A','CE','SE','INC','LIC','CLM','SFF','RET'
    # Fallas son típicamente SE, CE, SFF, RET
    query_fallas = """
        SELECT COUNT(*) as total 
        FROM asistencias 
        WHERE aprendiz_id = %s 
          AND estado NOT IN ('A', 'LIC', 'INC')
    """
    params = [aprendiz_id]
    if mes:
        query_fallas += " AND DATE_FORMAT(fecha, '%Y-%m') = %s"
        params.append(mes)
        
    row_fallas = models.query(query_fallas, tuple(params), fetchone=True)
    if row_fallas:
        resumen['total_fallas'] = row_fallas['total']
        
    # Observaciones recientes (últimas 3 asistencias con observación no vacía)
    query_obs = """
        SELECT fecha, estado, observacion 
        FROM asistencias 
        WHERE aprendiz_id = %s 
          AND observacion IS NOT NULL 
          AND TRIM(observacion) != ''
    """
    params_obs = [aprendiz_id]
    if mes:
        query_obs += " AND DATE_FORMAT(fecha, '%Y-%m') = %s"
        params_obs.append(mes)
        
    query_obs += " ORDER BY fecha DESC LIMIT 5"
    resumen['observaciones'] = models.query(query_obs, tuple(params_obs))
    
    return resumen

def obtener_asistencias(aprendiz_id: int, mes=None):
    """Lista de asistencias del aprendiz, filtrado por mes (YYYY-MM)."""
    query = """
        SELECT id, fecha, estado, observacion
        FROM asistencias
        WHERE aprendiz_id = %s
    """
    params = [aprendiz_id]
    if mes:
        query += " AND DATE_FORMAT(fecha, '%Y-%m') = %s"
        params.append(mes)
        
    query += " ORDER BY fecha DESC"
    return models.query(query, tuple(params))

def registrar_justificacion(usuario_id: int, aprendiz_id: int, fecha_falla: str, motivo: str, archivo_ruta: str = None):
    """Registra una justificación de inasistencia por parte del acudiente."""
    query = """
        INSERT INTO acudiente_justificaciones 
        (usuario_id, aprendiz_id, fecha_inasistencia, comentario, archivo_ruta, estado)
        VALUES (%s, %s, %s, %s, %s, 'pendiente')
    """
    models.execute(query, (usuario_id, aprendiz_id, fecha_falla, motivo, archivo_ruta or ''))

def cambiar_password_acudiente(usuario_id: int, nueva_password: str):
    """Cambia la contraseña y desmarca el flag de requiere_cambio_password en admin."""
    pw_hash = generate_password_hash(nueva_password)
    query = """
        UPDATE admin 
        SET password_hash = %s, requiere_cambio_password = 0 
        WHERE id = %s
    """
    models.execute(query, (pw_hash, usuario_id))
