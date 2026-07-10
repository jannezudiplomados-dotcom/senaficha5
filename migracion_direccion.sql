-- ============================================
-- MIGRACION: agregar el campo Direccion a una base de datos EXISTENTE
-- Ejecuta esto SOLO si ya tenias la base creada antes de esta version.
-- (Si vas a crear la base desde cero con database.sql, NO necesitas esto.)
-- ============================================
USE sena_fichas4;

ALTER TABLE usuarios
    ADD COLUMN direccion VARCHAR(255) NULL AFTER telefono;
