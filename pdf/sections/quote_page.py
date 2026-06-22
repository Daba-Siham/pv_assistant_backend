from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.platypus.tables import Table, TableStyle

def build_quote_page(elements, styles, data):

    elements.append(
        Paragraph(
            "DEVIS ESTIMATIF",
            styles["Heading1"]
        )
    )

    elements.append(Spacer(1, 20))

    devis_data = [

        ["Équipement", "Prix"],

        ["Panneaux photovoltaïques", "2800 €"],

        ["Batterie lithium", "8050 €"],

        ["Onduleur hybride", "1920 €"],

        ["Installation", "3193 €"],

        ["TOTAL", data.get("budget_estime", "0 €")]

    ]

    table = Table(
        devis_data,
        colWidths=[300, 150]
    )

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("FONTSIZE", (0,0), (-1,0), 12),

        ("BOTTOMPADDING", (0,0), (-1,0), 12),

        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),

        ("GRID", (0,0), (-1,-1), 1, colors.grey),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))