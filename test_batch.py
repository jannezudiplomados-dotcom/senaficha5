import os, shutil, sys
from docx import Document

os.makedirs('test_batch', exist_ok=True)
doc = Document()
doc.add_paragraph("Test")
for i in range(30):
    doc.save(f'test_batch/test_{i}.docx')

import subprocess
res = subprocess.run([sys.executable, 'convert_to_pdf.py', '--batch', os.path.abspath('test_batch'), 'docx'], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
