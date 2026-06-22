from reportlab.platypus import Paragraph, Spacer, PageBreak

def build_maintenance_page(elements, styles, data):

    title = Paragraph(
        "Maintenance du système solaire",
        styles["Heading1"]
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    content = Paragraph(
        """
        Conseils de maintenance :
        <br/><br/>

        • Nettoyer les panneaux tous les 6 mois<br/>
        • Vérifier les connexions électriques<br/>
        • Contrôler l'onduleur<br/>
        • Vérifier la production énergétique<br/>
        • Inspecter les supports et câbles
        """,
        styles["BodyText"]
    )

    elements.append(content)

    elements.append(PageBreak())

    return elements