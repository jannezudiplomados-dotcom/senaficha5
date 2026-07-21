import sys
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sena_fichas4"
)
cursor = db.cursor(dictionary=True)
cursor.execute("SELECT * FROM fichas")
fichas = cursor.fetchall()
for f in fichas:
    cursor.execute("SELECT count(*) as c FROM usuarios WHERE ficha_id=%s", (f['id'],))
    count = cursor.fetchone()['c']
    print(f"Ficha {f['id']} ({f.get('numero', '')}): {count} aprendices")
