from reportlab.platypus import *

def build_equipment_page(elements, styles, data):

    elements = []

    elements.append(
        Paragraph(
            "2. Équipements recommandés",
            styles["Heading2"]
        )
    )

    text = f"""
    • Panneaux : {data.get('panneaux')}<br/>
    • Batterie : {data.get('battery')}<br/>
    • Onduleur : {data.get('inverter')}<br/>
    • Production : {data.get('production')}<br/>
    """

    elements.append(
        Paragraph(text, styles["BodyText"])
    )

    elements.append(Spacer(1, 20))

    return elements