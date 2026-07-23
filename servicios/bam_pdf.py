import os
import subprocess
import logging
from config import Config

def convertir_excel_a_pdf(input_xlsx_path, output_filename=None):
    """
    Convierte un archivo Excel (.xlsx) a PDF usando LibreOffice en modo headless.
    Retorna la ruta del archivo PDF generado.
    """
    if not os.path.exists(input_xlsx_path):
        raise FileNotFoundError(f"El archivo a convertir no existe: {input_xlsx_path}")

    pdfs_dir = Config.GENERADOS_FOLDER
    os.makedirs(pdfs_dir, exist_ok=True)
    
    # El comando generara el pdf con el mismo nombre base que el excel, en la carpeta de salida
    base_name = os.path.splitext(os.path.basename(input_xlsx_path))[0]
    expected_pdf_name = f"{base_name}.pdf"
    
    # Configuración para LibreOffice en Windows o Linux
    libreoffice_path = 'soffice'
    lo_found = False
    if os.name == 'nt':
        # Ruta típica en Windows
        lo_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in lo_paths:
            if os.path.exists(p):
                libreoffice_path = p
                lo_found = True
                break
    else:
        lo_found = True # Asumimos que está en el PATH en Linux

    try:
        if os.name == 'nt' and not lo_found:
            # Usar Microsoft Excel vía win32com como fallback en Windows
            import win32com.client
            import pythoncom
            
            pythoncom.CoInitialize()
            excel = win32com.client.DispatchEx("Excel.Application")
            try:
                excel.Visible = False
            except Exception:
                pass
            excel.DisplayAlerts = False
            try:
                abs_excel_path = os.path.abspath(input_xlsx_path)
                abs_pdf_path = os.path.abspath(os.path.join(pdfs_dir, expected_pdf_name))
                wb = excel.Workbooks.Open(abs_excel_path)
                # xlTypePDF = 0
                wb.ExportAsFixedFormat(0, abs_pdf_path)
                wb.Close(False)
            finally:
                try:
                    excel.Quit()
                except Exception:
                    pass
                pythoncom.CoUninitialize()
            
            generated_pdf_path = abs_pdf_path
        else:
            # Si estamos en Linux o LibreOffice fue encontrado
            subprocess.run([
                libreoffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', pdfs_dir,
                input_xlsx_path
            ], capture_output=True, text=True, check=True)
            generated_pdf_path = os.path.join(pdfs_dir, expected_pdf_name)

        # Si se especificó un nombre de salida distinto, lo renombramos
        if output_filename:
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            final_path = os.path.join(pdfs_dir, output_filename)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(generated_pdf_path, final_path)
            return final_path
            
        return generated_pdf_path

    except subprocess.TimeoutExpired:
        logging.getLogger(__name__).error("Timeout al convertir archivo a PDF con LibreOffice.")
        raise Exception("El proceso de conversión a PDF tardó demasiado.")
    except subprocess.CalledProcessError as e:
        logging.getLogger(__name__).error(f"Error de LibreOffice: {e.stderr}")
        raise Exception("Error ejecutando LibreOffice (¿está instalado correctamente?)")
    except Exception as e:
        logging.getLogger(__name__).error(f"Error inesperado al convertir a PDF: {str(e)}")
        raise Exception(f"Error al generar el PDF: {str(e)}")
