from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from werkzeug.security import generate_password_hash, check_password_hash
import models
from extensions import limiter

auth_bp = Blueprint('auth', __name__)




def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Debes iniciar sesion.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get('admin_rol') not in roles:
                flash('No tienes permisos para esta accion.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if session.get('admin_id'):
        return redirect(url_for('dashboard.index'))

    bloqueo = session.get('login_bloqueo')
    if bloqueo and datetime.fromisoformat(bloqueo) > datetime.now():
        flash('Demasiados intentos. Intenta mas tarde.', 'danger')
        return render_template('login.html', next='')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = models.obtener_admin_por_username(username)
        if admin and admin['activo'] and check_password_hash(admin['password_hash'], password):
            session.clear()
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_nombre'] = admin['nombre']
            session['admin_rol'] = admin['rol']
            models.registrar_log(admin['id'], admin['username'], 'LOGIN', 'admin',
                                  admin['id'], 'Inicio de sesion', request.remote_addr)
            next_url = request.args.get('next') or request.form.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))
        intentos = session.get('login_intentos', 0) + 1
        session['login_intentos'] = intentos
        if intentos >= current_app.config['MAX_LOGIN_ATTEMPTS']:
            session['login_bloqueo'] = (datetime.now() + timedelta(
                minutes=current_app.config['LOGIN_LOCKOUT_MINUTES'])).isoformat()
            session['login_intentos'] = 0
        flash('Usuario o contrasena incorrectos.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html', next=request.args.get('next', ''))


@auth_bp.route('/logout', methods=['POST'])
def logout():
    if session.get('admin_id'):
        models.registrar_log(session.get('admin_id'), session.get('admin_username'),
                             'LOGOUT', 'admin', session.get('admin_id'),
                             'Cierre de sesion', request.remote_addr)
    session.clear()
    flash('Sesion cerrada.', 'info')
    return redirect(url_for('auth.login'))
