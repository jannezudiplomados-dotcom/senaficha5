from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import get_connection, registrar_log
from routes.auth import login_required, role_required

asignacion_bp = Blueprint(
    "asignacion", __name__,
    url_prefix="/asistencia/instructores"
)

@asignacion_bp.route("/", methods=["GET"])
@login_required
@role_required("superadmin", "admin")
def instructores():
    db = get_connection(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, username, nombre FROM admin WHERE rol = 'instructor' ORDER BY nombre")
    lista = cur.fetchall()
    cur.close(); db.close()
    return render_template("asistencia/instructores.html", instructores=lista)

@asignacion_bp.route("/<int:instructor_id>/asignar", methods=["GET"])
@login_required
@role_required("superadmin", "admin")
def asignar(instructor_id):
    db = get_connection(); cur = db.cursor(dictionary=True)

    cur.execute("SELECT id, username, nombre FROM admin WHERE id = %s AND rol = 'instructor'", (instructor_id,))
    instructor = cur.fetchone()
    if not instructor:
        flash("Instructor no encontrado", "danger")
        return redirect(url_for("asignacion.instructores"))

    cur.execute("SELECT id, nombre FROM programas ORDER BY nombre")
    programas = cur.fetchall()

    # Programas ya asignados
    cur.execute("SELECT programa_id FROM instructor_programas WHERE instructor_id = %s", (instructor_id,))
    prog_asignados = {r["programa_id"] for r in cur.fetchall()}

    # Fichas de los programas asignados
    fichas = []
    if prog_asignados:
        placeholders = ",".join(["%s"] * len(prog_asignados))
        cur.execute(
            f"SELECT id, numero, programa_id FROM fichas WHERE programa_id IN ({placeholders}) ORDER BY numero",
            tuple(prog_asignados)
        )
        fichas = cur.fetchall()

    cur.execute("SELECT ficha_id FROM instructor_fichas WHERE instructor_id = %s", (instructor_id,))
    fichas_asignadas = {r["ficha_id"] for r in cur.fetchall()}
    cur.close(); db.close()

    return render_template(
        "asistencia/asignar.html",
        instructor=instructor, programas=programas, prog_asignados=prog_asignados,
        fichas=fichas, fichas_asignadas=fichas_asignadas
    )

@asignacion_bp.route("/<int:instructor_id>/programas", methods=["POST"])
@login_required
@role_required("superadmin", "admin")
def guardar_programas(instructor_id):
    seleccion = request.form.getlist("programa_id")
    db = get_connection(); cur = db.cursor()
    try:
        cur.execute("DELETE FROM instructor_programas WHERE instructor_id = %s", (instructor_id,))
        for pid in seleccion:
            cur.execute(
                "INSERT INTO instructor_programas (instructor_id, programa_id) VALUES (%s, %s)",
                (instructor_id, int(pid))
            )
        db.commit()
        registrar_log(session.get("admin_id"), session.get("admin_username"), "ASIGNAR", "instructor_programas", instructor_id, str(seleccion))
        flash("Programas actualizados", "success")
    except Exception as e:
        db.rollback(); flash(f"Error: {e}", "danger")
    finally:
        cur.close(); db.close()
    return redirect(url_for("asignacion.asignar", instructor_id=instructor_id))

@asignacion_bp.route("/<int:instructor_id>/fichas", methods=["POST"])
@login_required
@role_required("superadmin", "admin")
def guardar_fichas(instructor_id):
    seleccion = request.form.getlist("ficha_id")
    db = get_connection(); cur = db.cursor()
    try:
        cur.execute("DELETE FROM instructor_fichas WHERE instructor_id = %s", (instructor_id,))
        for fid in seleccion:
            cur.execute(
                "INSERT INTO instructor_fichas (instructor_id, ficha_id, asignado_por) VALUES (%s, %s, %s)",
                (instructor_id, int(fid), session.get("admin_id"))
            )
        db.commit()
        registrar_log(session.get("admin_id"), session.get("admin_username"), "ASIGNAR", "instructor_fichas", instructor_id, str(seleccion))
        flash("Fichas actualizadas", "success")
    except Exception as e:
        db.rollback(); flash(f"Error: {e}", "danger")
    finally:
        cur.close(); db.close()
    return redirect(url_for("asignacion.asignar", instructor_id=instructor_id))
