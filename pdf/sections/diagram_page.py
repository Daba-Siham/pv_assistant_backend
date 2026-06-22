from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

def build_diagram_page():

    elements = []

    elements.append(
        Paragraph("Schéma photovoltaïque", styles['Title'])
    )

    elements.append(Spacer(1, 20))

    return elements