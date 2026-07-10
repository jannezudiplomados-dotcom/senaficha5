-- ============================================
-- Migracion: Asociar plantillas a programas
-- Ejecuta este script si ya tenias la base de datos creada
-- ============================================

USE sena_fichas4;

ALTER TABLE plantillas
ADD COLUMN programa_id INT AFTER descripcion;

ALTER TABLE plantillas
ADD CONSTRAINT fk_plantilla_programa FOREIGN KEY (programa_id) REFERENCES programas(id) ON DELETE CASCADE;

ALTER TABLE plantillas
ADD INDEX idx_plantilla_programa (programa_id);
