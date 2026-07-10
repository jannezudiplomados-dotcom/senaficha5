"""
Script de migracion: convierte las contrasenas SHA-256 existentes a hashes seguros (werkzeug).

Como SHA-256 es una funcion de un solo sentido, NO se puede revertir el hash.
Este script permite resetear las contrasenas de los administradores existentes.

Uso:
    python migrate_passwords.py

Prerequisitos:
    - pip install mysql-connector-python werkzeug python-dotenv
    - Variables de entorno o archivo .env configurado
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import mysql.connector
from werkzeug.security import generate_password_hash


def main():
    print("=" * 50)
    print("  Migracion de contrasenas SHA-256 -> werkzeug")
    print("=" * 50)

    # Conectar a la base de datos
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', 3306)),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'sena_fichas4'),
            charset='utf8mb4'
        )
    except mysql.connector.Error as e:
        print(f"Error de conexion: {e}")
        sys.exit(1)

    cursor = conn.cursor(dictionary=True)

    # 1. Ampliar la columna password_hash si es necesario
    print("\n1. Verificando columna password_hash...")
    cursor.execute("""
        SELECT CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'admin' AND COLUMN_NAME = 'password_hash'
    """, (os.environ.get('DB_NAME', 'sena_fichas4'),))
    col_info = cursor.fetchone()

    if col_info and col_info['CHARACTER_MAXIMUM_LENGTH'] < 255:
        print("   -> Ampliando columna password_hash a VARCHAR(255)...")
        cursor.execute("ALTER TABLE admin MODIFY COLUMN password_hash VARCHAR(255) NOT NULL")
        conn.commit()
        print("   -> Columna ampliada correctamente.")
    else:
        print("   -> Columna ya tiene el tamano correcto.")

    # 2. Listar administradores
    cursor.execute("SELECT id, username, nombre, password_hash FROM admin")
    admins = cursor.fetchall()

    if not admins:
        print("\nNo hay administradores en la base de datos.")
        cursor.close()
        conn.close()
        return

    print(f"\n2. Se encontraron {len(admins)} administrador(es):\n")
    for a in admins:
        hash_type = "SHA-256" if len(a['password_hash']) == 64 else "werkzeug"
        print(f"   ID: {a['id']} | Usuario: {a['username']} | Nombre: {a['nombre']} | Hash: {hash_type}")

    # 3. Preguntar si desea migrar
    print("\n3. Migracion de contrasenas")
    print("   NOTA: Las contrasenas SHA-256 no se pueden revertir.")
    print("   Debera ingresar una nueva contrasena para cada administrador.\n")

    respuesta = input("   Desea continuar? (s/n): ").strip().lower()
    if respuesta != 's':
        print("   Migracion cancelada.")
        cursor.close()
        conn.close()
        return

    migrados = 0
    for a in admins:
        # Solo migrar los que tienen hash SHA-256 (64 caracteres hex)
        if len(a['password_hash']) == 64:
            print(f"\n   Administrador: {a['username']} ({a['nombre']})")
            nueva = input(f"   Nueva contrasena para '{a['username']}' (Enter para 'admin123'): ").strip()
            if not nueva:
                nueva = 'admin123'

            nuevo_hash = generate_password_hash(nueva)
            cursor.execute("UPDATE admin SET password_hash = %s WHERE id = %s", (nuevo_hash, a['id']))
            conn.commit()
            migrados += 1
            print(f"   -> Contrasena actualizada correctamente.")
        else:
            print(f"\n   Administrador: {a['username']} - Ya usa formato werkzeug, omitido.")

    print(f"\n{'=' * 50}")
    print(f"  Migracion completada: {migrados} contrasena(s) actualizada(s)")
    print(f"{'=' * 50}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
