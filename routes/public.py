from datetime import datetime
from flask import Blueprint, render_template
import models

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def home():
    """Landing page pública de SIGDA."""
    try:
        stats = models.estadisticas_publicas()
        programas = models.programas_con_stats()
    except Exception:
        stats = None
        programas = []
    return render_template('home.html', stats=stats, programas=programas,
                           now=datetime.now())


@public_bp.route('/programas-publico')
def programas_publico():
    """Vista pública de programas de formación."""
    try:
        programas = models.programas_con_stats()
    except Exception:
        programas = []
    return render_template('programas_publico.html', programas=programas,
                           now=datetime.now())
