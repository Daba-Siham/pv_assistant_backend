from reportlab.platypus import Paragraph, Spacer, PageBreak

def build_cover_page(elements, styles, data):

    title = Paragraph(
        "Rapport Solaire Intelligent",
        styles["Title"]
    )

    elements.append(title)

    elements.append(Spacer(1, 40))

    intro = Paragraph(
        """
        Rapport professionnel généré par Solar AI.<br/><br/>

        Ce document contient :
        <br/>
        • Analyse énergétique<br/>
        • Dimensionnement photovoltaïque<br/>
        • Rentabilité<br/>
        • Recommandations IA<br/>
        • Maintenance<br/>
        • Guide installation
        """,
        styles["BodyText"]
    )

    elements.append(intro)

    elements.append(PageBreak())

    return elements