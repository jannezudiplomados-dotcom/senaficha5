-- Migración para añadir columna de firma a los administradores
-- Debe ser idempotente para evitar errores si ya se ejecutó

-- Añadimos la columna firma con el mismo tamaño que la de aprendices
ALTER TABLE admin ADD COLUMN IF NOT EXISTS firma VARCHAR(255) DEFAULT NULL;

-- ==============================================================
-- ROLLBACK: En caso de necesitar revertir este cambio, ejecutar:
-- ALTER TABLE admin DROP COLUMN firma;
-- ==============================================================
