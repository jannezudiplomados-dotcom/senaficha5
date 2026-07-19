import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sena_fichas4"
)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN foto VARCHAR(255) NULL AFTER firma;")
    print("Columna foto agregada a usuarios.")
except Exception as e:
    print("Error (puede que ya exista):", e)

conn.commit()
cur.close()
conn.close()
