# Módulo Bitácora Art. Media (GFPI-F-147) — Especificación técnica y prompt para Antigravity

> **Proyecto:** SIGDA — Sistema de Gestión de Fichas SENA  
> **Stack:** Python 3 · Flask (Blueprints) · MySQL (mysql-connector) · Jinja2 · Bootstrap 5 · JS vanilla  
> **Documento oficial base:** `GFPI-F-147` — Versión 05 · Hoja `Formato Bitácora Art. Media`  
> **Objetivo del módulo:** generar el PDF oficial de la bitácora de seguimiento de etapa productiva desde el sistema, sin modificar los módulos existentes.

---

## Tabla de contenidos

1. [Análisis del formato oficial](#1-análisis-del-formato-oficial)
2. [Diseño del módulo (no invasivo)](#2-diseño-del-módulo-no-invasivo)
3. [Modelo de datos (MySQL)](#3-modelo-de-datos-mysql)
4. [Flujo del wizard (UX)](#4-flujo-del-wizard-ux)
5. [Motor de generación de PDF](#5-motor-de-generación-de-pdf)
6. [Mapa de celdas del Excel](#6-mapa-de-celdas-del-excel)
7. [Estructura de archivos esperada](#7-estructura-de-archivos-esperada)
8. [Recomendaciones profesionales de diseño](#8-recomendaciones-profesionales-de-diseño)
9. [🤖 Prompt listo para Antigravity](#9-prompt-listo-para-antigravity)
10. [Criterios de aceptación](#10-criterios-de-aceptación)

---

## 1. Análisis del formato oficial

El archivo `GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx` tiene 4 hojas; el módulo solo trabaja con **`Formato Bitácora Art. Media`** (rango `B1:AA100`, con muchas celdas combinadas).

### 1.1 Encabezado institucional (fijo, no se toca)

- **Código:** `GFPI-F-147` — **Versión:** `05`
- **Proceso:** Gestión de Formación Profesional Integral
- **Nombre:** Formato Bitácora de Seguimiento Etapa Productiva para Aprendices de Articulación con la Educación Media
- **Clasificación de la información:** Pública / Pública Clasificada / Pública Reservada

### 1.2 Bloques que se llenan y origen del dato

| # | Bloque | Campos | Origen del dato |
|---|--------|--------|-----------------|
| 1 | Bitácora N° / Período | N°, Desde, Hasta | Formulario web |
| 2 | Datos del aprendiz (x5) | Nombre, Tipo y N° ID, Contacto tel., Correo institucional, Correo personal, Dirección | **Autocompletado desde BD** al seleccionar aprendiz |
| 3 | Datos del grupo | N° grupo (ficha), Modalidad de formación, Programa, Modalidad de ejecución | Ficha + programa seleccionados; modalidad desde form |
| 4 | Ente co-formador (entidad) | Nombre, NIT, Dirección | **Defaults editables:** `SENA - CGMLTI Regional Distrito Capital` / `899.999.034-1` / `Cl 52 N° 13 65` |
| 5 | Persona encargada (ente co-formador) | Nombre, Cargo, Tel, Correo | **Autocompletado con el instructor logueado** (editable) |
| 6 | Instructor de seguimiento (evaluador) | Nombre, Correo | **En blanco** por defecto (opcional editar) |
| 7 | Alternativa de etapa productiva | Contrato aprendizaje / Contrato vínculo formativo / Monitoria / Proyecto productivo / Vínculo laboral | Radio/selector |
| 8 | Actividades (tabla dinámica) | Descripción, Competencias, Fecha inicio, Fecha fin, Evidencia, Observaciones | Formulario — filas dinámicas |
| 9 | ARL por aprendiz | ¿Afiliado? (SI/NO), Nivel 1-5, ¿Corresponde? (SI/NO), ¿EPP? (SI/NO/NA) | Formulario — una fila por aprendiz |
| 10 | Firmas aprendices 1-5 + Fecha entrega | Imagen PNG por aprendiz | **Firmas guardadas en BD** (canvas → PNG existente) |
| 11 | Firma instructor de seguimiento | — | **Se deja en blanco** |
| 12 | Firma ente co-formador | PNG | Firma del instructor logueado (si tiene guardada) |
| 13 | Nota de autorización + Anexo fotográfico | Texto fijo | Se conserva de la plantilla |

### 1.3 Observaciones críticas del formato

- Las **fechas** vienen tipadas como `datetime` en el Excel → respetar `dd/mm/aa`.
- Las **casillas de alternativa** se marcan con una `X` en la celda correspondiente (ej: `H45` para *Proyecto productivo*).
- La **firma del instructor de seguimiento** queda vacía porque el evaluador firma en otro momento.
- El archivo tiene **muchas celdas combinadas** — con `openpyxl` siempre escribir en la celda superior-izquierda del merge.

---

## 2. Diseño del módulo (no invasivo)

### 2.1 Principios

> ⚠️ **No tocar** módulos ni tablas existentes. Todo vive en un blueprint nuevo `bitacoras_art_media`, con sus propias tablas prefijadas `bam_*` y sus propias plantillas HTML.

- Blueprint independiente: `app/bitacoras_art_media/`
- Prefijo de URL: `/bitacoras-art-media`
- Tablas MySQL nuevas con prefijo `bam_` (no colisionan)
- Reutiliza (**solo lectura**) tablas existentes: `programas`, `fichas`, `aprendices`, `usuarios`
- Nuevo ítem de menú lateral: **📋 Bitácoras Art. Media**
- Roles reutilizados: `superadmin`, `admin`, `instructor`

### 2.2 Submenús propuestos (barra lateral)

```
📋 Bitácoras Art. Media
  ├─ 🆕 Nueva bitácora            (wizard de 6 pasos)
  ├─ 📚 Historial de bitácoras    (listado + filtros + reimpresión)
  ├─ 🗂️  Plantillas               (subir/reemplazar/activar .xlsx)
  └─ ⚙️  Configuración            (datos por defecto del ente co-formador)
```

---

## 3. Modelo de datos (MySQL)

> 🔍 **Integración con el patrón existente:** la tabla `bam_plantillas` incluye la columna `tipo_generacion` (`'individual'` / `'grupal'`) para respetar el mismo filtro que ya usa el módulo de documentos actual (Programa → Ficha → Plantilla). La plantilla oficial GFPI-F-147 se registra con `tipo_generacion='grupal'` porque un mismo documento agrupa hasta 5 aprendices.

```sql
-- Migración: migraciones/20260722_bam_module.sql

CREATE TABLE bam_plantillas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  descripcion TEXT,
  archivo_ruta VARCHAR(500) NOT NULL,   -- .xlsx en static/plantillas_base/ o static/uploads/bam_plantillas/
  hoja_objetivo VARCHAR(100) NOT NULL DEFAULT 'Formato Bitácora Art. Media',
  tipo_generacion ENUM('individual','grupal') NOT NULL DEFAULT 'grupal',
  max_aprendices TINYINT NOT NULL DEFAULT 5,   -- 1 para individual, >1 para grupal
  activa TINYINT(1) DEFAULT 1,
  creado_por INT,
  creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_tipo_activa (tipo_generacion, activa),
  FOREIGN KEY (creado_por) REFERENCES usuarios(id)
);

CREATE TABLE bam_bitacoras (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plantilla_id INT NOT NULL,
  ficha_id INT NOT NULL,
  programa_id INT NOT NULL,
  numero_bitacora VARCHAR(20),
  periodo_desde DATE,
  periodo_hasta DATE,
  modalidad_formacion VARCHAR(50),
  modalidad_ejecucion ENUM('Presencial','Virtual','Mixta') DEFAULT 'Presencial',
  alternativa_etapa ENUM(
    'Contrato aprendizaje','Contrato vínculo formativo',
    'Monitoria','Proyecto productivo','Vínculo laboral'
  ),
  entidad_nombre TEXT,
  entidad_nit VARCHAR(30),
  entidad_direccion TEXT,
  jefe_nombre VARCHAR(200),
  jefe_cargo VARCHAR(150),
  jefe_telefono VARCHAR(30),
  jefe_correo VARCHAR(150),
  seguimiento_nombre VARCHAR(200) NULL,
  seguimiento_correo VARCHAR(150) NULL,
  fecha_entrega DATE,
  estado ENUM('borrador','generada') DEFAULT 'borrador',
  pdf_ruta VARCHAR(500) NULL,
  creado_por INT,
  creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (plantilla_id) REFERENCES bam_plantillas(id),
  FOREIGN KEY (ficha_id)     REFERENCES fichas(id),
  FOREIGN KEY (programa_id)  REFERENCES programas(id),
  FOREIGN KEY (creado_por)   REFERENCES usuarios(id)
);

CREATE TABLE bam_bitacora_aprendices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bitacora_id INT NOT NULL,
  aprendiz_id INT NOT NULL,
  orden TINYINT NOT NULL,                -- 1..5 (aprendiz 1..5 del formato)
  arl_afiliado ENUM('SI','NO') DEFAULT 'SI',
  arl_nivel_riesgo TINYINT DEFAULT 1,    -- 1..5
  arl_corresponde ENUM('SI','NO') DEFAULT 'SI',
  arl_epp ENUM('SI','NO','NA') DEFAULT 'SI',
  UNIQUE KEY uq_bit_orden (bitacora_id, orden),
  FOREIGN KEY (bitacora_id) REFERENCES bam_bitacoras(id) ON DELETE CASCADE,
  FOREIGN KEY (aprendiz_id) REFERENCES aprendices(id)
);

CREATE TABLE bam_bitacora_actividades (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bitacora_id INT NOT NULL,
  orden INT DEFAULT 0,
  descripcion TEXT NOT NULL,
  competencias TEXT,
  fecha_inicio DATE,
  fecha_fin DATE,
  evidencia VARCHAR(150),   -- Documento / Proceso / Producto / Entregable / Otro
  observaciones TEXT,
  FOREIGN KEY (bitacora_id) REFERENCES bam_bitacoras(id) ON DELETE CASCADE
);

CREATE TABLE bam_config (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clave VARCHAR(100) UNIQUE,
  valor TEXT
);

-- Semillas iniciales
INSERT INTO bam_config (clave, valor) VALUES
  ('entidad_nombre',    'Servicio Nacional de Aprendizaje SENA - Centro de Gestión de Mercados, Logística y Tecnologías de la Información - Regional Distrito Capital'),
  ('entidad_nit',       '899.999.034-1'),
  ('entidad_direccion', 'Cl 52 N° 13 65');

-- Registro semilla de la plantilla oficial (grupal, hasta 5 aprendices)
INSERT INTO bam_plantillas
  (nombre, descripcion, archivo_ruta, hoja_objetivo, tipo_generacion, max_aprendices, activa)
VALUES
  ('GFPI-F-147 v05 (oficial) - Bitácora Art. Media',
   'Formato oficial SENA para bitácora de seguimiento de etapa productiva - Articulación con la Educación Media',
   'static/plantillas_base/GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx',
   'Formato Bitácora Art. Media',
   'grupal',
   5,
   1);
```

---

## 4. Flujo del wizard (UX)

> 🔗 **Alineado al patrón existente del módulo de documentos:** los primeros 3 sub-pasos son idénticos al flujo actual (Programa → Ficha → Plantilla) y la plantilla se elige **filtrada por `tipo_generacion='grupal'`**. La bitácora Art. Media aparece en ese filtro porque un documento agrupa hasta 5 aprendices.

| Paso | Título | Contenido |
|------|--------|-----------|
| 1.a | **Programa** | Combo de programas activos (patrón existente) |
| 1.b | **Ficha** | Combo dependiente del programa (patrón existente) |
| 1.c | **Plantilla** | Tabs/combo filtrado por `tipo_generacion` (por defecto 'Grupal'). La plantilla oficial GFPI-F-147 aparece aquí |
| 2 | **Aprendices** | Hasta **5** combobox filtrados por ficha (respetando `max_aprendices` de la plantilla); AJAX autocompleta tipo/N° ID, contacto, correos, dirección y muestra thumbnail de la firma existente |
| 3 | **Datos generales** | N° bitácora, período (desde/hasta), modalidad formación, modalidad ejecución, alternativa de etapa productiva |
| 4 | **Ente co-formador + Instructor de seguimiento** | Entidad prellenada con defaults; persona encargada prellenada con el instructor logueado; evaluador en blanco |
| 5 | **Actividades** | Tabla con `+ Agregar fila`; cada fila: descripción, competencias, fecha inicio, fecha fin, evidencia (select), observaciones |
| 6 | **ARL por aprendiz** | Una fila por aprendiz seleccionado (SI/NO afiliado, nivel 1-5, SI/NO corresponde, SI/NO/NA EPP) |
| — | **Vista previa + Generar PDF** | Resumen final; botón `Generar PDF` → backend rellena el `.xlsx`, exporta a PDF, guarda y descarga |

---

## 5. Motor de generación de PDF

> 💡 **Estrategia recomendada:** usar el `.xlsx` oficial como plantilla, inyectar valores con `openpyxl`, pegar firmas como imágenes en las celdas correspondientes, y convertir a PDF con **LibreOffice headless**:
>
> ```bash
> soffice --headless --convert-to pdf --outdir <tmp> <input.xlsx>
> ```
>
> Esto conserva el diseño exacto del formato SENA.

**Alternativa:** `docxtpl` si prefieren mantener consistencia con el motor documental actual (requiere convertir la hoja a `.docx`).

### 5.1 Reglas de escritura con openpyxl

- Abrir con `data_only=False` para no perder fórmulas/estilos.
- Cuando la celda pertenece a un merge, escribir SIEMPRE en la celda top-left del merge.
- Fechas como `datetime.date` con formato de celda `dd/mm/aa` (no como texto).
- No romper celdas combinadas: usar `ws.cell(row, column).value = ...`.
- Imágenes:

  ```python
  from openpyxl.drawing.image import Image
  img = Image(path_png)
  img.width = 180
  img.height = 60
  ws.add_image(img, "B80")
  ```

---

## 6. Mapa de celdas del Excel

| Campo | Celda(s) |
|-------|----------|
| Bitácora N° | `B11` |
| Período (texto `Desde X hasta Y`) | `E11` |
| Aprendiz 1..5 · Nombre | `B15..B19` |
| Aprendiz 1..5 · Tipo/N° ID | `E15..E19` |
| Aprendiz 1..5 · Contacto tel. | `H15..H19` |
| Aprendiz 1..5 · Correo institucional | `B21..B25` |
| Aprendiz 1..5 · Correo personal | `E21..E25` |
| Aprendiz 1..5 · Dirección | `H21..H25` |
| N° grupo (ficha) | `B27` |
| Modalidad de formación | `C27` |
| Programa de formación | `F27` |
| Modalidad de ejecución | `I27` |
| Entidad · Nombre | `B31` |
| Entidad · NIT | `F31` |
| Entidad · Dirección | `H31` |
| Jefe inmediato · Nombre | `B35` |
| Jefe · Cargo | `D35` |
| Jefe · Teléfono | `F35` |
| Jefe · Correo | `H35` |
| Instructor seguimiento · Nombre | `B39` |
| Instructor seguimiento · Correo | `G39` |
| Alternativa · Contrato aprendizaje | `X` en `C43` |
| Alternativa · Contrato vínculo formativo | `X` en `C47` |
| Alternativa · Monitoria | `X` en `H43` |
| Alternativa · Proyecto productivo | `X` en `H45` |
| Alternativa · Vínculo laboral | `X` en `H47` |
| Actividades (5 filas base) | filas `53, 55, 57, 59, 61` — cols: `B` descripción · `D` competencias · `F` fecha inicio · `G` fecha fin · `H` evidencia · `I` observaciones |
| ARL aprendiz 1..5 · Nombre | `B71..B75` |
| ARL · ¿Afiliado? | `F71..F75` |
| ARL · Nivel riesgo | `G71..G75` |
| ARL · ¿Corresponde? | `H71..H75` |
| ARL · ¿EPP? | `I71..I75` |
| Firma aprendiz 1 (imagen) | ancla `B80` |
| Firma aprendiz 2 | ancla `F80` |
| Firma aprendiz 3 | ancla `B83` |
| Firma aprendiz 4 | ancla `F83` |
| Firma aprendiz 5 | ancla `B86` |
| Fecha entrega bitácora | `H86` |
| Firma instructor de seguimiento | `C92` — **dejar en blanco** |
| Firma ente co-formador (imagen) | ancla `H92` |

---

## 7. Estructura de archivos esperada

> ⚠️ **Estructura real del proyecto SIGDA (sena_fichas4):** es una app Flask **plana por tipo de archivo** (no app-factory con carpetas por módulo). Todo se integra respetando esas carpetas existentes.

```
sena_fichas4/
├── logs/
├── migraciones/                                   # ya existe
│   └── 20260722_bam_module.sql                     # NUEVO (migración del módulo)
├── routes/                                        # ya existe
│   ├── bitacoras_art_media.py                      # NUEVO blueprint (rutas HTML)
│   └── bitacoras_art_media_api.py                  # NUEVO (endpoints AJAX)
├── servicios/                                     # ya existe (en español)
│   ├── bam_models.py                               # NUEVO (CRUD sobre bam_*)
│   ├── bam_writer.py                               # NUEVO (openpyxl → xlsx relleno)
│   └── bam_pdf.py                                  # NUEVO (LibreOffice → pdf)
├── static/                                        # ya existe
│   ├── css/                                        # ya existe
│   ├── firmas/                                     # ya existe
│   ├── fotos/                                      # ya existe
│   ├── generados/                                  # ya existe
│   ├── images/                                     # ya existe
│   ├── js/                                         # ya existe
│   ├── plantillas/                                 # ya existe (plantillas docxtpl actuales)
│   ├── plantillas_base/                            # NUEVA — plantilla oficial del módulo
│   │   └── GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx
│   ├── uploads/                                    # NUEVA — archivos generados
│   │   ├── bam_pdfs/                               # PDFs de bitácoras generados
│   │   ├── bam_plantillas/                         # plantillas subidas vía UI (admins)
│   │   └── bam_tmp/                                # .xlsx temporales de generación
│   └── bitacoras_art_media/                        # NUEVA — assets frontend del módulo
│       ├── wizard.js
│       └── wizard.css
├── templates/                                     # ya existe
│   └── bitacoras_art_media/                        # NUEVA subcarpeta
│       ├── index.html
│       ├── plantillas_list.html
│       ├── plantillas_form.html
│       ├── wizard_paso1.html … wizard_paso6.html
│       ├── preview.html
│       ├── historial.html
│       └── config.html
├── test_batch/                                    # ya existe
├── venv/
└── .env
```

**Reglas de integración:**

- No crear carpetas tipo `app/bitacoras_art_media/`. Todo se ubica dentro de las carpetas existentes (`routes/`, `servicios/`, `templates/`, `static/`, `migraciones/`).
- Los archivos nuevos usan prefijo `bam_` cuando comparten carpeta con archivos de otros módulos (ej. `servicios/bam_writer.py`), y agrupación en subcarpeta cuando la carpeta padre soporta sub-namespacing (ej. `templates/bitacoras_art_media/`, `static/bitacoras_art_media/`).
- La plantilla oficial `.xlsx` va en `static/plantillas_base/` (siguiendo la convención existente del proyecto donde `static/plantillas/`, `static/firmas/`, `static/generados/` también viven en `static/`).
- Los archivos generados (PDFs, temporales, plantillas subidas por UI) viven en `static/uploads/bam_*/`.
- **Nota de seguridad:** al estar en `static/`, los PDFs generados quedan públicamente accesibles por URL directa (`/static/uploads/bam_pdfs/<id>.pdf`). Tu app actual ya tiene ese mismo comportamiento con `static/firmas/` y `static/generados/`, así que no es un problema nuevo — es una decisión de diseño que ya venía. Solo tenlo presente. Si más adelante quieres endurecer la seguridad, se sirven esos PDFs a través de una ruta Flask protegida con `@login_required` (`send_from_directory` con auth), aunque físicamente estén en `static/`.
- El blueprint se registra en el archivo principal de la app (el que hoy hace `app = Flask(__name__)` y registra los demás blueprints).

```python
# En el archivo de arranque (app.py o similar):
from routes.bitacoras_art_media import bp as bam_bp
from routes.bitacoras_art_media_api import bp as bam_api_bp
app.register_blueprint(bam_bp,     url_prefix="/bitacoras-art-media")
app.register_blueprint(bam_api_bp, url_prefix="/bitacoras-art-media/api")
```

---

## 8. Recomendaciones profesionales de diseño

### 8.1 UX / interfaz

- **Wizard con stepper visual** (Bootstrap `nav-pills` numerados) + breadcrumbs.
- **Guardado automático de borrador** cada 30 s con feedback discreto (`Guardado hace 3 s`).
- **Vista previa** antes de generar el PDF con validación en rojo si falta algo.
- Selectores de aprendiz con **búsqueda tipo Select2** por nombre o documento, filtrados por ficha.
- Junto a cada aprendiz elegido, **thumbnail de la firma** (180×60 px) para confirmar visualmente que sí existe.
- Botón `Generar PDF` con **spinner y bloqueo** mientras corre LibreOffice.
- **Tooltips** que expliquen el origen de cada dato (ej. "Este dato viene de la ficha del aprendiz — para modificarlo, edite el módulo Aprendices").

### 8.2 Arquitectura

- Blueprint aislado; servicios en `services/` fáciles de testear sin Flask.
- `bitacora_writer.py` recibe un `dict` tipado y no conoce la BD → testeable con fixture JSON.
- `pdf_converter.py` con `subprocess.run` + timeout de 60 s (o cola ligera para archivos grandes).
- Guardar el `.xlsx` intermedio también (opcional) para auditoría/reimpresión sin re-consultar BD.

### 8.3 Seguridad

- Validar que la plantilla subida sea realmente `.xlsx` (magic bytes con `python-magic`) y que contenga la hoja objetivo.
- Limitar el tamaño de subida (`MAX_CONTENT_LENGTH`).
- Ejecutar LibreOffice en un directorio temporal aislado por request.
- Logs en `log_actividades` para cada creación/edición/generación.
- Todas las rutas con `@login_required` y verificación de rol.
- Protección CSRF global (ya configurada en SIGDA).

### 8.4 Escalabilidad

- `bam_config` permite cambiar entidad/NIT/dirección sin tocar código.
- El campo `hoja_objetivo` en `bam_plantillas` permite en el futuro soportar **otras hojas** (Bitácora Regular, Instructivo, etc.) reutilizando el mismo motor.
- El writer con un **mapa de celdas** como `dict` permite adaptar el módulo si el SENA publica una nueva versión del formato (solo se actualiza el mapa).

### 8.5 Mejoras futuras (no incluidas en el prompt inicial)

- Firma en línea del **instructor de seguimiento** en el mismo canvas.
- Envío del PDF por correo al jefe inmediato al finalizar.
- Panel de estadísticas: bitácoras por ficha/período, alertas de ARL vencida.
- Exportar `.xlsx` además del PDF cuando el SENA pida el archivo editable.

---

## 9. Prompt listo para Antigravity

> 🤖 Copiar todo el bloque siguiente y pegar en Antigravity **junto con el archivo `GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx` adjunto**. Está diseñado para **no tocar** los módulos existentes del SIGDA y para entregarse por partes con confirmación entre cada una.

```text
ARCHIVOS ADJUNTOS
-----------------
Se adjunta el archivo oficial:
  - GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx

Usarlo como PLANTILLA BASE del módulo. Instrucciones estrictas:

1. Ubicación final en el repo:
     static/plantillas_base/GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx
   (dentro de `static/`, siguiendo la convención existente del proyecto donde
    `static/plantillas/`, `static/firmas/`, `static/generados/` también viven en static).
    Mantener el nombre original del archivo tal como lo entrega el SENA.

2. Trabajar SOLO con la hoja "Formato Bitácora Art. Media". No modificar las otras
   hojas (Instrucciones, Hoja1, Instructivo); conservarlas intactas en el archivo
   generado.

3. Nunca sobrescribir el archivo original. El writer siempre debe:
     a) Copiar la plantilla activa (por defecto la oficial GFPI-F-147) a un archivo
        temporal en `static/uploads/bam_tmp/<uuid>.xlsx`.
     b) Abrir la COPIA con openpyxl (data_only=False).
     c) Escribir en la copia.
     d) Convertir la copia a PDF con LibreOffice headless.
     e) Borrar el .xlsx temporal (mantener solo el PDF en static/uploads/bam_pdfs/).

4. En la migración inicial insertar automáticamente un registro semilla en
   `bam_plantillas`:
     nombre='GFPI-F-147 v05 (oficial)'
     archivo_ruta='static/plantillas_base/GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx'
     hoja_objetivo='Formato Bitácora Art. Media'
     activa=1

5. Antes de escribir, verificar:
     if 'Formato Bitácora Art. Media' not in wb.sheetnames:
         raise ValueError('La plantilla no contiene la hoja objetivo')

6. NO alterar el encabezado institucional (filas 1 a 8), la sección legal de ARL
   (filas 64-69), la nota de autorización (fila 94) ni los rótulos preimpresos de
   firmas. Solo escribir en las celdas del MAPA DE CELDAS.

7. Validación adicional para plantillas subidas por admins desde la UI:
     - Verificar magic bytes con python-magic (o zipfile.is_zipfile()).
     - Guardar esas plantillas en static/uploads/bam_plantillas/ con nombre
       plantilla_<id>_<timestamp>.xlsx.
     - No permitir sobrescribir la plantilla oficial en static/plantillas_base/ desde la UI.

8. Fuentes: LibreOffice usará las del sistema. Si el .xlsx usa Calibri/Arial,
   asegurarse de que estén instaladas en el servidor de producción para que el PDF
   conserve la tipografía.

CONTEXTO
--------
Proyecto: SIGDA - Sistema de Gestión de Fichas SENA (carpeta raíz: sena_fichas4).
Stack: Python 3, Flask (Blueprints), MySQL puro (mysql-connector), Jinja2, Bootstrap 5, JS vanilla.

Estructura REAL del proyecto (plana, NO app-factory):
  sena_fichas4/
    logs/
    migraciones/     <- migraciones SQL (en español)
    routes/          <- blueprints (un archivo .py por módulo)
    servicios/       <- lógica de servicio (en español)
    static/          <- CSS/JS/imágenes servidos al navegador
    templates/       <- HTMLs Jinja2
    test_batch/
    venv/
    .env

Restricción crítica: NO modificar rutas, servicios, plantillas ni tablas existentes.
Todo el módulo nuevo debe integrarse en las carpetas existentes usando prefijo `bam_`
y subcarpeta `bitacoras_art_media/` cuando corresponda. Las carpetas nuevas ya fueron
creadas por el usuario y viven DENTRO de static/:
  - static/plantillas_base/                       (plantilla oficial .xlsx)
  - static/uploads/bam_plantillas/                (plantillas subidas vía UI)
  - static/uploads/bam_pdfs/                      (PDFs generados)
  - static/uploads/bam_tmp/                       (.xlsx temporales durante generación)

Esta ubicación es consistente con la convención existente del proyecto
(static/plantillas/, static/firmas/, static/generados/ ya siguen ese patrón).

PATRÓN DE FLUJO EXISTENTE (respetar)
-----------------------------------
La app actual SIGDA usa un flujo estándar para generar documentos:

  Programa  ->  Ficha  ->  Plantilla  ->  (Llenar datos)  ->  Generar PDF

Las plantillas se clasifican por `tipo_generacion`:
  - individual : 1 aprendiz por documento (ej. certificados individuales).
  - grupal     : 1 documento con múltiples aprendices.

La UI de selección de plantilla debe filtrar por `tipo_generacion` (tabs o combo
'Individual' / 'Grupal') igual que el módulo de documentos actual.

ESTA plantilla (GFPI-F-147 Bitácora Art. Media) es tipo_generacion='grupal'
porque un solo documento agrupa 1 a 5 aprendices de la misma ficha.
En `bam_plantillas` la columna `max_aprendices=5` limita cuántos aprendices se
pueden seleccionar en el paso de aprendices.

El wizard del nuevo módulo DEBE arrancar con los mismos 3 sub-pasos del módulo
de documentos actual (Programa -> Ficha -> Plantilla filtrada por 'grupal')
antes de pasar a los pasos específicos de la bitácora.

OBJETIVO
--------
Crear un nuevo Blueprint `bitacoras_art_media` para generar el documento oficial
"GFPI-F-147 - Formato Bitácora de Seguimiento Etapa Productiva para Aprendices de Articulación con la Educación Media"
(hoja "Formato Bitácora Art. Media") en PDF, tomando datos de la plataforma y una plantilla .xlsx cargada por el administrador.

ENTREGABLES
-----------
1. Migración SQL con tablas nuevas (prefijo `bam_`):
   bam_plantillas, bam_bitacoras, bam_bitacora_aprendices, bam_bitacora_actividades, bam_config.
2. Dos blueprints Flask en `routes/`:
     - `routes/bitacoras_art_media.py`       (url_prefix="/bitacoras-art-media")
     - `routes/bitacoras_art_media_api.py`   (url_prefix="/bitacoras-art-media/api")
   Registrarlos en el archivo principal de la app (donde hoy se registran los demás blueprints).
3. Modelos / repositorios (mysql-connector puro, sin ORM) en `servicios/bam_models.py`.
4. Rutas y vistas para:
   - Listar / subir / activar / eliminar plantillas (.xlsx).
   - Wizard de 6 pasos para crear una bitácora (sesión Flask o borrador en BD).
   - Historial de bitácoras (listado, filtros por ficha/programa/fecha, reimprimir PDF).
   - Configuración: datos por defecto del ente co-formador (nombre, NIT, dirección).
5. Endpoints AJAX (alineados al patrón existente Programa → Ficha → Plantilla):
   - GET /bitacoras-art-media/api/programas                  -> programas activos.
   - GET /bitacoras-art-media/api/fichas?programa_id=        -> fichas del programa.
   - GET /bitacoras-art-media/api/plantillas?tipo=grupal&activa=1
                                                             -> plantillas filtradas por tipo_generacion.
   - GET /bitacoras-art-media/api/aprendices?ficha_id=       -> aprendices activos de la ficha.
   - GET /bitacoras-art-media/api/aprendiz/<id>              -> tipo doc, num_doc, tel, correos, dirección, url_firma_png.
6. Servicios de generación en `servicios/`:
   - `servicios/bam_writer.py`: abre la plantilla .xlsx activa con openpyxl, escribe SOLO en la hoja
     "Formato Bitácora Art. Media" en las celdas del mapa (ver abajo). Escribir siempre en la celda superior-izquierda del merge.
   - `servicios/bam_pdf.py`: convierte el .xlsx resultante a PDF con LibreOffice headless
     (`soffice --headless --convert-to pdf --outdir <tmp> <input.xlsx>`). Manejar timeout y limpieza de temporales.
   - Insertar firmas PNG con `openpyxl.drawing.image.Image` y `add_image(img, "B80")` etc., a tamaño estándar (180x60 px).
7. Templates Jinja2 con Bootstrap 5 (stepper, cards, breadcrumbs) en `templates/bitacoras_art_media/`
   (nueva subcarpeta dentro del `templates/` existente). CSS/JS del wizard en `static/bitacoras_art_media/`.
8. Nuevo ítem en el sidebar (extendiendo solo el layout base sin romper otros submenús):
   "📋 Bitácoras Art. Media" con 4 sub-items (Nueva bitácora, Historial, Plantillas, Configuración).
9. Roles reutilizados: superadmin/admin pueden subir plantillas y ver todo; instructor puede crear y ver sus propias bitácoras.
10. Registro en la tabla de auditoría existente (`log_actividades`) para cada creación/edición/generación.

MAPA DE CELDAS (hoja "Formato Bitácora Art. Media")
---------------------------------------------------
- B11: Bitácora N°
- E11: "Desde <dd/mm/aaaa> hasta <dd/mm/aaaa>"
- B15..B19: Nombre aprendiz 1..5
- E15..E19: "<Tipo> <Num>" (p.ej. "CC 1234567890")
- H15..H19: Contacto telefónico
- B21..B25: Correo institucional
- E21..E25: Correo personal
- H21..H25: Dirección de residencia
- B27: Número de grupo (ficha)
- C27: Modalidad de formación
- F27: Programa de formación
- I27: Modalidad de ejecución (Presencial/Virtual)
- B31: Entidad · Nombre        (default configurable en bam_config)
- F31: Entidad · NIT           (default configurable)
- H31: Entidad · Dirección     (default configurable)
- B35: Jefe inmediato · Nombre (default: instructor logueado)
- D35: Cargo del ente co-formador
- F35: Teléfono del ente co-formador
- H35: Correo del ente co-formador
- B39: Instructor de seguimiento · Nombre  (por defecto "")
- G39: Instructor de seguimiento · Correo  (por defecto "")
- Alternativa etapa productiva -> poner "X" en UNA de:
    - C43 Contrato aprendizaje
    - C47 Contrato vínculo formativo
    - H43 Monitoria
    - H45 Proyecto productivo
    - H47 Vínculo laboral
- Actividades: iterar filas 53, 55, 57, 59, 61 (5 filas base). Escribir en:
    * B<r>: descripción
    * D<r>: competencias (viene precargado en la plantilla; sobrescribir SOLO si el usuario lo cambia)
    * F<r>: fecha inicio
    * G<r>: fecha fin
    * H<r>: evidencia
    * I<r>: observaciones
  Si el usuario agrega más filas, insertar filas nuevas conservando estilos.
- ARL por aprendiz (filas 71..75):
    * B71..B75 nombre aprendiz
    * F71..F75 SI/NO afiliado
    * G71..G75 nivel 1..5
    * H71..H75 SI/NO corresponde
    * I71..I75 SI/NO/NA EPP
- Firmas aprendices (insertar imagen PNG en):
    * Aprendiz 1: ancla B80
    * Aprendiz 2: ancla F80
    * Aprendiz 3: ancla B83
    * Aprendiz 4: ancla F83
    * Aprendiz 5: ancla B86
- H86: Fecha entrega bitácora
- Firma instructor de seguimiento: DEJAR EN BLANCO (no insertar imagen en C92)
- Firma ente co-formador: insertar PNG del instructor logueado en ancla H92
  (si no tiene firma guardada, dejar en blanco)

REGLAS DE ESCRITURA CON openpyxl
--------------------------------
- data_only=False al abrir para no perder fórmulas/estilos.
- Cuando la celda pertenece a un merge, escribir SIEMPRE en la celda top-left del merge.
- Fechas como datetime.date con formato de celda "dd/mm/aa" (no como texto).
- No romper celdas combinadas: usar `ws.cell(row, column).value = ...` sobre la celda ancla.
- Imágenes:
    from openpyxl.drawing.image import Image
    img = Image(path_png); img.width = 180; img.height = 60
    ws.add_image(img, "B80")

AUTOCOMPLETADO (comportamiento del wizard)
------------------------------------------
- Paso 1: selects de Programa -> Ficha -> Plantilla (activa por defecto).
- Paso 2: por cada aprendiz seleccionado (1..5), fetch AJAX y rellenar readonly:
  tipo/num_doc, tel, correo institucional, correo personal, dirección + thumbnail de firma.
- Paso 4: prellenar Ente co-formador con `bam_config` (nombre, NIT, dirección),
  y Persona encargada con datos del usuario logueado (nombre, cargo, correo, tel). Todos editables.
- Paso 5: precargar 5 filas de actividades vacías; permitir +Agregar y -Eliminar.
- Paso 6: mostrar los aprendices elegidos con defaults SI / 1 / SI / SI.

SEGURIDAD Y UX
--------------
- Todas las rutas protegidas con `@login_required` y verificación de rol.
- Formularios con protección CSRF (ya configurada globalmente).
- Validaciones server-side: fechas coherentes, mínimo 1 y máximo 5 aprendices, alternativa etapa productiva obligatoria.
- Autoguardado del borrador cada 30 s con AJAX.
- Al generar, mostrar página de "Vista previa" antes de crear el PDF.
- El PDF final se guarda en `uploads/bam_pdfs/<bitacora_id>.pdf` y queda accesible en el Historial.
- Validar la plantilla subida con magic bytes (python-magic) y verificar que contenga la hoja objetivo.
- Limitar tamaño de subida con MAX_CONTENT_LENGTH.

ESTRUCTURA DE ARCHIVOS ESPERADA (adaptada a sena_fichas4)
---------------------------------------------------------
sena_fichas4/
  migraciones/
    20260722_bam_module.sql                       # NUEVO
  routes/
    bitacoras_art_media.py                        # NUEVO blueprint (rutas HTML)
    bitacoras_art_media_api.py                    # NUEVO (endpoints AJAX)
  servicios/
    bam_models.py                                 # NUEVO (CRUD sobre bam_*)
    bam_writer.py                                 # NUEVO (openpyxl -> xlsx)
    bam_pdf.py                                    # NUEVO (LibreOffice -> pdf)
  static/
    plantillas_base/                              # YA CREADA por el usuario
      GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx
    uploads/                                      # YA CREADA por el usuario
      bam_pdfs/                                   # PDFs generados
      bam_plantillas/                             # plantillas subidas vía UI
      bam_tmp/                                    # .xlsx temporales durante generación
    bitacoras_art_media/                          # NUEVA subcarpeta (JS/CSS del módulo)
      wizard.js
      wizard.css
  templates/
    bitacoras_art_media/                          # NUEVA subcarpeta
      index.html
      plantillas_list.html
      plantillas_form.html
      wizard_paso1.html ... wizard_paso6.html
      preview.html
      historial.html
      config.html

Registro del blueprint en el archivo principal (app.py o run.py):
  from routes.bitacoras_art_media import bp as bam_bp
  from routes.bitacoras_art_media_api import bp as bam_api_bp
  app.register_blueprint(bam_bp,     url_prefix="/bitacoras-art-media")
  app.register_blueprint(bam_api_bp, url_prefix="/bitacoras-art-media/api")

CRITERIOS DE ACEPTACIÓN
-----------------------
- Ejecutar la migración y arrancar la app SIN errores.
- Ningún módulo existente cambia su comportamiento visual ni sus rutas.
- Un instructor puede: subir una plantilla (o usar la que suba un admin), crear una bitácora nueva con 3 aprendices,
  y descargar el PDF con el diseño oficial preservado, con las firmas insertadas correctamente.
- La firma del instructor de seguimiento aparece en blanco.
- Todos los strings del código y templates en español.
- Código formateado con black; nombres de variables descriptivos.

ENTREGA POR PARTES (con confirmación entre cada una)
----------------------------------------------------
1) SQL de migración + semillas de bam_config.
2) Blueprint + models + rutas base + registro en app/__init__.py.
3) Servicios (bitacora_writer.py + pdf_converter.py) con tests unitarios básicos usando un fixture JSON.
4) Templates + wizard.js del formulario paso a paso.
5) Extensión del sidebar y ajustes finales de UX (Select2, tooltips, spinner al generar).

Al finalizar cada parte, mostrar el diff propuesto y esperar confirmación antes de continuar con la siguiente.
```

---

## 10. Criterios de aceptación

- ✅ Ejecutar la migración y arrancar la app SIN errores.
- ✅ Ningún módulo existente cambia su comportamiento visual ni sus rutas.
- ✅ Un instructor puede crear una bitácora con 1-5 aprendices y descargar el PDF con el diseño oficial preservado.
- ✅ Las firmas guardadas de los aprendices aparecen insertadas en la posición correcta.
- ✅ La firma del instructor de seguimiento aparece en blanco.
- ✅ Datos por defecto del ente co-formador editables desde `Configuración`.
- ✅ Historial permite reimprimir el PDF sin volver a llenar el formulario.
- ✅ Todo el módulo respeta roles y auditoría del sistema existente.

---

_Última actualización: 22 de julio de 2026 — SIGDA (Sistema de Gestión de Fichas SENA)_
