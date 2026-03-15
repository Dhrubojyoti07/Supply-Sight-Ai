from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io


def generate_pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin
    line_height = 14

    for line in text.splitlines():
        if y < margin:
            c.showPage()
            y = height - margin
        c.setFont("Helvetica", 10)
        c.drawString(margin, y, line[:1000])
        y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.read()
