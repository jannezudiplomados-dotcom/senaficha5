import os
import logging
from waitress import serve
from app import app
from config import Config

if __name__ == '__main__':
    # Asegurarnos de que el entorno este en modo produccion
    os.environ['FLASK_DEBUG'] = '0'
    os.environ['FLASK_ENV'] = 'production'
    
    # Configurar el logging de Waitress
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)

    print(f"Iniciando el servidor Waitress en produccion en http://127.0.0.1:8000")
    print(f"Base de datos: {Config.DB_HOST} -> {Config.DB_NAME}")
    
    # Ejecutar Waitress (bind a 127.0.0.1 esperando que un proxy inverso exponga a internet)
    serve(app, host='127.0.0.1', port=8000, threads=6)
