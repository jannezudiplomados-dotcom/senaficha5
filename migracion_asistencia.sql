-- 1) La tabla `admin` YA tiene la columna `rol` ENUM('superadmin','admin','instructor').
--    No se agrega. Asegura que exista un superadmin (el usuario 'admin' ya lo es):
-- UPDATE admin SET rol='superadmin' WHERE username='admin';

-- 2) Asignación instructor <-> programas
CREATE TABLE IF NOT EXISTS instructor_programas (
  instructor_id INT NOT NULL,
  programa_id   INT NOT NULL,
  PRIMARY KEY (instructor_id, programa_id),
  CONSTRAINT fk_ip_instructor FOREIGN KEY (instructor_id) REFERENCES admin(id) ON DELETE CASCADE,
  CONSTRAINT fk_ip_programa   FOREIGN KEY (programa_id)   REFERENCES programas(id) ON DELETE CASCADE
);

-- 3) Asignación instructor <-> fichas (la hace el superadmin)
CREATE TABLE IF NOT EXISTS instructor_fichas (
  instructor_id INT NOT NULL,
  ficha_id      INT NOT NULL,
  asignado_por  INT NULL,
  asignado_en   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (instructor_id, ficha_id),
  CONSTRAINT fk_if_instructor FOREIGN KEY (instructor_id) REFERENCES admin(id) ON DELETE CASCADE,
  CONSTRAINT fk_if_ficha      FOREIGN KEY (ficha_id)      REFERENCES fichas(id) ON DELETE CASCADE,
  CONSTRAINT fk_if_asignado   FOREIGN KEY (asignado_por)  REFERENCES admin(id)
);

-- 4) Asistencia
CREATE TABLE IF NOT EXISTS asistencias (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  aprendiz_id     INT NOT NULL,
  ficha_id        INT NOT NULL,
  fecha           DATE NOT NULL,
  estado          ENUM('A','CE','SE','INC','LIC','CLM','SFF','RET') NOT NULL,
  observacion     VARCHAR(255) NULL,
  registrado_por  INT NULL,               -- id del instructor que toma la asistencia
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_aprendiz_fecha (aprendiz_id, fecha),
  CONSTRAINT fk_asis_aprendiz FOREIGN KEY (aprendiz_id)    REFERENCES usuarios(id) ON DELETE CASCADE,
  CONSTRAINT fk_asis_ficha    FOREIGN KEY (ficha_id)       REFERENCES fichas(id)   ON DELETE CASCADE,
  CONSTRAINT fk_asis_admin    FOREIGN KEY (registrado_por) REFERENCES admin(id)
);
CREATE INDEX idx_asis_ficha_fecha ON asistencias (ficha_id, fecha);
CREATE INDEX idx_asis_estado ON asistencias (estado);
