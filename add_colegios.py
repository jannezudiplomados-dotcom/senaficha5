import mysql.connector
from config import Config

def migrar_colegios():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )
        cur = conn.cursor()
        
        print("Creando tabla colegios...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS colegios (
            idcolegio INT AUTO_INCREMENT PRIMARY KEY,
            nombre_colegio VARCHAR(200) NOT NULL,
            descripcion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)
        
        print("Añadiendo columna colegio_id a fichas...")
        try:
            cur.execute("ALTER TABLE fichas ADD COLUMN colegio_id INT DEFAULT NULL;")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                print("La columna colegio_id ya existe en fichas.")
            else:
                raise err
                
        print("Añadiendo foreign key a fichas...")
        try:
            cur.execute("ALTER TABLE fichas ADD CONSTRAINT fk_ficha_colegio FOREIGN KEY (colegio_id) REFERENCES colegios(idcolegio) ON DELETE SET NULL;")
        except mysql.connector.Error as err:
            if err.errno in (1061, 1826, 1050, 1005):
                print("La llave foránea ya existe o hubo un error manejable.")
            else:
                # 1022: duplicate, 1061: duplicate key name
                print(f"Error (quizás ya existe): {err}")
                
        conn.commit()
        print("Migración completada con éxito.")
    except Exception as e:
        print(f"Error en la migración: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

if __name__ == "__main__":
    migrar_colegios()
