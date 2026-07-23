import os
import mysql.connector
from models import get_connection

def run_migration():
    conn = get_connection()
    cur = conn.cursor()
    with open('migraciones/20260723_acudiente_module.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Remove START TRANSACTION and COMMIT for multiple statement execution with mysql.connector if needed
    # Or just execute it using cur.execute(sql, multi=True)
    try:
        results = cur.execute(sql, multi=True)
        for res in results:
            print("Executed:", res.statement)
        conn.commit()
        print("Migration executed successfully.")
    except Exception as e:
        print("Error executing migration:", e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
