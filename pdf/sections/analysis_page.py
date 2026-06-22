from reportlab.platypus import *

def build_analysis_page(elements, styles, data):

    elements = []

    elements.append(
        Paragraph(
            "1. Analyse énergétique",
            styles["Heading2"]
        )
    )

    consommation = data.get("consommation", 0)

    monthly = int(consommation) * 30

    yearly = int(consommation) * 365

    text = f"""
    Consommation journalière : {consommation} kWh/j<br/>
    Consommation mensuelle : {monthly} kWh/mois<br/>
    Consommation annuelle : {yearly} kWh/an
    """

    elements.append(
        Paragraph(text, styles["BodyText"])
    )

    elements.append(Spacer(1, 20))

    return elements