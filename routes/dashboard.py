from flask import Blueprint, render_template
import models
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    stats = models.estadisticas()
    logs = models.listar_logs(10)
    por_estado = models.aprendices_por_estado()
    por_programa = models.aprendices_por_programa()
    por_colegio = models.aprendices_por_colegio()
    fichas_programa = models.fichas_por_programa_stats()
    top = models.top_fichas(10)
    return render_template('dashboard.html', stats=stats, logs=logs,
                           por_estado=por_estado, por_programa=por_programa,
                           por_colegio=por_colegio,
                           fichas_programa=fichas_programa,
                           top_fichas=top)
