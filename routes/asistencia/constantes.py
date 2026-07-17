from functools import wraps
from flask import session, abort

ESTADOS_ASISTENCIA = {
    "A":   {"label": "Asiste",                   "color": "#22c55e", "tecla": "1"},
    "CE":  {"label": "Con excusa",               "color": "#3b82f6", "tecla": "2"},
    "SE":  {"label": "Sin excusa",               "color": "#f59e0b", "tecla": "3"},
    "INC": {"label": "Incapacidad",              "color": "#ef4444", "tecla": "4"},
    "LIC": {"label": "Licencia",                 "color": "#a855f7", "tecla": "5"},
    "CLM": {"label": "Calamidad",                "color": "#6b7280", "tecla": "6"},
    "SFF": {"label": "Sin formación o feriados", "color": "#60a5fa", "tecla": "7"},
    "RET": {"label": "Retirado",                 "color": "#b91c1c", "tecla": "8"},
}

def es_estado_valido(codigo: str) -> bool:
    return codigo in ESTADOS_ASISTENCIA

def superadmin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("admin_rol") != "superadmin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper
