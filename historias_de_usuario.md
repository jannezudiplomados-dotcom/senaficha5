# Historias de Usuario - SIGDA (Sistema de Gestión de Fichas y Aprendices)

A continuación se presentan las historias de usuario principales que componen el sistema, estructuradas con sus respectivos criterios de aceptación.

---

## 1. Módulo de Autenticación y Autorización

### HU-01: Iniciar sesión en el sistema
**Como** usuario del sistema (superadmin, admin o instructor).
**Quiero** ingresar mis credenciales en una pantalla de login.
**Para** acceder al panel de control y a las funciones permitidas según mi rol.

**Criterios de Aceptación:**
- Dado que el usuario está en la pantalla de login, cuando ingresa un `username` y `password` correctos, entonces el sistema debe redireccionarlo al Panel de Control (Dashboard).
- Si las credenciales son incorrectas, el sistema debe mostrar un mensaje flash indicando "Error en login".
- El sistema debe guardar el rol y (si aplica) el `programa_id` del usuario en la sesión (`session`).

### HU-02: Restricción de acceso según roles
**Como** administrador del sistema.
**Quiero** que los instructores tengan un acceso restringido.
**Para** garantizar la seguridad y privacidad de la información que no les corresponde.

**Criterios de Aceptación:**
- Si un usuario ingresa con rol de `instructor`, en el menú lateral solo deben ser visibles las pestañas de **Panel** y **Documentos**.
- Las pestañas de Programas, Fichas, Aprendices, Colegios, Plantillas y Administradores deben estar ocultas para el instructor.
- Si el instructor es redirigido o intenta acceder por URL directa a un módulo no autorizado, el sistema debe bloquear el acceso o no mostrar información.

---

## 2. Módulo de Gestión de Administradores

### HU-03: Gestión de usuarios administrativos (CRUD)
**Como** superadmin.
**Quiero** poder crear, leer, actualizar y eliminar usuarios administrativos.
**Para** controlar quién tiene acceso al sistema y bajo qué rol.

**Criterios de Aceptación:**
- El superadmin debe poder ver la lista completa de administradores en una tabla.
- Al crear o editar un administrador, se debe poder seleccionar su rol (`superadmin`, `admin`, `instructor`).
- Si se selecciona el rol `instructor`, se debe permitir asignar un "Programa Asociado" de forma opcional.
- La tabla de lista de administradores debe mostrar una columna con el **Programa** asociado (o "N/A" si no tiene).

---

## 3. Módulo de Gestión Académica (CRUDs Básicos)

### HU-04: Gestión de Programas de Formación y Colegios
**Como** admin o superadmin.
**Quiero** registrar nuevos programas de formación y colegios asociados.
**Para** utilizarlos como base para la clasificación de las fichas y los aprendices.

**Criterios de Aceptación:**
- El sistema debe permitir registrar, editar y listar programas y colegios.
- Los registros deben requerir campos obligatorios como nombre del programa/colegio.
- El sistema debe impedir la eliminación de un programa o colegio si existen registros hijos (fichas/aprendices) dependientes (manejado por llaves foráneas y actualización en cascada/null).

### HU-05: Gestión de Fichas (Grupos)
**Como** admin o superadmin.
**Quiero** poder crear y gestionar fichas (grupos).
**Para** agrupar a los aprendices y tener fechas de inicio/fin claras.

**Criterios de Aceptación:**
- En la creación de la ficha, se debe permitir seleccionar a qué **Programa de Formación** y **Colegio** pertenece (combobox dinámicos).
- Se debe poder asignar un estado a la ficha (ej. Activo, Finalizado).

---

## 4. Módulo de Aprendices y Firmas

### HU-06: Registro de Aprendices con Firma Digital
**Como** admin o superadmin.
**Quiero** poder registrar los datos personales de un aprendiz y capturar su firma.
**Para** guardar un expediente completo y posteriormente generar documentos firmados.

**Criterios de Aceptación:**
- El formulario de registro debe contener campos como identificación, nombres, apellidos, correos y teléfonos.
- El formulario debe incluir un componente de Canvas (pizarra digital) para que el aprendiz dibuje su firma.
- La firma debe ser procesada y almacenada en el servidor como una imagen (`.png`) o en base64 en la base de datos (según implementación actual).
- El aprendiz debe estar asociado obligatoriamente a una Ficha y Programa existentes.

---

## 5. Módulo de Documentos y Plantillas

### HU-07: Subida de Plantillas de Documentos
**Como** admin o superadmin.
**Quiero** poder subir archivos tipo DOCX con variables (ej. `{{ nombre }}`, `{{ identificacion }}`).
**Para** usarlas como molde en la generación automática de certificados.

**Criterios de Aceptación:**
- El sistema debe permitir cargar un archivo `.docx` al servidor.
- El sistema debe almacenar el nombre y la ruta de la plantilla.

### HU-08: Generación de Documentos Individuales
**Como** usuario del sistema (admin, superadmin, o instructor).
**Quiero** generar un documento PDF para un solo aprendiz.
**Para** emitir un certificado o acta de forma inmediata.

**Criterios de Aceptación:**
- El usuario selecciona un aprendiz y la plantilla deseada.
- El sistema debe reemplazar las variables del `.docx` con los datos del aprendiz y su firma digital (si existe).
- El sistema debe convertir el archivo DOCX resultante a PDF y mostrar o descargar el archivo.

### HU-09: Generación Masiva (Por Ficha)
**Como** usuario del sistema.
**Quiero** seleccionar una ficha y una plantilla para generar los documentos de todo el grupo.
**Para** ahorrar tiempo en procesos masivos como graduaciones.

**Criterios de Aceptación:**
- Al seleccionar una ficha, el sistema debe recorrer todos los aprendices activos vinculados a ella.
- Se debe generar un PDF para cada uno de ellos y, al finalizar, agruparlos todos en un archivo `.ZIP` descargable, o fusionarlos en un único PDF consolidado (según configuración).

---

## 6. Módulo del Panel de Control (Dashboard)

### HU-10: Visualización de Estadísticas Generales
**Como** administrador o superadmin.
**Quiero** ver un resumen estadístico (total aprendices, fichas, programas).
**Para** analizar el estado general del sistema de forma gráfica.

**Criterios de Aceptación:**
- El panel debe mostrar tarjetas de KPI (indicadores).
- El panel debe incluir gráficas en Chart.js (ej. aprendices por programa, estado de los aprendices, fichas por colegio).
- Se debe mostrar un registro de "Actividad Reciente" en la parte inferior.

### HU-11: Visualización Filtrada para Instructores
**Como** instructor.
**Quiero** que al entrar a mi Panel de Control, las estadísticas solo reflejen mi programa asignado.
**Para** centrarme únicamente en la información pertinente a mis aprendices y fichas.

**Criterios de Aceptación:**
- Cuando el usuario es instructor, los KPIs y gráficas deben filtrarse pasando el `programa_id` a la base de datos.
- El módulo de "Actividad Reciente" debe estar oculto en su vista.
- La tabla de "Top Fichas" solo debe listar las fichas correspondientes al programa asignado.
