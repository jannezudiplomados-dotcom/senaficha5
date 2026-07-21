import models
import logging

try:
    models.init_pool()
    conn = models.get_connection()
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE admin ADD COLUMN firma VARCHAR(255) DEFAULT NULL;")
    conn.commit()
    cursor.close()
    conn.close()
    print("Migration applied successfully: added firma to admin table.")
except Exception as e:
    print("Migration error:", e)
