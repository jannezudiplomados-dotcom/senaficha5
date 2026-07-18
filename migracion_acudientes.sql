-- ============================================
-- Migración: Correo institucional, Portafolio y Acudientes
-- Base de datos: sena_fichas4
-- Fecha: 2026-07-18
-- ============================================
USE sena_fichas4;

-- 1) Nuevas columnas en usuarios: correo institucional y portafolio
ALTER TABLE usuarios
  ADD COLUMN correo_institucional VARCHAR(150) NULL AFTER correo,
  ADD COLUMN portafolio_url VARCHAR(500) NULL AFTER firma;

ALTER TABLE usuarios
  ADD CONSTRAINT uq_portafolio_url UNIQUE (portafolio_url);

-- 2) Tabla acudientes (un acudiente puede tener varios aprendices)
CREATE TABLE IF NOT EXISTS acudientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  identificacion VARCHAR(30) NULL,
  nombres_completos VARCHAR(200) NOT NULL,
  correo VARCHAR(150) NULL,
  telefono VARCHAR(30) NULL,
  parentesco VARCHAR(50) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_acudiente_identificacion (identificacion)
) ENGINE=InnoDB;

-- 3) FK usuarios -> acudientes
ALTER TABLE usuarios
  ADD COLUMN acudiente_id INT NULL AFTER direccion,
  ADD CONSTRAINT fk_usuario_acudiente FOREIGN KEY (acudiente_id)
    REFERENCES acudientes(id) ON DELETE SET NULL,
  ADD INDEX idx_usuario_acudiente (acudiente_id);
