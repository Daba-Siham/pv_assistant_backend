from reportlab.platypus import Paragraph, Spacer, PageBreak

def build_roi_page(elements, styles, data):

    elements.append(
        Paragraph("Analyse ROI", styles["Heading1"])
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            "Contenu ROI ici...",
            styles["BodyText"]
        )
    )

    elements.append(PageBreak())

    return elements