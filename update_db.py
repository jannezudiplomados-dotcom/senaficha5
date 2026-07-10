import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sena_fichas4"
)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE plantillas ADD COLUMN tipo_generacion ENUM('individual', 'grupal', 'ambos') DEFAULT 'ambos' AFTER programa_id;")
    print("Columna tipo_generacion agregada a la tabla plantillas.")
except Exception as e:
    print(f"Error o la columna ya existe: {e}")

conn.commit()
cur.close()
conn.close()
