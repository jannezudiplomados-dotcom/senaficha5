"""
Helper script: converts DOCX/XLSX to PDF using Microsoft Office COM.
Run as a separate process to avoid COM threading issues with Flask.
Usage: python convert_to_pdf.py <input_path> <output_path>
"""
import sys
import os


def convert_docx(abs_in, abs_out):
    import comtypes.client
    word = comtypes.client.CreateObject('Word.Application')
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(abs_in)
        doc.SaveAs(abs_out, FileFormat=17)  # 17 = wdFormatPDF
        doc.Close(False)
    finally:
        try:
            word.Quit()
        except Exception:
            pass


def convert_xlsx(abs_in, abs_out):
    import comtypes.client
    excel = comtypes.client.CreateObject('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(abs_in)
        wb.ExportAsFixedFormat(0, abs_out)  # 0 = xlTypePDF
        wb.Close(False)
    finally:
        try:
            excel.Quit()
        except Exception:
            pass


def main():
    if len(sys.argv) != 3:
        print("Uso: python convert_to_pdf.py <input> <output>", file=sys.stderr)
        sys.exit(1)

    input_path = os.path.abspath(sys.argv[1])
    output_path = os.path.abspath(sys.argv[2])

    if not os.path.exists(input_path):
        print(f"Archivo no encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(input_path)[1].lower()

    import pythoncom
    pythoncom.CoInitialize()
    try:
        if ext == '.docx':
            convert_docx(input_path, output_path)
        elif ext == '.xlsx':
            convert_xlsx(input_path, output_path)
        else:
            print(f"Extension no soportada: {ext}", file=sys.stderr)
            sys.exit(1)
    finally:
        pythoncom.CoUninitialize()

    if os.path.exists(output_path):
        print("OK")
    else:
        print("Error: PDF no generado", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
