START TRANSACTION;

-- 1. Ampliar ENUM de rol en tabla admin
ALTER TABLE admin
  MODIFY COLUMN rol ENUM('superadmin','admin','instructor','acudiente') NOT NULL,
  ADD COLUMN IF NOT EXISTS requiere_cambio_password TINYINT(1) NOT NULL DEFAULT 0;

-- 2. Tabla relación N:N (Acudiente <-> Aprendiz)
CREATE TABLE acudiente_aprendiz (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id     INT NOT NULL,                -- usuarios.id con rol='acudiente'
  aprendiz_id    INT NOT NULL,                -- usuarios.id (aprendices) o tabla aprendices si existe por separado
  parentesco     ENUM('padre','madre','tutor','abuelo','abuela','tio','tia','otro') NOT NULL DEFAULT 'otro',
  parentesco_otro VARCHAR(60) NULL,           
  telefono_contacto VARCHAR(30) NULL,
  documento_soporte VARCHAR(500) NULL,        
  estado         ENUM('pendiente','activo','revocado') NOT NULL DEFAULT 'pendiente',
  aprobado_por   INT NULL,                    -- usuarios.id (admin o superadmin)
  aprobado_en    DATETIME NULL,
  motivo_revocacion TEXT NULL,
  creado_en      DATETIME DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_acu_apr (usuario_id, aprendiz_id),
  INDEX idx_usuario_estado (usuario_id, estado),
  INDEX idx_aprendiz (aprendiz_id),
  FOREIGN KEY (usuario_id)   REFERENCES admin(id) ON DELETE CASCADE,
  FOREIGN KEY (aprendiz_id)  REFERENCES usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (aprobado_por) REFERENCES admin(id)
);

-- 3. Tabla auditoría estructurada
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
  FOREIGN KEY (usuario_id)  REFERENCES admin(id),
  FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id)
);

-- 4. Tabla justificaciones
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
  FOREIGN KEY (usuario_id)  REFERENCES admin(id),
  FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id),
  FOREIGN KEY (revisado_por) REFERENCES admin(id)
);

-- 5. Tabla consentimientos (Habeas Data)
CREATE TABLE acudiente_consentimientos (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id          INT NOT NULL,
  aceptado_politica_v VARCHAR(20) NOT NULL,
  ip                  VARCHAR(45) NOT NULL,
  creado_en           DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_usuario (usuario_id),
  FOREIGN KEY (usuario_id) REFERENCES admin(id) ON DELETE CASCADE
);

-- 6. Vista activa de conveniencia
CREATE OR REPLACE VIEW v_acudiente_aprendices_activos AS
SELECT
  aa.usuario_id,
  ad.nombre      AS acudiente_nombre,
  a.id           AS aprendiz_id,
  a.identificacion AS numero_documento,
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
JOIN admin ad     ON ad.id = aa.usuario_id
JOIN usuarios a   ON a.id = aa.aprendiz_id
JOIN fichas f     ON f.id = a.ficha_id
JOIN programas p  ON p.id = f.programa_id
WHERE aa.estado = 'activo';

COMMIT;
