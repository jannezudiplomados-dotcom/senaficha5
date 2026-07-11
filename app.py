import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session
from extensions import csrf, limiter
from config import Config
import models


def _configurar_logs(app):
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(os.path.join(log_dir, 'error.log'),
                                  maxBytes=1024 * 1024, backupCount=3, encoding='utf-8')
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [en %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)
    limiter.init_app(app)
    _configurar_logs(app)

    for folder in (Config.UPLOAD_FOLDER, Config.FIRMAS_FOLDER, Config.GENERADOS_FOLDER):
        os.makedirs(folder, exist_ok=True)

    models.init_pool()

    from routes.public import public_bp
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.usuarios import usuarios_bp
    from routes.programas import programas_bp
    from routes.fichas import fichas_bp
    from routes.documentos import documentos_bp
    from routes.plantillas import plantillas_bp
    from routes.admins import admins_bp
    from routes.colegios import colegios_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(programas_bp, url_prefix='/programas')
    app.register_blueprint(fichas_bp, url_prefix='/fichas')
    app.register_blueprint(documentos_bp, url_prefix='/documentos')
    app.register_blueprint(plantillas_bp, url_prefix='/plantillas')
    app.register_blueprint(admins_bp, url_prefix='/admins')
    app.register_blueprint(colegios_bp, url_prefix='/colegios')

    @app.context_processor
    def inject_user():
        return dict(usuario_actual=session.get('admin_nombre'),
                    rol_actual=session.get('admin_rol'))

    @app.errorhandler(404)
    def e404(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def e413(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def e500(e):
        app.logger.error('Error interno 500: %s', e, exc_info=True)
        return render_template('errors/500.html'), 500

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        # HSTS solo cuando HTTPS esta configurado (SESSION_COOKIE_SECURE=True en .env)
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # Basic CSP, ajustado si necesitas recursos de terceros
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net data:; img-src 'self' data:; object-src 'none'"
        return response

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='127.0.0.1', port=5000)
