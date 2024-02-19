import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def add_plot_to_pdf(title, x, y, pdf: PdfPages):
    plt.figure(figsize=(8, 4))
    plt.plot(x, y, color="blue", linewidth=2, markersize=4)
    plt.title(title)
    pdf.savefig()
    plt.close()

from PyPDF2 import PdfReader, PdfWriter
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def add_text_to_pdf(input_pdf_filename, output_pdf_filename, text_to_add):
    # Read the existing PDF
    existing_pdf = PdfReader(open(input_pdf_filename, "rb"))
    
    # Create an output PDF
    output_pdf = PdfWriter()

    # Add all pages from the existing PDF to the output PDF
    for page in existing_pdf.pages:
        output_pdf.add_page(page)

    # Create a PDF with Reportlab for the new page
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(20, 20, text_to_add)
    can.save()

    # Move to the beginning of the StringIO buffer
    packet.seek(0)

    # Create a new PDF with Reportlab
    new_pdf = PdfReader(packet)
    
    # Add the new page with added text to the output PDF
    output_pdf.add_page(new_pdf.pages[0])

    # Write the output PDF to a file
    with open(output_pdf_filename, "wb") as output_stream:
        output_pdf.write(output_stream)