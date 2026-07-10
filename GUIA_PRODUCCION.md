# Guía de Arquitectura y Ciberseguridad para Producción

Este documento detalla las configuraciones y requerimientos para desplegar el aplicativo "Gestión de Fichas SENA" en un entorno de **producción real**, cumpliendo con estándares profesionales de ciberseguridad.

## 1. Servidor WSGI para Producción (Waitress)
*   **Problema:** En desarrollo se usa `app.run()`. Esto es inseguro y no soporta tráfico real.
*   **Implementación:** Se ha configurado **Waitress** (el estándar WSGI para Windows).
*   **Cómo ejecutar en Producción:** En lugar de `python app.py`, en el servidor debes correr:
    ```bash
    python run_production.py
    ```

## 2. Seguridad en Base de Datos (Muy Importante)
*   **Problema:** Usar el usuario `root` de MySQL expone todas las bases de datos del servidor si la app es comprometida.
*   **Qué debes hacer en el servidor:** 
    Debes crear un usuario restrictivo ejecutando esto en tu MySQL:
    ```sql
    CREATE USER 'sena_app_user'@'localhost' IDENTIFIED BY 'contraseña_segura_aqui';
    GRANT SELECT, INSERT, UPDATE, DELETE ON gestion_fichas.* TO 'sena_app_user'@'localhost';
    FLUSH PRIVILEGES;
    ```
    Luego, actualiza tu archivo `.env` en producción con estas credenciales.

## 3. Certificado SSL / HTTPS y Servidor Proxy
*   Waitress debe estar detrás de un Proxy Inverso (como **IIS** o **Nginx**) que maneje el certificado SSL (HTTPS).
*   Una vez tengas HTTPS configurado en el servidor, asegúrate de añadir esta variable en tu `.env`:
    ```env
    SESSION_COOKIE_SECURE=True
    ```
    Esto encriptará las cookies de sesión de los administradores.

## 4. Protección Contra Ataques de Fuerza Bruta (DDoS)
*   Se ha implementado `Flask-Limiter` en el sistema.
*   La ruta de `/login` está protegida para aceptar máximo **10 peticiones por minuto** por IP, evitando que programas automatizados adivinen contraseñas.
*   Existe un límite global de 200 peticiones al día por usuario para evitar saturación de recursos.

## 5. Archivo de Entorno (`.env`)
*   Asegúrate de que en el servidor de producción el archivo `.env` tenga estrictamente:
    ```env
    FLASK_DEBUG=False
    FLASK_ENV=production
    ```
    Esto apagará el modo "Debug" y evitará que se muestre código fuente en pantalla si ocurre un error.

---
**Nota Final:** El código actual de la aplicación ya cuenta con consultas SQL parametrizadas (anti SQL-Injection) y protección CSRF, por lo que a nivel de programación la aplicación es robusta. Siguiendo esta guía de infraestructura, estará 100% lista para producción.
