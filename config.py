import os
from datetime import timedelta

# Carga opcional de variables desde un archivo .env (si python-dotenv esta instalado)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import warnings
        warnings.warn('SECRET_KEY no esta configurada. Usando clave temporal. Define la variable en .env')
        SECRET_KEY = os.urandom(32).hex()

    # MySQL
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'sena_fichas4')

    # Carpetas
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'plantillas')
    FIRMAS_FOLDER = os.path.join(BASE_DIR, 'static', 'firmas')
    FOTOS_FOLDER = os.path.join(BASE_DIR, 'static', 'fotos')
    GENERADOS_FOLDER = os.path.join(BASE_DIR, 'static', 'generados')

    ALLOWED_EXTENSIONS = {'docx', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Seguridad / login
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 5

    # Session Hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ['true', '1', 't']
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Acudiente Config
    ACUDIENTE_SESSION_MINUTES = int(os.environ.get('ACUDIENTE_SESSION_MINUTES', 20))
    ACUDIENTE_MAX_JUSTIFICACIONES_MB = int(os.environ.get('ACUDIENTE_MAX_JUSTIFICACIONES_MB', 5))
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    # Entorno
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

    # Paginacion
    PER_PAGE = 10
