import traceback
from servicios import bam_models
try:
    bam_models.crear_plantilla('test', 'test.xlsx', 'hoja', 'grupal', 5, 1)
    print('OK')
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
