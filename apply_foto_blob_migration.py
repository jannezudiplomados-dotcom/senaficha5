import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sena_fichas4"
)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE usuarios MODIFY foto LONGTEXT NULL;")
    print("Columna foto modificada a LONGTEXT en la tabla usuarios.")
except Exception as e:
    print("Error:", e)

conn.commit()
cur.close()
conn.close()
