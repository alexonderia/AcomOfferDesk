"""Rebuild small, synthetic preview fixtures using only the Python standard library."""
import base64
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1] / 'src/shared/lib/files/__fixtures__'
root.mkdir(parents=True, exist_ok=True)
rels = 'http://schemas.openxmlformats.org/package/2006/relationships'
office_rels = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
with ZipFile(root / 'preview.docx', 'w', ZIP_DEFLATED) as archive:
    archive.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    archive.writestr('_rels/.rels', f'<Relationships xmlns="{rels}"><Relationship Id="r1" Type="{office_rels}/officeDocument" Target="word/document.xml"/></Relationships>')
    archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body><w:p><w:r><w:t>Preview document</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:p><w:hyperlink r:id="unsafe"><w:r><w:t>Unsafe link text</w:t></w:r></w:hyperlink></w:p></w:body></w:document>')
    archive.writestr('word/_rels/document.xml.rels', f'<Relationships xmlns="{rels}"><Relationship Id="unsafe" Type="{office_rels}/hyperlink" Target="javascript:alert(1)" TargetMode="External"/></Relationships>')

with ZipFile(root / 'preview.xlsx', 'w', ZIP_DEFLATED) as archive:
    archive.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
    archive.writestr('_rels/.rels', f'<Relationships xmlns="{rels}"><Relationship Id="r1" Type="{office_rels}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    archive.writestr('xl/workbook.xml', f'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="{office_rels}"><sheets><sheet name="First sheet" sheetId="1" r:id="r1"/><sheet name="Second sheet" sheetId="2" r:id="r2"/></sheets></workbook>')
    archive.writestr('xl/_rels/workbook.xml.rels', f'<Relationships xmlns="{rels}"><Relationship Id="r1" Type="{office_rels}/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="r2" Type="{office_rels}/worksheet" Target="worksheets/sheet2.xml"/></Relationships>')
    for number, text in [(1, 'First sheet value'), (2, '&lt;script&gt;alert(1)&lt;/script&gt;')]:
        archive.writestr(f'xl/worksheets/sheet{number}.xml', f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:B2"/><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>{text}</t></is></c><c r="B1"><v>21</v></c></row><row r="2"><c r="B2"><f>SUM(B1,B1)</f><v>42</v></c></row></sheetData></worksheet>')

objects = [
    b'<< /Type /Catalog /Pages 2 0 R >>',
    b'<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>',
    b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>',
    b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] /Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R >>',
    b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
]
for label in [b'Preview page one', b'Preview page two']:
    stream = b'BT /F1 24 Tf 35 220 Td (' + label + b') Tj ET'
    objects.append(b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream')
pdf = bytearray(b'%PDF-1.4\n')
offsets = [0]
for number, content in enumerate(objects, 1):
    offsets.append(len(pdf))
    pdf.extend(f'{number} 0 obj\n'.encode() + content + b'\nendobj\n')
xref = len(pdf)
pdf.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
for offset in offsets[1:]:
    pdf.extend(f'{offset:010d} 00000 n \n'.encode())
pdf.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
(root / 'preview.pdf').write_bytes(pdf)
(root / 'preview.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jfWQAAAAASUVORK5CYII='))
