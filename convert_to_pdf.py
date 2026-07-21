"""
Helper script: converts DOCX/XLSX to PDF using Microsoft Office COM.
Run as a separate process to avoid COM threading issues with Flask.

Usage (Single file): 
  python convert_to_pdf.py --single <input_path> <output_path>

Usage (Batch directory):
  python convert_to_pdf.py --batch <dir_path> <ext>
  (Convierte todos los archivos .<ext> en <dir_path> a .pdf en el mismo <dir_path>)
"""
import sys
import os
import glob
import traceback

def _process_single_docx(abs_in):
    import comtypes.client
    import pythoncom
    pythoncom.CoInitialize()
    word = None
    try:
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        word.DisplayAlerts = 0
        abs_out = abs_in.rsplit('.', 1)[0] + '.pdf'
        doc = word.Documents.Open(abs_in, ReadOnly=True)
        doc.SaveAs(abs_out, FileFormat=17)
        doc.Close(False)
    except Exception as e:
        print(f"Error procesando {abs_in}: {e}", file=sys.stderr)
    finally:
        if word:
            try: word.Quit()
            except: pass
        pythoncom.CoUninitialize()

def batch_convert_docx(directory):
    files = glob.glob(os.path.join(directory, "*.docx"))
    print(f"Encontrados {len(files)} archivos .docx para convertir.")
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(_process_single_docx, files)

def _process_single_xlsx(abs_in):
    import comtypes.client
    import pythoncom
    pythoncom.CoInitialize()
    excel = None
    try:
        excel = comtypes.client.CreateObject('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.Interactive = False
        abs_out = abs_in.rsplit('.', 1)[0] + '.pdf'
        wb = excel.Workbooks.Open(abs_in, UpdateLinks=0, ReadOnly=True)
        wb.ExportAsFixedFormat(0, abs_out)
        wb.Close(False)
    except Exception as e:
        print(f"Error procesando {abs_in}: {e}", file=sys.stderr)
    finally:
        if excel:
            try: 
                excel.Interactive = True
                excel.Quit()
            except: pass
        pythoncom.CoUninitialize()

def batch_convert_xlsx(directory):
    files = glob.glob(os.path.join(directory, "*.xlsx"))
    print(f"Encontrados {len(files)} archivos .xlsx para convertir.")
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(_process_single_xlsx, files)

def main():
    if len(sys.argv) < 3:
        print("Uso: python convert_to_pdf.py [--single <in> <out> | --batch <dir> <ext>]", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    import pythoncom
    pythoncom.CoInitialize()
    
    try:
        if mode == '--batch':
            if len(sys.argv) != 4:
                print("Uso batch: python convert_to_pdf.py --batch <dir> <docx|xlsx>", file=sys.stderr)
                sys.exit(1)
            
            directory = os.path.abspath(sys.argv[2])
            ext = sys.argv[3].lower().strip('.')
            
            if not os.path.isdir(directory):
                print(f"Directorio no encontrado: {directory}", file=sys.stderr)
                sys.exit(1)
                
            if ext == 'docx':
                batch_convert_docx(directory)
            elif ext == 'xlsx':
                batch_convert_xlsx(directory)
            else:
                print(f"Extensión no soportada: {ext}", file=sys.stderr)
                sys.exit(1)
                
        elif mode == '--single' or not mode.startswith('--'):
            # Compatibilidad hacia atrás (si no pasan --single)
            input_path = os.path.abspath(sys.argv[2] if mode == '--single' else sys.argv[1])
            output_path = os.path.abspath(sys.argv[3] if mode == '--single' else sys.argv[2])
            
            if not os.path.exists(input_path):
                print(f"Archivo no encontrado: {input_path}", file=sys.stderr)
                sys.exit(1)
                
            ext = os.path.splitext(input_path)[1].lower()
            
            if ext == '.docx':
                batch_convert_docx(os.path.dirname(input_path)) # Actually we need a single function
                # Better to just adapt the old functions
                import comtypes.client
                word = comtypes.client.CreateObject('Word.Application')
                word.Visible = False
                word.DisplayAlerts = 0
                try:
                    doc = word.Documents.Open(input_path, ReadOnly=True)
                    doc.SaveAs(output_path, FileFormat=17)
                    doc.Close(False)
                finally:
                    word.Quit()
            elif ext == '.xlsx':
                import comtypes.client
                excel = comtypes.client.CreateObject('Excel.Application')
                excel.Visible = False
                excel.DisplayAlerts = False
                excel.Interactive = False
                try:
                    wb = excel.Workbooks.Open(input_path, UpdateLinks=0, ReadOnly=True)
                    wb.ExportAsFixedFormat(0, output_path)
                    wb.Close(False)
                finally:
                    excel.Interactive = True
                    excel.Quit()
            else:
                print(f"Extension no soportada: {ext}", file=sys.stderr)
                sys.exit(1)
                
            if not os.path.exists(output_path):
                print("Error: PDF no generado", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Modo desconocido: {mode}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
    finally:
        pythoncom.CoUninitialize()

    print("OK")

if __name__ == '__main__':
    main()
