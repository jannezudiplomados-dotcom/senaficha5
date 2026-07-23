-- Migración: migraciones/20260722_bam_module.sql

DROP TABLE IF EXISTS bam_config;
DROP TABLE IF EXISTS bam_bitacora_actividades;
DROP TABLE IF EXISTS bam_bitacora_aprendices;
DROP TABLE IF EXISTS bam_bitacoras;
DROP TABLE IF EXISTS bam_plantillas;

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
  FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id)
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
