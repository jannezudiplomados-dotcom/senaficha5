import logging
import mysql.connector
from mysql.connector import pooling
from config import Config

_pool = None


def init_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name='sena_pool', pool_size=5, pool_reset_session=True,
            host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
            password=Config.DB_PASSWORD, database=Config.DB_NAME, charset='utf8mb4')
    return _pool


def get_connection():
    if _pool is None:
        init_pool()
    return _pool.get_connection()


def query(sql, params=None, fetchone=False):
    last_err = None
    for attempt in range(3):
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(sql, params or ())
                return cur.fetchone() if fetchone else cur.fetchall()
            finally:
                cur.close()
        except mysql.connector.errors.OperationalError as e:
            last_err = e
            logging.getLogger(__name__).warning(
                'MySQL OperationalError (intento %d/3): %s', attempt + 1, e)
            if attempt < 2:
                continue
            raise
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    raise last_err  # pragma: no cover


def execute(sql, params=None):
    last_err = None
    for attempt in range(3):
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(sql, params or ())
                conn.commit()
                return cur.lastrowid
            finally:
                cur.close()
        except mysql.connector.errors.OperationalError as e:
            last_err = e
            logging.getLogger(__name__).warning(
                'MySQL OperationalError en execute (intento %d/3): %s', attempt + 1, e)
            if attempt < 2:
                continue
            raise
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    raise last_err  # pragma: no cover


# ---------- PROGRAMAS ----------
def listar_programas():
    return query('SELECT * FROM programas ORDER BY nombre')

def contar_programas(search=None):
    if search:
        like = f'%{search}%'
        r = query('SELECT COUNT(*) AS total FROM programas WHERE nombre LIKE %s OR codigo LIKE %s',
                  (like, like), fetchone=True)
    else:
        r = query('SELECT COUNT(*) AS total FROM programas', fetchone=True)
    return r['total']

def obtener_programas_paginados(page=1, per_page=10, search=None):
    offset = (page - 1) * per_page
    if search:
        like = f'%{search}%'
        return query('SELECT * FROM programas WHERE nombre LIKE %s OR codigo LIKE %s ORDER BY nombre LIMIT %s OFFSET %s',
                     (like, like, per_page, offset))
    return query('SELECT * FROM programas ORDER BY nombre LIMIT %s OFFSET %s', (per_page, offset))

def obtener_programa(pid):
    return query('SELECT * FROM programas WHERE id=%s', (pid,), fetchone=True)

def crear_programa(codigo, nombre, descripcion, duracion, fecha_inicio=None, fecha_fin=None):
    return execute('INSERT INTO programas (codigo,nombre,descripcion,duracion_meses,fecha_inicio,fecha_fin) '
                   'VALUES (%s,%s,%s,%s,%s,%s)', (codigo, nombre, descripcion, duracion, fecha_inicio, fecha_fin))

def actualizar_programa(pid, codigo, nombre, descripcion, duracion, fecha_inicio=None, fecha_fin=None):
    execute('UPDATE programas SET codigo=%s,nombre=%s,descripcion=%s,duracion_meses=%s,fecha_inicio=%s,fecha_fin=%s '
            'WHERE id=%s', (codigo, nombre, descripcion, duracion, fecha_inicio, fecha_fin, pid))

def eliminar_programa(pid):
    execute('DELETE FROM programas WHERE id=%s', (pid,))


# ---------- FICHAS ----------
def listar_fichas():
    return query('''SELECT f.*, p.nombre AS programa_nombre, c.nombre_colegio,
        (SELECT COUNT(*) FROM usuarios u WHERE u.ficha_id=f.id) AS total_aprendices
        FROM fichas f JOIN programas p ON f.programa_id=p.id 
        LEFT JOIN colegios c ON f.colegio_id = c.idcolegio
        ORDER BY f.numero''')

def contar_fichas(search=None):
    if search:
        like = f'%{search}%'
        r = query('''SELECT COUNT(*) AS total FROM fichas f
            JOIN programas p ON f.programa_id=p.id
            LEFT JOIN colegios c ON f.colegio_id = c.idcolegio
            WHERE f.numero LIKE %s OR p.nombre LIKE %s OR c.nombre_colegio LIKE %s''',
                  (like, like, like), fetchone=True)
    else:
        r = query('SELECT COUNT(*) AS total FROM fichas', fetchone=True)
    return r['total']

def obtener_fichas_paginadas(page=1, per_page=10, search=None):
    offset = (page - 1) * per_page
    if search:
        like = f'%{search}%'
        return query('''SELECT f.*, p.nombre AS programa_nombre, c.nombre_colegio,
            (SELECT COUNT(*) FROM usuarios u WHERE u.ficha_id=f.id) AS total_aprendices
            FROM fichas f JOIN programas p ON f.programa_id=p.id
            LEFT JOIN colegios c ON f.colegio_id = c.idcolegio
            WHERE f.numero LIKE %s OR p.nombre LIKE %s OR c.nombre_colegio LIKE %s
            ORDER BY f.numero LIMIT %s OFFSET %s''',
                     (like, like, like, per_page, offset))
    return query('''SELECT f.*, p.nombre AS programa_nombre, c.nombre_colegio,
        (SELECT COUNT(*) FROM usuarios u WHERE u.ficha_id=f.id) AS total_aprendices
        FROM fichas f JOIN programas p ON f.programa_id=p.id
        LEFT JOIN colegios c ON f.colegio_id = c.idcolegio
        ORDER BY f.numero LIMIT %s OFFSET %s''', (per_page, offset))

def fichas_por_programa(programa_id):
    return query('SELECT * FROM fichas WHERE programa_id=%s ORDER BY numero', (programa_id,))

def obtener_ficha(fid):
    return query('''SELECT f.*, p.nombre AS programa_nombre, p.codigo AS programa_codigo,
        p.fecha_inicio AS programa_fecha_inicio, p.fecha_fin AS programa_fecha_fin,
        c.nombre_colegio
        FROM fichas f JOIN programas p ON f.programa_id=p.id 
        LEFT JOIN colegios c ON f.colegio_id = c.idcolegio
        WHERE f.id=%s''', (fid,), fetchone=True)

def crear_ficha(numero, programa_id, colegio_id, jornada, fi, ff):
    return execute('INSERT INTO fichas (numero,programa_id,colegio_id,jornada,fecha_inicio,fecha_fin) '
                   'VALUES (%s,%s,%s,%s,%s,%s)', (numero, programa_id, colegio_id, jornada, fi, ff))

def actualizar_ficha(fid, numero, programa_id, colegio_id, jornada, fi, ff):
    execute('UPDATE fichas SET numero=%s,programa_id=%s,colegio_id=%s,jornada=%s,fecha_inicio=%s,fecha_fin=%s '
            'WHERE id=%s', (numero, programa_id, colegio_id, jornada, fi, ff, fid))

def eliminar_ficha(fid):
    execute('DELETE FROM fichas WHERE id=%s', (fid,))


# ---------- USUARIOS (aprendices) ----------
def usuario_existe(identificacion, excluir_id=None):
    if excluir_id:
        r = query('SELECT 1 FROM usuarios WHERE identificacion=%s AND id<>%s',
                  (identificacion, excluir_id), fetchone=True)
    else:
        r = query('SELECT 1 FROM usuarios WHERE identificacion=%s', (identificacion,), fetchone=True)
    return r is not None

def contar_usuarios(search=None):
    if search:
        like = f'%{search}%'
        r = query('''SELECT COUNT(*) AS total FROM usuarios u LEFT JOIN fichas f ON u.ficha_id=f.id
            WHERE u.nombres LIKE %s OR u.apellidos LIKE %s OR u.identificacion LIKE %s OR f.numero LIKE %s''',
            (like, like, like, like), fetchone=True)
    else:
        r = query('SELECT COUNT(*) AS total FROM usuarios', fetchone=True)
    return r['total']

def obtener_usuarios_paginados(page=1, per_page=10, search=None):
    offset = (page - 1) * per_page
    if search:
        like = f'%{search}%'
        return query('''SELECT u.*, f.numero AS ficha_numero, p.nombre AS programa_nombre
            FROM usuarios u LEFT JOIN fichas f ON u.ficha_id=f.id
            LEFT JOIN programas p ON f.programa_id=p.id
            WHERE u.nombres LIKE %s OR u.apellidos LIKE %s OR u.identificacion LIKE %s OR f.numero LIKE %s
            ORDER BY u.created_at DESC LIMIT %s OFFSET %s''',
            (like, like, like, like, per_page, offset))
    return query('''SELECT u.*, f.numero AS ficha_numero, p.nombre AS programa_nombre
        FROM usuarios u LEFT JOIN fichas f ON u.ficha_id=f.id
        LEFT JOIN programas p ON f.programa_id=p.id
        ORDER BY u.created_at DESC LIMIT %s OFFSET %s''', (per_page, offset))

def obtener_usuario(uid):
    return query('''SELECT u.*, f.programa_id, f.numero AS ficha_numero,
        f.fecha_inicio AS ficha_inicio, f.fecha_fin AS ficha_fin, p.nombre AS programa_nombre
        FROM usuarios u LEFT JOIN fichas f ON u.ficha_id=f.id
        LEFT JOIN programas p ON f.programa_id=p.id WHERE u.id=%s''', (uid,), fetchone=True)

def usuarios_por_ficha(ficha_id):
    return query('''SELECT u.*, f.numero AS ficha_numero, p.nombre AS programa_nombre
        FROM usuarios u JOIN fichas f ON u.ficha_id=f.id JOIN programas p ON f.programa_id=p.id
        WHERE u.ficha_id=%s ORDER BY u.apellidos, u.nombres''', (ficha_id,))

def crear_usuario(identificacion, tipo, nombres, apellidos, correo, telefono, direccion, ficha_id, firma, estado):
    return execute('''INSERT INTO usuarios
        (identificacion,tipo_documento,nombres,apellidos,correo,telefono,direccion,ficha_id,firma,estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (identificacion, tipo, nombres, apellidos, correo, telefono, direccion, ficha_id, firma, estado))

def actualizar_usuario(uid, identificacion, tipo, nombres, apellidos, correo, telefono, direccion, ficha_id, firma, estado):
    execute('''UPDATE usuarios SET identificacion=%s,tipo_documento=%s,nombres=%s,apellidos=%s,
        correo=%s,telefono=%s,direccion=%s,ficha_id=%s,firma=%s,estado=%s WHERE id=%s''',
        (identificacion, tipo, nombres, apellidos, correo, telefono, direccion, ficha_id, firma, estado, uid))

def eliminar_usuario(uid):
    execute('DELETE FROM usuarios WHERE id=%s', (uid,))


# ---------- ADMIN (multi-admin) ----------
def obtener_admin_por_username(username):
    return query('SELECT * FROM admin WHERE username=%s', (username,), fetchone=True)

def obtener_admin(aid):
    return query('SELECT * FROM admin WHERE id=%s', (aid,), fetchone=True)

def listar_admins():
    return query('SELECT a.id, a.username, a.nombre, a.rol, a.activo, a.created_at, p.nombre AS programa_nombre FROM admin a LEFT JOIN programas p ON a.programa_id = p.id ORDER BY a.created_at')

def crear_admin(username, password_hash, nombre, rol, programa_id=None):
    return execute('INSERT INTO admin (username,password_hash,nombre,rol,programa_id) VALUES (%s,%s,%s,%s,%s)',
                   (username, password_hash, nombre, rol, programa_id))

def actualizar_admin(aid, nombre, rol, activo, programa_id=None, password_hash=None):
    if password_hash:
        execute('UPDATE admin SET nombre=%s,rol=%s,activo=%s,programa_id=%s,password_hash=%s WHERE id=%s',
                (nombre, rol, activo, programa_id, password_hash, aid))
    else:
        execute('UPDATE admin SET nombre=%s,rol=%s,activo=%s,programa_id=%s WHERE id=%s', (nombre, rol, activo, programa_id, aid))

def eliminar_admin(aid):
    execute('DELETE FROM admin WHERE id=%s', (aid,))


# ---------- PLANTILLAS ----------
def listar_plantillas(programa_id=None):
    if programa_id:
        return query('SELECT pl.*, p.nombre AS programa_nombre FROM plantillas pl JOIN programas p ON pl.programa_id = p.id WHERE pl.programa_id = %s ORDER BY pl.created_at DESC', (programa_id,))
    return query('SELECT pl.*, p.nombre AS programa_nombre FROM plantillas pl LEFT JOIN programas p ON pl.programa_id = p.id ORDER BY pl.created_at DESC')

def contar_plantillas(programa_id=None):
    if programa_id:
        r = query('SELECT COUNT(*) AS total FROM plantillas WHERE programa_id = %s', (programa_id,), fetchone=True)
    else:
        r = query('SELECT COUNT(*) AS total FROM plantillas', fetchone=True)
    return r['total']

def obtener_plantillas_paginadas(page=1, per_page=5, programa_id=None):
    offset = (page - 1) * per_page
    if programa_id:
        return query('SELECT pl.*, p.nombre AS programa_nombre FROM plantillas pl JOIN programas p ON pl.programa_id = p.id WHERE pl.programa_id = %s ORDER BY pl.created_at DESC LIMIT %s OFFSET %s', (programa_id, per_page, offset))
    return query('SELECT pl.*, p.nombre AS programa_nombre FROM plantillas pl LEFT JOIN programas p ON pl.programa_id = p.id ORDER BY pl.created_at DESC LIMIT %s OFFSET %s', (per_page, offset))

def obtener_plantilla(pid):
    return query('SELECT pl.*, p.nombre AS programa_nombre FROM plantillas pl LEFT JOIN programas p ON pl.programa_id = p.id WHERE pl.id=%s', (pid,), fetchone=True)

def crear_plantilla(nombre, archivo, descripcion, programa_id, tipo_generacion='ambos'):
    return execute('INSERT INTO plantillas (nombre,archivo,descripcion,programa_id,tipo_generacion) VALUES (%s,%s,%s,%s,%s)',
                   (nombre, archivo, descripcion, programa_id, tipo_generacion))

def eliminar_plantilla(pid):
    execute('DELETE FROM plantillas WHERE id=%s', (pid,))


# ---------- LOG / AUDITORIA ----------
def registrar_log(admin_id, admin_username, accion, entidad, entidad_id=None, detalle=None, ip=None):
    try:
        execute('''INSERT INTO log_actividades
            (admin_id,admin_username,accion,entidad,entidad_id,detalle,ip)
            VALUES (%s,%s,%s,%s,%s,%s,%s)''',
            (admin_id, admin_username, accion, entidad, entidad_id, detalle, ip))
    except Exception as e:
        logging.getLogger(__name__).warning('Error registrando log de auditoria: %s', e)

def listar_logs(limite=100):
    return query('SELECT * FROM log_actividades ORDER BY created_at DESC LIMIT %s', (limite,))


# ---------- ESTADISTICAS ----------
def estadisticas(programa_id=None):
    cond_u = f" WHERE u.programa_id = {programa_id}" if programa_id else ""
    cond_f = f" WHERE programa_id = {programa_id}" if programa_id else ""
    cond_p = f" WHERE id = {programa_id}" if programa_id else ""
    cond_pl = f" WHERE programa_id = {programa_id}" if programa_id else ""
    
    total_u_q = f"SELECT COUNT(*) AS c FROM usuarios u LEFT JOIN fichas f ON u.ficha_id = f.id"
    if programa_id:
        total_u_q += f" WHERE f.programa_id = {programa_id}"
    else:
        total_u_q = "SELECT COUNT(*) AS c FROM usuarios"

    activos_u_q = f"SELECT COUNT(*) AS c FROM usuarios u LEFT JOIN fichas f ON u.ficha_id = f.id WHERE u.estado='Activo'"
    if programa_id:
        activos_u_q += f" AND f.programa_id = {programa_id}"

    return {
        'total_aprendices': query(total_u_q, fetchone=True)['c'],
        'total_fichas': query(f'SELECT COUNT(*) AS c FROM fichas{cond_f}', fetchone=True)['c'],
        'total_programas': query(f'SELECT COUNT(*) AS c FROM programas{cond_p}', fetchone=True)['c'],
        'total_plantillas': query(f'SELECT COUNT(*) AS c FROM plantillas{cond_pl}', fetchone=True)['c'],
        'total_colegios': query('SELECT COUNT(*) AS c FROM colegios', fetchone=True)['c'],
        'aprendices_activos': query(activos_u_q, fetchone=True)['c'],
    }

def aprendices_por_estado(programa_id=None):
    if programa_id:
        return query('''SELECT u.estado, COUNT(*) AS total FROM usuarios u 
                        LEFT JOIN fichas f ON u.ficha_id = f.id 
                        WHERE f.programa_id = %s GROUP BY u.estado ORDER BY u.estado''', (programa_id,))
    return query('SELECT estado, COUNT(*) AS total FROM usuarios GROUP BY estado ORDER BY estado')

def aprendices_por_programa(programa_id=None):
    cond = "WHERE p.id = %s" if programa_id else ""
    params = (programa_id,) if programa_id else ()
    return query(f'''SELECT p.nombre AS programa, COUNT(u.id) AS total
        FROM programas p
        LEFT JOIN fichas f ON f.programa_id = p.id
        LEFT JOIN usuarios u ON u.ficha_id = f.id
        {cond}
        GROUP BY p.id, p.nombre ORDER BY total DESC''', params)

def aprendices_por_ficha(programa_id=None):
    cond = "WHERE f.programa_id = %s" if programa_id else ""
    params = (programa_id,) if programa_id else ()
    return query(f'''SELECT f.numero AS ficha, COUNT(u.id) AS total
        FROM fichas f LEFT JOIN usuarios u ON u.ficha_id = f.id
        {cond}
        GROUP BY f.id, f.numero ORDER BY f.numero''', params)

def aprendices_por_colegio(programa_id=None):
    """Cantidad de aprendices por colegio (a través de fichas)."""
    cond = "WHERE f.programa_id = %s" if programa_id else ""
    params = (programa_id,) if programa_id else ()
    return query(f'''SELECT c.nombre_colegio AS colegio, COUNT(u.id) AS total
        FROM colegios c
        LEFT JOIN fichas f ON f.colegio_id = c.idcolegio
        LEFT JOIN usuarios u ON u.ficha_id = f.id
        {cond}
        GROUP BY c.idcolegio, c.nombre_colegio ORDER BY total DESC''', params)

def fichas_por_programa_stats(programa_id=None):
    """Cantidad de fichas por programa para gráfica donut."""
    cond = "WHERE p.id = %s" if programa_id else ""
    params = (programa_id,) if programa_id else ()
    return query(f'''SELECT p.nombre AS programa, COUNT(f.id) AS total
        FROM programas p
        LEFT JOIN fichas f ON f.programa_id = p.id
        {cond}
        GROUP BY p.id, p.nombre ORDER BY total DESC''', params)

def top_fichas(limite=10, programa_id=None):
    """Top fichas con más aprendices, incluyendo programa y colegio."""
    cond = "WHERE f.programa_id = %s" if programa_id else ""
    params = (programa_id, limite) if programa_id else (limite,)
    return query(f'''SELECT f.numero AS ficha, p.nombre AS programa,
            COALESCE(c.nombre_colegio, '—') AS colegio,
            f.jornada, COUNT(u.id) AS total
        FROM fichas f
        LEFT JOIN programas p ON f.programa_id = p.id
        LEFT JOIN colegios c ON f.colegio_id = c.idcolegio
        LEFT JOIN usuarios u ON u.ficha_id = f.id
        {cond}
        GROUP BY f.id, f.numero, p.nombre, c.nombre_colegio, f.jornada
        ORDER BY total DESC LIMIT %s''', params)



# ---------- PÚBLICO (landing page) ----------
def programas_con_stats():
    """Lista programas con total de fichas y aprendices, para la landing pública."""
    return query('''
        SELECT p.id, p.nombre AS nombre_programa, p.descripcion,
            COUNT(DISTINCT f.id) AS total_fichas,
            COUNT(DISTINCT u.id) AS total_aprendices
        FROM programas p
        LEFT JOIN fichas f ON f.programa_id = p.id
        LEFT JOIN usuarios u ON u.ficha_id = f.id
        GROUP BY p.id, p.nombre, p.descripcion
        ORDER BY p.nombre
    ''')


def estadisticas_publicas():
    """Estadísticas básicas para el hero de la landing page."""
    return {
        'total_usuarios': query('SELECT COUNT(*) AS c FROM usuarios', fetchone=True)['c'],
        'total_fichas': query('SELECT COUNT(*) AS c FROM fichas', fetchone=True)['c'],
        'total_programas': query('SELECT COUNT(*) AS c FROM programas', fetchone=True)['c'],
        'total_plantillas': query('SELECT COUNT(*) AS c FROM plantillas', fetchone=True)['c'],
    }


# ---------- COLEGIOS ----------
def listar_colegios():
    return query('SELECT * FROM colegios ORDER BY nombre_colegio')

def contar_colegios(search=None):
    if search:
        like = f'%{search}%'
        r = query('SELECT COUNT(*) AS total FROM colegios WHERE nombre_colegio LIKE %s', (like,), fetchone=True)
    else:
        r = query('SELECT COUNT(*) AS total FROM colegios', fetchone=True)
    return r['total']

def obtener_colegios_paginados(page=1, per_page=10, search=None):
    offset = (page - 1) * per_page
    if search:
        like = f'%{search}%'
        return query('SELECT * FROM colegios WHERE nombre_colegio LIKE %s ORDER BY nombre_colegio LIMIT %s OFFSET %s', (like, per_page, offset))
    return query('SELECT * FROM colegios ORDER BY nombre_colegio LIMIT %s OFFSET %s', (per_page, offset))

def obtener_colegio(cid):
    return query('SELECT * FROM colegios WHERE idcolegio=%s', (cid,), fetchone=True)

def crear_colegio(nombre, descripcion):
    return execute('INSERT INTO colegios (nombre_colegio,descripcion) VALUES (%s,%s)', (nombre, descripcion))

def actualizar_colegio(cid, nombre, descripcion):
    execute('UPDATE colegios SET nombre_colegio=%s,descripcion=%s WHERE idcolegio=%s', (nombre, descripcion, cid))

def eliminar_colegio(cid):
    execute('DELETE FROM colegios WHERE idcolegio=%s', (cid,))
