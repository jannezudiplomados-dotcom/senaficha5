import models
import logging

try:
    models.init_pool()
    conn = models.get_connection()
    cursor = conn.cursor()
    
    with open('migraciones/20260722_bam_module.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Split by semicolon and execute each statement
    statements = sql.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Migration 20260722_bam_module.sql applied successfully.")
except Exception as e:
    print("Migration error:", e)
