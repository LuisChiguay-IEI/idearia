"""
Genera documentos PDF y Word (.docx) simples, sin librerías externas.

Se usan para los datos de demostración y para las pruebas automatizadas
(así las pruebas suben archivos reales y válidos).
"""

import io
import textwrap
import zipfile
from xml.sax.saxutils import escape


def _escapar_pdf(texto):
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generar_pdf(titulo, secciones, encabezado="Idearia · Planificación de experiencia de aprendizaje"):
    """
    Crea un PDF de una página.
    secciones: lista de tuplas (subtítulo, texto).
    """
    instrucciones = [
        "0.18 0.42 0.85 rg 0 790 595 52 re f",
        "BT /F2 11 Tf 1 1 1 rg 40 810 Td (" + _escapar_pdf(encabezado) + ") Tj ET",
    ]
    y = 752
    for linea in textwrap.wrap(titulo, 60):
        instrucciones.append(f"BT /F2 17 Tf 0.11 0.17 0.35 rg 40 {y} Td ({_escapar_pdf(linea)}) Tj ET")
        y -= 24
    y -= 6
    for subtitulo, texto in secciones:
        if y < 70:
            break
        instrucciones.append(f"BT /F2 11.5 Tf 0.18 0.42 0.85 rg 40 {y} Td ({_escapar_pdf(subtitulo)}) Tj ET")
        y -= 17
        for linea in textwrap.wrap(texto, 95) or [""]:
            if y < 60:
                break
            instrucciones.append(f"BT /F1 10 Tf 0.15 0.18 0.25 rg 40 {y} Td ({_escapar_pdf(linea)}) Tj ET")
            y -= 14
        y -= 8
    instrucciones.append(
        "BT /F1 8 Tf 0.45 0.5 0.6 rg 40 30 Td ("
        + _escapar_pdf("Documento de demostración generado para pruebas de Idearia.")
        + ") Tj ET"
    )
    contenido = "\n".join(instrucciones).encode("cp1252", errors="replace")

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(contenido) + contenido + b"\nendstream",
    ]
    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    posiciones = []
    for numero, objeto in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for posicion in posiciones:
        salida += b"%010d 00000 n \n" % posicion
    salida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, inicio_xref)
    return bytes(salida)


def generar_docx(titulo, secciones):
    """Crea un documento Word (.docx) mínimo y válido."""

    def parrafo(texto, negrita=False, tamano=None):
        propiedades = ""
        if negrita or tamano:
            propiedades = "<w:rPr>" + ("<w:b/>" if negrita else "") + (f'<w:sz w:val="{tamano}"/>' if tamano else "") + "</w:rPr>"
        return f'<w:p><w:r>{propiedades}<w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>'

    cuerpo = [parrafo("Idearia · Planificación de experiencia de aprendizaje", tamano=18), parrafo(titulo, True, 32)]
    for subtitulo, texto in secciones:
        cuerpo.append(parrafo(subtitulo, True, 24))
        cuerpo.append(parrafo(texto))
    documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        + "".join(cuerpo)
        + "<w:sectPr/></w:body></w:document>"
    )
    tipos = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    relaciones = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    relaciones_documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
    )
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", tipos)
        docx.writestr("_rels/.rels", relaciones)
        docx.writestr("word/document.xml", documento)
        docx.writestr("word/_rels/document.xml.rels", relaciones_documento)
    return memoria.getvalue()
