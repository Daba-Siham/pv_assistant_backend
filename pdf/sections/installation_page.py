from reportlab.platypus import Paragraph, Spacer, PageBreak

def build_installation_page(elements, styles, data):

    title = Paragraph(
        "Guide d'installation",
        styles["Heading1"]
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    content = Paragraph(
        """
        Étapes d'installation des panneaux solaires :
        <br/><br/>

        1. Analyse du site<br/>
        2. Préparation du toit<br/>
        3. Installation des supports<br/>
        4. Pose des panneaux<br/>
        5. Connexion électrique<br/>
        6. Test du système
        """,
        styles["BodyText"]
    )

    elements.append(content)

    elements.append(PageBreak())

    return elements