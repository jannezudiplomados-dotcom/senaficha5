# Módulo Portal del Acudiente — Informe de Asistencia

> **Proyecto:** SIGDA — Sistema de Gestión de Fichas SENA (`sena_fichas4/`)
> **Stack:** Python 3 · Flask (Blueprints) · MySQL (mysql-connector) · Jinja2 · Bootstrap 5 · Chart.js · JS vanilla
> **Objetivo:** habilitar un rol **`acudiente`** con acceso restringido a un único portal donde puede buscar a su aprendiz (por nombre, apellido o identificación) y consultar su informe de asistencia completo (mismo formato que el actual, adaptado a vista individual).
>
> **🔒 REGLA DE ORO (NO NEGOCIABLE):** al iniciar sesión con rol `acudiente`, el usuario **solo debe ver UN menú**: *🔍 Buscar mi Aprendiz*. **Cero acceso** al sidebar completo, cero acceso a otros módulos (fichas, aprendices, documentos, bitácoras, asistencia, reportes, configuración, usuarios, admin, etc.). Cualquier intento de navegar a otra ruta debe redirigirlo automáticamente al portal del acudiente.
>
> **⚡ COMPORTAMIENTO AL LOGIN (UX inteligente):**
> - Si tiene **1 solo aprendiz asociado** → **salta el portal** y va directo al informe del aprendiz (con el mes actual precargado). Ve el historial de una.
> - Si tiene **varios aprendices asociados** (ej. hermanos) → ve el portal con tarjetas + buscador para elegir.
> - Si **no tiene aprendices asociados** → mensaje amigable *"Aún no tienes aprendices asociados. Contacta con la coordinación académica."*
> - En todos los casos, un botón *"Cambiar de aprendiz"* / *"Ver todos mis aprendices"* está siempre visible en el header del informe para volver al portal cuando corresponda.
> **Target del prompt:** **Antigravity + Gemini 3.1 Pro** (código profesional, con validaciones exhaustivas, tests mínimos y trazabilidad).

---

## Tabla de contenidos

1. [Contexto y motivación](#1-contexto-y-motivación)
2. [Concepto del rol Acudiente](#2-concepto-del-rol-acudiente)
3. [Modelo de datos](#3-modelo-de-datos)
4. [Autenticación, autorización y menú restringido](#4-autenticación-autorización-y-menú-restringido)
5. [Flujo UX del portal del acudiente](#5-flujo-ux-del-portal-del-acudiente)
6. [Endpoints backend](#6-endpoints-backend)
7. [Informes y gráficas (extendido y profesional)](#7-informes-y-gráficas-extendido-y-profesional)
8. [Seguridad y privacidad (LOPD / Habeas Data)](#8-seguridad-y-privacidad-lopd--habeas-data)
9. [Estructura de archivos en `sena_fichas4/`](#9-estructura-de-archivos-en-sena_fichas4)
10. [🤖 Prompt para Antigravity (Gemini 3.1 Pro)](#10-prompt-para-antigravity-gemini-31-pro)
11. [Criterios de aceptación](#11-criterios-de-aceptación)

---

## 1. Contexto y motivación

El sistema SIGDA hoy expone el **Informe de Asistencia** (pestaña `Informe de Asistencia` bajo Asistencia) solo a instructores y administradores. El módulo permite:

- Seleccionar ficha, estudiante y rango de fechas.
- Ver tabla con conteos de A / CE / SE / INC / LIC / CLM / SFF.
- Exportar Excel / PDF / Imprimir.
- Analizar con IA (resumen automático).
- Gráfica de dona: **Distribución de Asistencia**.

**Necesidad nueva:** los **padres o acudientes** de los aprendices necesitan consultar el estado de asistencia de su hijo/a sin acceso al resto de la plataforma, cumpliendo con habeas data (solo ven a SU aprendiz asociado).

---

## 2. Concepto del rol Acudiente

### 2.1 Definición

`acudiente` = padre, madre o representante legal de un aprendiz, autorizado a consultar la información académica básica del menor/aprendiz asociado.

### 2.2 Reglas de negocio

| Regla | Detalle |
|-------|---------|
| **Relación** | Un acudiente puede tener **1 a N aprendices** asociados (ej. hermanos). Un aprendiz puede tener **1 a N acudientes**. Relación many-to-many. |
| **Alcance de visibilidad** | Solo puede ver aprendices con relación activa (`estado='activo'`) confirmada por un `admin` o `superadmin`. |
| **Menú** | Al iniciar sesión ve **una sola opción**: *🔍 Buscar mi Aprendiz*. No hay sidebar, ni submenús, ni acceso a otros módulos. |
| **Auto-load al login** | Si tiene 1 solo aprendiz asociado, va **directo al informe** de ese aprendiz. Si tiene varios, ve el portal con tarjetas. |
| **Búsqueda** | Por nombre, apellido o número de identificación **restringida a sus aprendices asociados** (no puede consultar cualquiera). |
| **Datos visibles** | Solo asistencia agregada por período. NO ve calificaciones, comentarios de instructores, ni datos de otros compañeros. |
| **Datos ocultos** | Correo personal del aprendiz, dirección, teléfono, firma. |
| **Auditoría** | Cada consulta se registra en `log_actividades` con IP, timestamp, ID de aprendiz consultado y rango de fechas. |
| **Sesión** | Timeout de sesión reducido a 20 minutos por inactividad (vs. 2 h del rol instructor). |
| **Contraseña** | Obligatorio cambiar contraseña en primer login. Recuperación por correo. |

### 2.3 Datos que un acudiente SÍ puede ver

- Nombre completo del aprendiz.
- Ficha, programa de formación.
- **Informe de asistencia** por rango de fechas (mismo formato que la tercera imagen).
- Distribución de asistencia (dona).
- **Tendencia mensual** de asistencia (gráfico de línea — nuevo).
- **Detalle por día** (calendar heatmap — nuevo).
- **Comparativo vs. promedio de la ficha** (barras — nuevo, anonimizado).
- **Alertas** si `SE (Sin Excusa) > 3` en el período (badge rojo).
- **Historial de justificaciones** subidas.
- **Exportar PDF** solo del aprendiz asociado (con marca de agua *"Reporte para acudiente"*).

### 2.4 Datos que un acudiente NO puede ver

- Datos de otros aprendices, ni siquiera de la misma ficha.
- Correo institucional/personal del aprendiz.
- Dirección, teléfono, firma dibujada.
- Módulos de bitácora, documentos, notas, reportes globales.
- Endpoints AJAX del sistema principal.

---

## 3. Modelo de datos

### 3.1 Extender roles existentes

Agregar `'acudiente'` al ENUM de roles en `usuarios`:

```sql
-- Migración: migraciones/20260723_acudiente_role.sql
ALTER TABLE usuarios
  MODIFY COLUMN rol ENUM('superadmin','admin','instructor','acudiente') NOT NULL;
```

### 3.2 Nueva tabla `acudiente_aprendiz` (relación N:N)

```sql
CREATE TABLE acudiente_aprendiz (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id     INT NOT NULL,                -- usuarios.id con rol='acudiente'
  aprendiz_id    INT NOT NULL,                -- aprendices.id
  parentesco     ENUM('padre','madre','tutor','abuelo','abuela','tio','tia','otro') NOT NULL DEFAULT 'otro',
  parentesco_otro VARCHAR(60) NULL,           -- solo si parentesco='otro'
  telefono_contacto VARCHAR(30) NULL,
  documento_soporte VARCHAR(500) NULL,        -- PDF/imagen que valida el parentesco (registro civil, autorización)
  estado         ENUM('pendiente','activo','revocado') NOT NULL DEFAULT 'pendiente',
  aprobado_por   INT NULL,                    -- usuarios.id (admin o superadmin)
  aprobado_en    DATETIME NULL,
  motivo_revocacion TEXT NULL,
  creado_en      DATETIME DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_acu_apr (usuario_id, aprendiz_id),
  INDEX idx_usuario_estado (usuario_id, estado),
  INDEX idx_aprendiz (aprendiz_id),
  FOREIGN KEY (usuario_id)   REFERENCES usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (aprendiz_id)  REFERENCES aprendices(id) ON DELETE CASCADE,
  FOREIGN KEY (aprobado_por) REFERENCES usuarios(id)
);
```

### 3.3 Tabla `acudiente_consultas_log` (auditoría específica)

Complementa `log_actividades` con datos estructurados para reportería de acceso:

```sql
CREATE TABLE acudiente_consultas_log (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id      INT NOT NULL,
  aprendiz_id     INT NOT NULL,
  accion          ENUM('busqueda','informe','exportar_pdf','exportar_excel','descarga_justificacion') NOT NULL,
  fecha_inicial   DATE NULL,
  fecha_final     DATE NULL,
  ip              VARCHAR(45),
  user_agent      VARCHAR(300),
  creado_en       DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_usuario_fecha (usuario_id, creado_en),
  INDEX idx_aprendiz_fecha (aprendiz_id, creado_en),
  FOREIGN KEY (usuario_id)  REFERENCES usuarios(id),
  FOREIGN KEY (aprendiz_id) REFERENCES aprendices(id)
);
```

### 3.4 Vista SQL de conveniencia (opcional pero recomendado)

```sql
CREATE OR REPLACE VIEW v_acudiente_aprendices_activos AS
SELECT
  aa.usuario_id,
  a.id           AS aprendiz_id,
  a.numero_documento,
  a.tipo_documento,
  CONCAT_WS(' ', a.nombres, a.apellidos) AS nombre_completo,
  a.nombres,
  a.apellidos,
  a.ficha_id,
  f.numero        AS ficha_numero,
  p.id            AS programa_id,
  p.nombre        AS programa_nombre,
  aa.parentesco,
  aa.estado       AS estado_relacion
FROM acudiente_aprendiz aa
JOIN aprendices a ON a.id = aa.aprendiz_id
JOIN fichas f     ON f.id = a.ficha_id
JOIN programas p  ON p.id = f.programa_id
WHERE aa.estado = 'activo';
```

---

## 4. Autenticación, autorización y menú restringido

### 4.1 Redirección post-login por rol (con auto-load inteligente)

En la ruta de login (posiblemente `routes/auth.py` o similar):

```python
# después de validar credenciales exitosamente
if user['rol'] == 'acudiente':
    # 1. cambio de contraseña obligatorio en primer login
    if user['requiere_cambio_password']:
        return redirect(url_for('acudiente.cambiar_password'))

    # 2. auto-load inteligente según cuántos aprendices tenga asociados
    from servicios.acu_models import listar_aprendices_de_acudiente
    aprendices = listar_aprendices_de_acudiente(user['id'])

    if len(aprendices) == 1:
        # → salta el portal, va directo al informe del único aprendiz
        return redirect(url_for('acudiente.informe_aprendiz', aid=aprendices[0]['aprendiz_id']))

    # 0 o 2+ aprendices → portal con tarjetas + buscador
    return redirect(url_for('acudiente.portal'))
else:
    return redirect(url_for('dashboard.index'))            # flujo actual sin cambios
```

**Comportamiento resultante:**

| Aprendices asociados | Redirección post-login | Vista final |
|----------------------|------------------------|-------------|
| 0 | `/acudiente/portal` | Mensaje "Sin aprendices asociados. Contacta coordinación." |
| 1 | `/acudiente/aprendiz/<id>` | Informe del aprendiz con mes actual precargado (auto-generado). |
| 2 o más | `/acudiente/portal` | Portal con buscador + tarjetas para elegir. |

En todas las pantallas del informe, un botón **"← Cambiar de aprendiz"** está disponible en el header (visible solo si el acudiente tiene más de un aprendiz asociado).

### 4.2 Decorador `@acudiente_required`

```python
# servicios/acu_auth.py
from functools import wraps
from flask import session, redirect, url_for, abort

def acudiente_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('rol') != 'acudiente':
            abort(403)
        return f(*args, **kwargs)
    return wrapper
```

### 4.3 Layout base separado (`templates/acudiente/base.html`)

> 🚨 **IMPORTANTE:** este layout es TOTALMENTE independiente del layout actual del sistema. NO se debe reutilizar `templates/base.html` (o el layout equivalente que trae el sidebar con módulos como Fichas, Aprendices, Documentos, Asistencia, etc.). El acudiente **no debe ver ese sidebar bajo ninguna circunstancia**.

- **No hereda** del layout de instructor/admin (que trae sidebar completo).
- **Sin sidebar**, sin menú lateral, sin íconos de módulos, sin dropdowns de admin.
- Header simple y limpio: logo institucional + título "Portal del Acudiente" + nombre del usuario + botón *Salir*.
- Contenido centrado con `container-md`.
- Footer con enlaces a *Política de tratamiento de datos* y *Contacto institucional*.
- La única opción de navegación visible es el buscador de aprendices ("🔍 Buscar mi Aprendiz") ya renderizado como contenido central.
- Cero enlaces hacia otras rutas del sistema en el HTML entregado al acudiente.

### 4.4 Middleware: forzar redirect si acudiente intenta otras rutas

Este middleware es la **segunda línea de defensa** (además del layout separado): si por algún motivo el acudiente escribe manualmente una URL de otro módulo en la barra del navegador (ej. `/fichas`, `/aprendices`, `/admin`, `/documentos`, etc.), el sistema lo devuelve automáticamente a su portal.

```python
# en el before_request global (donde ya se validan sesiones)
WHITELIST_ACUDIENTE = ('acudiente.', 'acudiente_api.', 'auth.logout', 'auth.login', 'static')

if session.get('rol') == 'acudiente':
    ep = request.endpoint or ''
    if not ep.startswith(WHITELIST_ACUDIENTE):
        # log del intento de acceso para auditoría
        logger.warning(
            "Acudiente %s intentó acceder a %s (bloqueado)",
            session.get('user_id'), request.path
        )
        return redirect(url_for('acudiente.portal'))
```

**Reglas complementarias:**

- Los templates de `acudiente/*.html` no deben incluir ni un solo `<a href="/otro_modulo">` o `{% include 'sidebar.html' %}`. Todo elemento de navegación hacia rutas fuera del blueprint `acudiente` está prohibido.
- El menú contextual del navegador (right-click) o inspección de HTML no debe revelar ninguna ruta administrativa.
- Los endpoints AJAX externos al blueprint `acudiente_api` deben responder 403 si la sesión es de rol acudiente (defensa en profundidad).

---

## 5. Flujo UX del portal del acudiente

### 5.1 Login

- Misma pantalla actual, sin cambios.
- Al detectar rol `acudiente`, aplica el auto-load inteligente:
  - **1 aprendiz asociado** → redirige directo al informe (`/acudiente/aprendiz/<id>`) con mes actual precargado. **No pasa por el portal.**
  - **2 o más aprendices** → redirige al portal (`/acudiente/portal`) para que elija.
  - **0 aprendices** → redirige al portal con mensaje de contacto a coordinación.
- En el primer login, obliga a cambiar contraseña y aceptar tratamiento de datos (checkbox de habeas data) **antes** de aplicar el auto-load.

### 5.2 Portal principal (solo si tiene 2+ aprendices o 0)

> 💡 **Nota:** si el acudiente tiene **1 solo aprendiz asociado, esta pantalla se omite** y va directo al informe. Este portal aparece solo cuando hay que elegir entre varios aprendices, o cuando no hay ninguno asociado.

```
┌────────────────────────────────────────────────────────────────┐
│ [SENA]  Portal del Acudiente          👤 María López  [Salir] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│              🔍 Consulta la asistencia de tu aprendiz          │
│                                                                │
│   ┌────────────────────────────────────────────┐  ┌────────┐  │
│   │  Nombre, apellido o número de documento    │  │ Buscar │  │
│   └────────────────────────────────────────────┘  └────────┘  │
│                                                                │
│   Sugerencia: puedes escribir el nombre completo, un apellido │
│   o el número de identificación de tu aprendiz.               │
│                                                                │
│   ─────── Aprendices asociados a tu cuenta ───────            │
│                                                                │
│   👦 Juan Pérez Gómez     CC 1024535253     Ficha 3415660     │
│      Programa: PROGRAMACION DE SOFTWARE                       │
│      [Ver informe →]                                          │
│                                                                │
│   👧 Laura Pérez Gómez    TI 1099887766     Ficha 3512420     │
│      Programa: ANALISIS Y DESARROLLO DE SOFTWARE              │
│      [Ver informe →]                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Comportamiento del buscador (solo relevante si tiene 2+ aprendices):**

- Autocompletado con debounce 300 ms (endpoint AJAX).
- Solo resuelve resultados dentro de `v_acudiente_aprendices_activos` filtrada por `usuario_id = current_user.id`.
- `Enter` o click en *Buscar* → si hay un único match, salta directo al informe. Si hay varios, muestra lista.
- Si el buscador va vacío, se muestran todos los aprendices asociados como tarjetas (ver mockup).
- Si el acudiente no tiene aprendices asociados → mensaje amigable: *"Aún no tienes aprendices asociados. Contacta con la coordinación académica."* con botón *Contactar*.

> 💡 **Recordatorio:** si el acudiente tiene 1 solo aprendiz asociado nunca ve esta pantalla (va directo al informe por el auto-load del login).

### 5.3 Pantalla del informe (post-búsqueda o post-login directo)

Replica exacta de la tercera imagen del usuario, **pero adaptada:**

- **Ocultar** el selector de "Selecciona Ficha" y "Estudiante" (ya vienen fijos por la búsqueda o auto-load).
- Cuando se llega por auto-load (1 solo aprendiz), la página **genera automáticamente el informe del mes actual** al cargar (sin esperar click en "Generar Informe").
- Botón **← Cambiar de aprendiz** en el header, visible solo si `len(aprendices_asociados) > 1`.
- Mostrar:
  - Cabecera con datos del aprendiz seleccionado (nombre, doc enmascarado, ficha, programa).
  - Selectores de **Fecha Inicial** y **Fecha Final** (por defecto: mes actual).
  - Botón **Generar Informe** y **Volver a búsqueda** (este último solo si tiene 2+ aprendices).
- Tras generar, mostrar:
  1. Barra azul de resumen (Ficha · Total días · Período).
  2. Tabla de conteo `A · CE · SE · INC · LIC · CLM · SFF · ...`.
  3. Botones: *Analizar con IA* · *Exportar Excel* · *Exportar PDF* · *Imprimir*.
  4. Dona **Distribución de Asistencia**.
  5. **[NUEVO]** Línea de **Tendencia mensual** (últimos 6 meses).
  6. **[NUEVO]** **Calendario heatmap** con estado por día.
  7. **[NUEVO]** **Comparativo vs promedio de la ficha** (barras anonimizadas).
  8. **[NUEVO]** Panel de **Alertas** (si SE > 3, INC prolongada, etc.).
  9. **[NUEVO]** Sección **Justificaciones**: subir soporte (PDF/JPG) para inasistencias marcadas SE.
  10. Panel de **Análisis con IA**: resumen en lenguaje natural ("Juan ha asistido al 92% de las sesiones. Sin embargo tiene 2 inasistencias sin excusa en la última semana; se recomienda...").

---

## 6. Endpoints backend

Todos con `@acudiente_required` y validación de propiedad de la relación:

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/acudiente/portal` | Landing con buscador + tarjetas de aprendices asociados. **Solo se muestra si hay 2+ aprendices o ninguno**; si hay 1 solo, el login ya redirigió al informe directamente. |
| `GET`  | `/acudiente/api/buscar?q=<texto>` | Autocomplete (solo aprendices asociados). Retorna JSON `[{id, nombre_completo, num_doc, ficha, programa}]`. |
| `GET`  | `/acudiente/aprendiz/<id>` | Pantalla del informe. Verifica que `<id>` pertenezca al acudiente. **Auto-genera** el informe del mes actual al cargar. Endpoint con nombre `acudiente.informe_aprendiz`. |
| `POST` | `/acudiente/aprendiz/<id>/informe` | Genera JSON del informe (tabla, dona, tendencia, heatmap, comparativo, alertas). Body: `{fecha_inicial, fecha_final}`. |
| `GET`  | `/acudiente/aprendiz/<id>/informe/pdf?desde=&hasta=` | Descarga PDF con marca de agua *"Reporte para acudiente"*. |
| `GET`  | `/acudiente/aprendiz/<id>/informe/excel?desde=&hasta=` | Descarga Excel. |
| `POST` | `/acudiente/aprendiz/<id>/analizar-ia` | Devuelve resumen textual generado por IA sobre el rango. |
| `POST` | `/acudiente/aprendiz/<id>/justificacion` | Sube archivo (PDF/JPG) justificando inasistencia. Guarda en `static/uploads/acudiente_justificaciones/`. Notifica al instructor de la ficha. |
| `GET`  | `/acudiente/aprendiz/<id>/justificaciones` | Lista justificaciones subidas (historial). |
| `POST` | `/acudiente/perfil/cambiar-password` | Cambio obligatorio en primer login. |
| `GET`  | `/acudiente/politica-datos` | Página estática con política de tratamiento de datos. |

**Reglas clave para todas las rutas de `<id>` de aprendiz:**

```python
def verificar_pertenencia(usuario_id: int, aprendiz_id: int) -> bool:
    query = """
        SELECT 1 FROM acudiente_aprendiz
        WHERE usuario_id = %s AND aprendiz_id = %s AND estado = 'activo'
        LIMIT 1
    """
    # devolver bool; si False, abort(404) — nunca 403 para no filtrar existencia
```

---

## 7. Informes y gráficas (extendido y profesional)

### 7.1 Tabla de asistencia

Mismas columnas que hoy (`A, CE, SE, INC, LIC, CLM, SFF` y cualquier otra existente). Renderizada con Bootstrap 5, sin permitir edición.

### 7.2 Gráfica dona — Distribución de asistencia (Chart.js)

Existente, con colores accesibles WCAG AA:

- A (verde `#22c55e`)
- CE (azul `#3b82f6`)
- SE (rojo `#ef4444`)
- INC (amarillo `#eab308`)
- LIC (púrpura `#a855f7`)
- CLM (naranja `#f97316`)
- SFF (gris `#6b7280`)

### 7.3 [NUEVO] Línea de tendencia mensual (últimos 6 meses)

Chart.js `line` con dataset por estado. Permite ver evolución del porcentaje de asistencia. Muestra en tooltip cifras absolutas.

### 7.4 [NUEVO] Calendario heatmap por día

Grilla tipo GitHub contributions. Cada celda:
- Verde intenso → A
- Azul → CE
- Rojo → SE
- Amarillo → INC
- Gris → sin registro/día no lectivo

Al pasar el mouse: fecha y estado. Al hacer click: abre panel lateral con detalle.

### 7.5 [NUEVO] Comparativo vs promedio de la ficha (barras)

Dos barras por categoría:
- Aprendiz consultado (nombre)
- Promedio de la ficha (anonimizado, sin listar compañeros)

Muestra al acudiente si el aprendiz está por encima o debajo del promedio. Solo lectura.

### 7.6 [NUEVO] Panel de alertas

Cards de colores con reglas configurables (en `bam_config` o nueva `acudiente_config`):

| Condición | Nivel | Mensaje |
|-----------|-------|---------|
| `SE >= 3` en el período | 🔴 Crítico | *"El aprendiz tiene X inasistencias sin excusa. Se recomienda contacto inmediato."* |
| `INC >= 5 días consecutivos` | 🟡 Advertencia | *"Inasistencia por incapacidad prolongada. Verifica la certificación médica."* |
| `Asistencia < 80%` | 🟠 Atención | *"Porcentaje de asistencia por debajo del mínimo institucional."* |
| `Racha CE >= 3` | 🟡 Advertencia | *"Varias inasistencias justificadas consecutivas."* |
| Todo OK | 🟢 Estado óptimo | *"Asistencia dentro de rangos esperados. ¡Felicitaciones!"* |

### 7.7 [NUEVO] Sección de justificaciones

- Formulario con selector de fecha (SE del período) + archivo PDF/JPG.
- Al enviar, guarda en `static/uploads/acudiente_justificaciones/<uuid>.<ext>` y crea registro en `acudiente_justificaciones` (nueva tabla, ver §3).
- Notifica al instructor de la ficha (correo + campanita in-app si existe).
- El instructor luego puede aprobar → cambia estado del día `SE → CE` en el módulo de asistencia (fuera de alcance directo del acudiente).

**Tabla soporte:**

```sql
CREATE TABLE acudiente_justificaciones (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id     INT NOT NULL,        -- acudiente que subió
  aprendiz_id    INT NOT NULL,
  fecha_inasistencia DATE NOT NULL,
  archivo_ruta   VARCHAR(500) NOT NULL,
  comentario     TEXT,
  estado         ENUM('pendiente','aprobada','rechazada') DEFAULT 'pendiente',
  revisado_por   INT NULL,
  revisado_en    DATETIME NULL,
  comentario_revision TEXT NULL,
  creado_en      DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aprendiz_fecha (aprendiz_id, fecha_inasistencia),
  INDEX idx_estado (estado),
  FOREIGN KEY (usuario_id)  REFERENCES usuarios(id),
  FOREIGN KEY (aprendiz_id) REFERENCES aprendices(id),
  FOREIGN KEY (revisado_por) REFERENCES usuarios(id)
);
```

### 7.8 [NUEVO] Análisis con IA

Reutilizar el servicio de IA existente ("Analizar con IA" ya visible en la imagen). El prompt hacia el modelo debe incluir:

- Nombre del aprendiz + programa + ficha.
- Rango de fechas.
- Métricas: total días, % asistencia, número por categoría.
- Tendencia (mejora/empeora respecto al mes anterior).
- Instrucción: **generar un resumen en lenguaje natural, empático, dirigido al acudiente**, con 2-3 recomendaciones accionables y sin jerga técnica.

### 7.9 [NUEVO] Exportar PDF con marca de agua

- WeasyPrint o ReportLab (elegir según lo ya usado en SIGDA).
- Encabezado institucional SENA + "Reporte de asistencia — Portal del Acudiente".
- Marca de agua diagonal *"CONFIDENCIAL — Uso exclusivo del acudiente autorizado"*.
- Pie con fecha de generación, IP, ID de consulta (para trazabilidad).

---

## 8. Seguridad y privacidad (LOPD / Habeas Data)

### 8.1 Reglas obligatorias

1. **Nunca revelar datos de aprendices no asociados**, ni siquiera con IDs directos en URL (`/acudiente/aprendiz/999` de un aprendiz ajeno → 404).
2. **Escapar y validar** todo input del buscador (SQL parametrizado, sin string interpolation).
3. **Rate limiting**: máx. 60 requests/minuto por acudiente (Flask-Limiter o similar) para prevenir enumeración.
4. **Auditoría completa** en `acudiente_consultas_log` de cada acción.
5. **Sesión con timeout corto** (20 min de inactividad).
6. **Contraseña**: mínimo 10 caracteres, con mayúscula + minúscula + número + símbolo. Hash bcrypt (cost ≥ 12).
7. **CSRF** activo en todos los formularios (ya configurado global).
8. **Cookies**: `Secure`, `HttpOnly`, `SameSite=Lax`.
9. **Cabeceras de seguridad** (Flask-Talisman o headers manuales): `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy` estricta.
10. **Consentimiento habeas data**: registrar aceptación explícita con timestamp e IP en tabla `acudiente_consentimientos` (columna `aceptado_politica_v` con versión del documento).
11. **Sin exponer nombres de aprendices en URLs** por buscadores. Todas las rutas requieren sesión activa.
12. **Enmascarar identificación** en la UI (`10245*****53`) excepto al descargar el PDF final.

### 8.2 Onboarding del acudiente (creación de cuenta)

El `admin` o `superadmin` crea la cuenta desde el módulo actual de "Nuevo administrador" (ver segunda imagen del usuario):

- Rol nuevo `acudiente` disponible en el combo.
- Al elegir `acudiente`, el formulario debe mostrar **campo obligatorio de aprendiz(es) a asociar** (multi-select con búsqueda) + parentesco + carga de documento soporte.
- Al crear, se genera una contraseña temporal enviada por correo (o entregada físicamente).
- La relación queda `estado='pendiente'` hasta que un `superadmin` la apruebe (o `activo` si el creador ya es `superadmin`).

---

## 9. Estructura de archivos en `sena_fichas4/`

> Sigue la convención plana existente del proyecto (`routes/`, `servicios/`, `templates/`, `static/`, `migraciones/`).

```
sena_fichas4/
├── migraciones/
│   └── 20260723_acudiente_module.sql       # NUEVO — roles + tablas nuevas
├── routes/
│   ├── acudiente.py                         # NUEVO — rutas HTML (portal, informe)
│   └── acudiente_api.py                     # NUEVO — endpoints AJAX (buscar, informe JSON, justificar)
├── servicios/
│   ├── acu_auth.py                          # NUEVO — decorador @acudiente_required + verificar_pertenencia
│   ├── acu_models.py                        # NUEVO — CRUD sobre acudiente_*
│   ├── acu_informe.py                       # NUEVO — cálculo del informe (tabla, tendencia, heatmap, comparativo, alertas)
│   ├── acu_pdf.py                           # NUEVO — export PDF con marca de agua
│   └── acu_ia.py                            # NUEVO — prompt-builder para el servicio de IA existente
├── static/
│   ├── acudiente/                           # NUEVA subcarpeta — JS/CSS del portal
│   │   ├── portal.js                        # buscador + autocomplete
│   │   ├── informe.js                       # Chart.js configs (dona + línea + heatmap + barras)
│   │   └── portal.css                       # estilos del layout minimalista
│   └── uploads/
│       └── acudiente_justificaciones/       # NUEVA — soportes PDF/JPG
└── templates/
    └── acudiente/                           # NUEVA subcarpeta
        ├── base.html                        # layout sin sidebar
        ├── portal.html                      # buscador + tarjetas de aprendices
        ├── informe.html                     # pantalla del informe (mimicking imagen 3)
        ├── justificaciones.html
        ├── cambiar_password.html
        ├── politica_datos.html
        └── partials/
            ├── card_aprendiz.html
            ├── panel_alertas.html
            ├── chart_dona.html
            ├── chart_tendencia.html
            ├── chart_heatmap.html
            └── chart_comparativo.html
```

**Registro de los blueprints en el archivo principal:**

```python
from routes.acudiente     import bp as acu_bp
from routes.acudiente_api import bp as acu_api_bp
app.register_blueprint(acu_bp,     url_prefix="/acudiente")
app.register_blueprint(acu_api_bp, url_prefix="/acudiente/api")
```

---

## 10. Prompt para Antigravity (Gemini 3.1 Pro)

> 🤖 Copiar el bloque completo de abajo y pegarlo en Antigravity. **No requiere adjuntar archivos** (todo el contexto está inline). Diseñado para código de calidad producción, con tests, validaciones y trazabilidad. Entrega dividida en 6 partes con confirmación entre cada una.

```text
ROL DEL AGENTE
--------------
Actúa como un desarrollador senior Full-Stack con 10+ años en Python/Flask,
seguridad OWASP y diseño de UI accesible. Aplica principios SOLID, escribe
código idiomático, documentado en español, con type hints, docstrings estilo
Google y pruebas unitarias mínimas para la lógica de negocio.

CONTEXTO DEL PROYECTO
---------------------
Proyecto: SIGDA - Sistema de Gestión de Fichas SENA (carpeta raíz: sena_fichas4).
Stack: Python 3, Flask (Blueprints), MySQL puro (mysql-connector), Jinja2,
Bootstrap 5, Chart.js, JS vanilla.

Estructura REAL del proyecto (plana por tipo de archivo, NO app-factory):
  sena_fichas4/
    logs/
    migraciones/     <- migraciones SQL
    routes/          <- blueprints (un archivo .py por módulo)
    servicios/       <- lógica de servicio (en español)
    static/          <- CSS/JS/imágenes servidos al navegador
    templates/       <- HTMLs Jinja2
    test_batch/
    venv/
    .env

Roles existentes en `usuarios.rol`: 'superadmin', 'admin', 'instructor'.
Se agrega el nuevo rol 'acudiente'.

Restricción crítica: NO modificar módulos, rutas, servicios ni tablas existentes.
Solo se permite:
  - ALTER a `usuarios` para agregar 'acudiente' al ENUM `rol`.
  - Agregar un branch en el before_request/login existente para redirigir al portal.
  - Extender el formulario "Nuevo administrador" para soportar el rol acudiente
    (agregar campos condicionales SIN romper el flujo actual).

OBJETIVO GLOBAL
---------------
Habilitar un Portal del Acudiente en el que:
  1. Un usuario con rol 'acudiente' al iniciar sesión es redirigido a una
     pantalla única con un buscador (nombre / apellido / número documento).
  2. Solo puede consultar aprendices que estén relacionados con él en la tabla
     `acudiente_aprendiz` con estado 'activo'.
  3. Al buscar (Enter o botón Buscar) y seleccionar un aprendiz, ve el Informe
     de Asistencia (mismo estilo visual del módulo actual):
       - Barra de resumen (Ficha, Total días, Modo, Período).
       - Tabla con conteo por estado (A, CE, SE, INC, LIC, CLM, SFF).
       - Botones: Analizar con IA, Exportar Excel, Exportar PDF, Imprimir.
       - Dona 'Distribución de Asistencia'.
     Además incorpora estas mejoras profesionales:
       - Línea de tendencia mensual (6 meses).
       - Calendario heatmap por día.
       - Comparativo vs promedio de la ficha (anonimizado).
       - Panel de alertas configurables.
       - Subida de justificaciones (PDF/JPG) por inasistencia SE.
       - Análisis con IA en lenguaje empático dirigido al acudiente.
       - Export PDF con marca de agua y trazabilidad.

ENTREGABLES (6 PARTES CON CONFIRMACIÓN)
---------------------------------------
PARTE 1 - Migración SQL
  Archivo: migraciones/20260723_acudiente_module.sql
  Debe contener:
    - ALTER TABLE usuarios MODIFY COLUMN rol ENUM('superadmin','admin','instructor','acudiente') NOT NULL;
    - CREATE TABLE acudiente_aprendiz (relación N:N con estado, parentesco,
      documento_soporte, aprobado_por, timestamps, índices y FKs).
    - CREATE TABLE acudiente_consultas_log (auditoría estructurada).
    - CREATE TABLE acudiente_justificaciones (soportes de inasistencia).
    - CREATE TABLE acudiente_consentimientos (habeas data con versión aceptada).
    - CREATE OR REPLACE VIEW v_acudiente_aprendices_activos.
    - Toda la migración envuelta en transacción (START TRANSACTION / COMMIT).
    - Índices en columnas de búsqueda y join.

PARTE 2 - Auth, decorador y middleware (BLINDAJE DE MENÚ)

  REGLA DE ORO DE ESTA PARTE:
  ---------------------------
  Cuando un usuario con rol 'acudiente' inicia sesión, el sistema debe mostrar
  SOLO UN MENÚ: 'Buscar mi Aprendiz'. Nada más. Cero sidebar, cero enlaces a
  otros módulos, cero acceso a /fichas, /aprendices, /documentos, /asistencia,
  /reportes, /usuarios, /admin, /configuracion ni a ninguna otra ruta del
  sistema. Cualquier intento de navegar manualmente a otra URL debe
  redirigirlo automáticamente a /acudiente/portal y registrar el intento en el
  log.

  Archivos:
    - servicios/acu_auth.py:
        * @acudiente_required decorator (verifica sesión + rol='acudiente').
        * verificar_pertenencia(usuario_id, aprendiz_id) -> bool.
        * enmascarar_documento(num) -> '10245*****53'.
        * WHITELIST_ACUDIENTE = tupla de endpoints permitidos
          ('acudiente.', 'acudiente_api.', 'auth.logout', 'auth.login', 'static').
    - Modificación mínima al before_request global existente para forzar que
      cualquier acudiente que intente acceder a otras rutas sea redirigido a
      /acudiente/portal. Registrar cada intento con logger.warning con IP,
      user_id y ruta intentada.
    - Modificación mínima al login existente para redirigir según rol
      (acudiente -> /acudiente/portal; otros -> flujo actual sin cambios).

  Requisitos:
    - Nunca devolver 403 si el acudiente no es dueño de un aprendiz; devolver 404
      para no filtrar existencia.
    - Timeout de sesión de 20 minutos para acudiente.
    - Los endpoints AJAX de otros módulos (ej. /api/fichas, /api/aprendices,
      /api/documentos) deben responder 403 si la sesión es rol='acudiente',
      NO redirigir (para que no confundan a las llamadas fetch).
    - Verificar que el layout de acudiente NO haga {% extends 'base.html' %}
      ni {% include 'sidebar.html' %} del sistema principal.

  Prueba manual obligatoria al terminar la Parte 2:
    1. Loguearse como acudiente y verificar que SOLO se ve el buscador y NO
       aparece el sidebar del sistema.
    2. Escribir manualmente /fichas en la URL -> debe redirigir a
       /acudiente/portal.
    3. Escribir /admin, /aprendices, /documentos -> debe redirigir igual.
    4. Loguearse como instructor -> el sidebar completo debe seguir funcionando
       sin cambios.

PARTE 3 - Modelos y servicios de dominio
  Archivos:
    - servicios/acu_models.py:
        * listar_aprendices_de_acudiente(usuario_id) -> List[Dict]
        * buscar_aprendices_de_acudiente(usuario_id, q) -> List[Dict]
            (LIKE parametrizado sobre nombres, apellidos, numero_documento;
             siempre restringido a v_acudiente_aprendices_activos)
        * obtener_aprendiz_si_pertenece(usuario_id, aprendiz_id) -> Optional[Dict]
        * log_consulta(usuario_id, aprendiz_id, accion, fecha_ini, fecha_fin, request)
        * crud de acudiente_justificaciones
        * registrar_consentimiento(usuario_id, version)
    - servicios/acu_informe.py:
        * generar_informe(aprendiz_id, fecha_ini, fecha_fin) -> Dict con:
            - resumen: {total_dias, por_estado: {A, CE, SE, INC, LIC, CLM, SFF},
              porcentaje_asistencia}
            - tabla: filas del detalle
            - tendencia_mensual: [{mes, A, CE, SE, ...}]
            - heatmap: {'YYYY-MM-DD': 'A'|'CE'|'SE'|...}
            - comparativo_ficha: {aprendiz: {...}, promedio_ficha: {...}}
            - alertas: [{nivel, mensaje, codigo}]
        * calcular_alertas(resumen) -> List[Dict] con reglas configurables.
    - servicios/acu_pdf.py:
        * generar_pdf(informe, aprendiz, acudiente, request) -> bytes
          con encabezado SENA, marca de agua diagonal 'CONFIDENCIAL - Uso
          exclusivo del acudiente autorizado', pie con IP, timestamp, ID de
          consulta. Usar la librería PDF ya presente en el proyecto (weasyprint
          o reportlab). Si no existe, proponer weasyprint.
    - servicios/acu_ia.py:
        * construir_prompt(aprendiz, resumen, tendencia) -> str empático para
          el servicio de IA existente. Devolver el texto del resumen.

  Todos los queries SQL deben usar parámetros (%s), nunca f-strings.
  Escribir 5-8 tests unitarios en tests/test_acu_informe.py para las
  funciones puras (generar_informe con fixtures, calcular_alertas).

PARTE 4 - Blueprints y rutas (con AUTO-LOAD inteligente)

  REGLA UX DE ESTA PARTE:
  -----------------------
  Modificar el login existente para que, al autenticar un usuario con
  rol='acudiente', consulte cuántos aprendices tiene asociados y aplique:
    - 0 aprendices  -> redirect a /acudiente/portal (mensaje amigable).
    - 1 aprendiz    -> redirect DIRECTO a /acudiente/aprendiz/<id> (salta el
                       portal). La página auto-genera el informe del mes
                       actual al cargar (sin click manual en 'Generar').
    - 2+ aprendices -> redirect a /acudiente/portal (tarjetas + buscador).
  El botón 'Cambiar de aprendiz' aparece en el header del informe solo si el
  acudiente tiene 2+ aprendices.

  Archivos:
    - routes/acudiente.py (Blueprint 'acudiente', url_prefix='/acudiente'):
        * GET  /portal                          -> render portal.html
                                                    (buscador + tarjetas si
                                                    hay 2+ aprendices; si hay
                                                    0, mensaje amigable)
        * GET  /aprendiz/<int:aid>              -> render informe.html
                                                    (endpoint name:
                                                    'acudiente.informe_aprendiz')
                                                    Verifica pertenencia y
                                                    pasa un flag
                                                    `auto_generar=True` +
                                                    `mostrar_boton_cambiar=
                                                    (len(aprendices)>1)` al
                                                    template.
        * GET  /aprendiz/<int:aid>/informe/pdf  -> descarga PDF
        * GET  /aprendiz/<int:aid>/informe/excel-> descarga XLSX (openpyxl)
        * GET  /justificaciones                 -> historial
        * POST /perfil/cambiar-password         -> cambio en primer login
        * GET  /politica-datos                  -> política
    - routes/acudiente_api.py (Blueprint 'acudiente_api', url_prefix='/acudiente/api'):
        * GET  /buscar?q=<>                     -> JSON autocomplete
        * POST /aprendiz/<int:aid>/informe      -> JSON del informe
        * POST /aprendiz/<int:aid>/analizar-ia  -> JSON con resumen IA
        * POST /aprendiz/<int:aid>/justificacion (multipart) -> guarda y notifica
    - Registro en el archivo principal (donde se registran los blueprints
      existentes):
        app.register_blueprint(acu_bp,     url_prefix='/acudiente')
        app.register_blueprint(acu_api_bp, url_prefix='/acudiente/api')

  Todas las rutas con @acudiente_required, todas las que reciben <aid> deben
  verificar_pertenencia() y devolver 404 si no.
  Rate-limit sugerido (Flask-Limiter): 60 req/min por acudiente.

PARTE 5 - Templates y assets frontend (LAYOUT AISLADO)

  RECORDATORIO CRÍTICO:
  ---------------------
  El acudiente ve UN SOLO MENÚ: 'Buscar mi Aprendiz'. Estos templates NO deben
  extender del layout base del sistema principal ni incluir el sidebar de
  instructores/admin. Son completamente independientes.

  Archivos:
    - templates/acudiente/base.html:
        Layout minimalista SIN sidebar. NO extiende de templates/base.html del
        sistema principal (crear layout completo desde cero: <html>, <head>,
        <body>). Header con logo SENA, título 'Portal del Acudiente', nombre
        del usuario, botón Salir. NO incluir enlaces a otros módulos. Footer
        con enlace a política de datos. Meta viewport responsive.
    - templates/acudiente/portal.html:
        Buscador prominente (nombre/apellido/documento) con autocomplete,
        tarjetas de aprendices asociados. Estado vacío amigable si no hay
        aprendices.
    - templates/acudiente/informe.html:
        Cabecera con datos del aprendiz, selectores de fecha (default: mes
        actual), botón Generar Informe. Al generar, mostrar la barra azul
        de resumen, tabla, botones (Analizar con IA, Exportar Excel/PDF,
        Imprimir), 4 gráficas (dona, línea, heatmap, comparativo), panel de
        alertas, sección de justificaciones.
    - templates/acudiente/partials/*.html (uno por cada gráfica y por card).
    - templates/acudiente/cambiar_password.html: formulario obligatorio en
      primer login con checkbox de habeas data.
    - templates/acudiente/politica_datos.html: texto de la política.
    - static/acudiente/portal.js: buscador con debounce 300ms, fetch a
      /acudiente/api/buscar, renderizado de resultados, Enter=submit.
    - static/acudiente/informe.js: Chart.js configs para 4 gráficas, fetch
      del informe, actualización reactiva al cambiar fechas, spinner en
      Analizar con IA, upload de justificaciones con preview.
    - static/acudiente/portal.css: variables CSS, tipografía Inter o system,
      colores accesibles WCAG AA.

  Cumplir:
    - Todos los strings en español.
    - Alt text en todas las imágenes/iconos.
    - Roles ARIA en los charts (aria-label describiendo el gráfico).
    - Skip-link 'Ir al contenido principal'.
    - Foco visible en todos los elementos interactivos.
    - Enmascarar número de documento en la UI
      (usar servicios/acu_auth.py:enmascarar_documento).

PARTE 6 - Onboarding y hardening
  Cambios mínimos:
    - Extender el formulario 'Nuevo administrador' existente para que al
      elegir rol='acudiente' aparezcan (con display:none inicial + JS toggle):
        * Multi-select de aprendices (endpoint existente o nuevo que liste
          aprendices para admin).
        * Combo parentesco.
        * Input documento soporte (archivo).
      Al guardar con rol='acudiente':
        * Inserta en usuarios (contraseña temporal, requiere_cambio_password=1).
        * Inserta N filas en acudiente_aprendiz con estado='pendiente' si el
          creador es admin, o 'activo' si es superadmin.
        * Envía correo con contraseña temporal (usar el servicio de correo
          existente si lo hay; si no, dejar función 'enviar_correo' stub
          con TODO).
    - Añadir a settings/config global (o crear si no existe):
        RATELIMIT_STORAGE_URL, ACUDIENTE_SESSION_MINUTES=20,
        ACUDIENTE_MAX_JUSTIFICACIONES_MB=5.
    - Añadir cabeceras de seguridad al blueprint acudiente (X-Frame-Options,
      Content-Security-Policy estricta para /acudiente/*).
    - Añadir migración auxiliar si la columna requiere_cambio_password no
      existe en usuarios.

CRITERIOS DE ACEPTACIÓN (validar antes de entregar cada parte)
--------------------------------------------------------------
- La app arranca sin errores tras aplicar la migración.
- REGLA DE ORO: un acudiente logueado ve UN SOLO MENÚ ('Buscar mi Aprendiz')
  y NADA MAS. No ve sidebar, no ve enlaces a otros módulos, no puede navegar
  a /fichas, /aprendices, /documentos, /asistencia, /reportes, /usuarios,
  /admin, /configuracion ni ninguna otra ruta del sistema.
- AUTO-LOAD: si el acudiente tiene 1 solo aprendiz asociado, al iniciar
  sesión va DIRECTO al informe del aprendiz con el mes actual precargado
  (sin pasar por el portal ni hacer clicks). Si tiene 2+ aprendices, ve el
  portal con tarjetas para elegir. Si tiene 0, ve mensaje amigable con
  contacto a coordinación.
- El botón 'Cambiar de aprendiz' aparece en el header del informe solo si el
  acudiente tiene 2 o más aprendices asociados.
- Un acudiente logueado NO puede acceder a /instructores, /fichas, /aprendices,
  ni a ningún módulo existente; siempre lo redirige a /acudiente/portal.
- Escribir manualmente una URL de otro módulo en la barra del navegador
  siempre lo devuelve al portal (verificado con al menos 3 rutas).
- El acudiente solo ve aprendices que le pertenecen; buscar por documento
  ajeno devuelve lista vacía (no 403).
- Los charts renderizan correctamente con datos reales y con dataset vacío
  (mostrar mensaje 'Sin datos en el período seleccionado').
- Todas las consultas están parametrizadas (0 riesgo SQL injection).
- El PDF se descarga con marca de agua y con los datos correctos.
- Los tests unitarios pasan (pytest tests/test_acu_informe.py).
- Zero cambios de comportamiento en los módulos existentes (probar login como
  instructor/admin/superadmin y validar que el flujo actual sigue intacto).
- Ningún string en inglés visible al usuario final.
- Todos los archivos nuevos con encoding UTF-8 y saltos LF.

ENTREGA POR PARTES
------------------
Produce las 6 partes en el ORDEN listado. Al terminar cada parte:
  1. Muestra el diff de los archivos creados/modificados.
  2. Resume qué se probó y cómo probarlo manualmente en 3 pasos.
  3. Espera mi confirmación (yo diré 'ok, sigue') antes de pasar a la
     siguiente parte.

ESTILO DE CÓDIGO
----------------
- Formateado con black --line-length 100.
- isort para imports.
- Type hints en todas las funciones públicas.
- Docstrings estilo Google en funciones no triviales.
- Nombres de variables y funciones en español, salvo términos técnicos
  universalmente conocidos (id, url, json, request).
- Sin comentarios obvios; comentar solo el 'por qué', no el 'qué'.
- Manejo de errores con logging estructurado (logger.info/warning/error).
- Nada de print() en producción; usar logger.

EMPIEZA POR LA PARTE 1 Y ESPERA CONFIRMACIÓN.
```

---

## 11. Criterios de aceptación

- ✅ Migración SQL corre sin errores en MySQL 8.x.
- ✅ Un usuario con rol `acudiente` al iniciar sesión ve únicamente el portal (sin sidebar) **si tiene 2+ aprendices** o **si tiene 0 aprendices** asociados.
- ✅ Si el acudiente tiene **1 solo aprendiz** asociado, al iniciar sesión va **directo al informe** del aprendiz (auto-load, mes actual precargado, sin pasar por el portal).
- ✅ El botón *"← Cambiar de aprendiz"* aparece en el header del informe solo si tiene 2+ aprendices.
- ✅ El buscador solo devuelve aprendices asociados y con `estado='activo'`.
- ✅ Búsqueda por nombre, apellido o número de documento funciona con `LIKE` parametrizado.
- ✅ Enter en el buscador dispara la búsqueda igual que el botón.
- ✅ El informe replica el layout de la tercera imagen + 4 gráficas nuevas + panel de alertas + justificaciones.
- ✅ El acudiente NO puede acceder a ninguna otra ruta del sistema; middleware lo redirige.
- ✅ Intentar `/acudiente/aprendiz/<id_ajeno>` devuelve 404, no 403.
- ✅ Cada consulta queda registrada en `acudiente_consultas_log` con IP y user-agent.
- ✅ PDF se genera con marca de agua y encabezado institucional.
- ✅ Análisis IA genera resumen en lenguaje empático dirigido al acudiente.
- ✅ Tests unitarios de `acu_informe.py` pasan (`pytest`).
- ✅ Cero cambios de comportamiento en módulos existentes (probar login como `instructor` y `admin`).
- ✅ Formulario "Nuevo administrador" ahora acepta rol `acudiente` con campos condicionales.
- ✅ Contraseña temporal enviada por correo al crear el acudiente; obligatorio cambiarla en el primer login.
- ✅ Checkbox de habeas data marcado y registrado en `acudiente_consentimientos`.
- ✅ Rate-limiting activo (60 req/min).
- ✅ Todos los strings en español, accesibilidad WCAG AA.

---

## 📌 Cómo usar este archivo mañana

1. Abre **Antigravity** y selecciona el modelo **Gemini 3.1 Pro**.
2. Pega el bloque completo de la **sección 10** (el prompt).
3. Cuando el agente termine la **Parte 1 (Migración SQL)**, pruébala en tu MySQL local antes de escribir `ok, sigue`.
4. Repite para cada una de las 6 partes.
5. Al final, un `admin`/`superadmin` puede crear el primer acudiente desde el formulario "Nuevo administrador" (extendido en la Parte 6).

**Tiempo estimado total:** 4-6 horas de implementación asistida + 1-2 h de pruebas.
