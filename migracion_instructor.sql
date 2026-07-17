-- Migracion para agregar rol instructor y programa_id a la tabla admin
USE sena_fichas4;

ALTER TABLE admin
MODIFY COLUMN rol ENUM('superadmin','admin','instructor') DEFAULT 'instructor',
ADD COLUMN programa_id INT DEFAULT NULL AFTER rol,
ADD CONSTRAINT fk_admin_programa FOREIGN KEY (programa_id) REFERENCES programas(id) ON DELETE SET NULL,
ADD INDEX idx_admin_programa (programa_id);
