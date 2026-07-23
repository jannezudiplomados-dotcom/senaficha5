from functools import wraps
from flask import session, redirect, url_for, abort, request
import models

def acudiente_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('admin_rol') != 'acudiente':
            abort(403)
        return f(*args, **kwargs)
    return wrapper

def verificar_pertenencia(usuario_id: int, aprendiz_id: int) -> bool:
    """Verifica si el acudiente (usuario_id) tiene acceso al aprendiz (aprendiz_id)."""
    # usuario_id corresponds to admin.id, aprendiz_id corresponds to usuarios.id
    query = """
        SELECT 1 FROM acudiente_aprendiz
        WHERE usuario_id = %s AND aprendiz_id = %s AND estado = 'activo'
        LIMIT 1
    """
    conn = models.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (usuario_id, aprendiz_id))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def enmascarar_documento(num: str) -> str:
    """Enmascara un número de documento, ej: 10245*****53"""
    if not num:
        return ""
    num_str = str(num)
    if len(num_str) <= 4:
        return num_str
    return f"{num_str[:5]}{'*' * (len(num_str)-7)}{num_str[-2:]}"

WHITELIST_ACUDIENTE = ('acudiente.', 'acudiente_api.', 'auth.logout', 'auth.login', 'static')
