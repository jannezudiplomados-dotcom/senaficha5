import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sena_fichas4"
)
cur = conn.cursor()

try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS acudientes (
      id INT AUTO_INCREMENT PRIMARY KEY,
      identificacion VARCHAR(30) NULL,
      nombres_completos VARCHAR(200) NOT NULL,
      correo VARCHAR(150) NULL,
      telefono VARCHAR(30) NULL,
      parentesco VARCHAR(50) NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      UNIQUE KEY uq_acudiente_identificacion (identificacion)
    ) ENGINE=InnoDB;
    """)
    print("Tabla acudientes verificada/creada.")
except Exception as e:
    print("Error creando acudientes:", e)

try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN correo_institucional VARCHAR(150) NULL AFTER correo;")
    print("Columna correo_institucional agregada.")
except Exception as e:
    print("correo_institucional:", e)

try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN portafolio_url VARCHAR(500) NULL AFTER firma;")
    print("Columna portafolio_url agregada.")
except Exception as e:
    print("portafolio_url:", e)

try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN acudiente_id INT NULL AFTER direccion;")
    print("Columna acudiente_id agregada.")
except Exception as e:
    print("acudiente_id:", e)

try:
    cur.execute("ALTER TABLE usuarios ADD CONSTRAINT uq_portafolio_url UNIQUE (portafolio_url);")
    print("Restriccion unique portafolio agregada.")
except Exception as e:
    print("unique portafolio:", e)

try:
    cur.execute("ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_acudiente FOREIGN KEY (acudiente_id) REFERENCES acudientes(id) ON DELETE SET NULL;")
    print("FK acudiente agregada.")
except Exception as e:
    print("fk acudiente:", e)

try:
    cur.execute("ALTER TABLE usuarios ADD INDEX idx_usuario_acudiente (acudiente_id);")
    print("Indice acudiente_id agregado.")
except Exception as e:
    print("idx_usuario_acudiente:", e)

conn.commit()
cur.close()
conn.close()
print("Migración de acudientes y correo institucional completada a XAMPP.")
