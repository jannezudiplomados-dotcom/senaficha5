import models
import logging

try:
    models.init_pool()
    conn = models.get_connection()
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE plantillas ADD COLUMN programa_id INT AFTER descripcion")
    cursor.execute("ALTER TABLE plantillas ADD CONSTRAINT fk_plantilla_programa FOREIGN KEY (programa_id) REFERENCES programas(id) ON DELETE CASCADE")
    cursor.execute("ALTER TABLE plantillas ADD INDEX idx_plantilla_programa (programa_id)")
    conn.commit()
    cursor.close()
    conn.close()
    print("Migration applied successfully.")
except Exception as e:
    print("Migration error:", e)
