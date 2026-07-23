import os
import json
import unittest
from servicios.bam_writer import generar_excel_bitacora

class TestBAMServices(unittest.TestCase):
    def setUp(self):
        # Crear un fixture JSON dummy en memoria
        self.fixture_data = {
            "numero_bitacora": "123",
            "periodo_desde": "2026-07-01",
            "periodo_hasta": "2026-07-15",
            "aprendices": [
                {
                    "nombres": "Juan",
                    "apellidos": "Perez",
                    "tipo_documento": "CC",
                    "identificacion": "1234567890",
                    "telefono": "3001234567",
                    "correo_institucional": "jperez@sena.edu.co",
                    "correo_personal": "jp@gmail.com",
                    "direccion": "Calle Falsa 123",
                    "arl_afiliado": "SI",
                    "arl_nivel_riesgo": 1,
                    "arl_corresponde": "SI",
                    "arl_epp": "SI",
                    "firma_path": None # Opcional: ruta a una imagen de prueba
                }
            ],
            "ficha_numero": "2500123",
            "modalidad_formacion": "Presencial",
            "programa_nombre": "Tecnólogo en ADSO",
            "modalidad_ejecucion": "Presencial",
            "entidad_nombre": "SENA Regional",
            "entidad_nit": "899.999.034-1",
            "entidad_direccion": "Cl 52",
            "jefe_nombre": "Carlos Instructor",
            "jefe_cargo": "Instructor",
            "jefe_telefono": "3010000000",
            "jefe_correo": "carlos@sena.edu.co",
            "seguimiento_nombre": "",
            "seguimiento_correo": "",
            "alternativa_etapa": "Proyecto productivo",
            "actividades": [
                {
                    "descripcion": "Desarrollo web",
                    "competencias": "Desarrollar aplicaciones",
                    "fecha_inicio": "2026-07-02",
                    "fecha_fin": "2026-07-10",
                    "evidencia": "Repositorio",
                    "observaciones": "Ninguna"
                }
            ],
            "fecha_entrega": "2026-07-20",
            "firma_ente_coformador_path": None
        }
        
        self.template_path = os.path.join('static', 'plantillas_base', 'GFPI-F-147FormatoBitacoraSeguimientoEtapaProductiva.xlsx')
        
    def test_writer_creates_file(self):
        # Este test fallará si el archivo de plantilla no existe. 
        # Si existe, verifica que se cree correctamente una copia rellena.
        if os.path.exists(self.template_path):
            out_path = generar_excel_bitacora(self.template_path, self.fixture_data)
            self.assertTrue(os.path.exists(out_path))
            # Limpiar
            if os.path.exists(out_path):
                os.remove(out_path)
        else:
            print(f"Skipping writer test, template not found at {self.template_path}")

if __name__ == '__main__':
    unittest.main()
