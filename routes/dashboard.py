from flask import Blueprint, render_template, session
import models
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    rol = session.get('admin_rol')
    programa_id = session.get('admin_programa_id') if rol == 'instructor' else None

    stats = models.estadisticas(programa_id)
    logs = models.listar_logs(10)
    por_estado = models.aprendices_por_estado(programa_id)
    por_programa = models.aprendices_por_programa(programa_id)
    por_colegio = models.aprendices_por_colegio(programa_id)
    fichas_programa = models.fichas_por_programa_stats(programa_id)
    top = models.top_fichas(10, programa_id)
    
    # Obtener fichas permitidas para el filtro de asistencia
    db = models.get_connection()
    cur = db.cursor(dictionary=True)
    from routes.asistencia.routes import fichas_permitidas
    mis_fichas = fichas_permitidas(cur)
    cur.close(); db.close()

    return render_template('dashboard.html', stats=stats, logs=logs,
                           por_estado=por_estado, por_programa=por_programa,
                           por_colegio=por_colegio,
                           fichas_programa=fichas_programa,
                           top_fichas=top, mis_fichas=mis_fichas)
