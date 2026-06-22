
# ============================================================
# GENERATE PDF COMPLET — RAPPORT IA PHOTOVOLTAÏQUE
# ============================================================

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.paragraph import ParagraphStyle
from reportlab.lib.pagesizes import A4

from datetime import datetime
from pathlib import Path

from pdf.report_theme import (
    ACCENT_COLOR,
    BORDER_COLOR,
    DANGER_COLOR,
    LIGHT_BG_COLOR,
    MUTED_COLOR,
    PRIMARY_COLOR,
    REPORT_FONTS,
    SECONDARY_COLOR,
    SUCCESS_COLOR,
    SURFACE_COLOR,
    TEXT_COLOR,
    WARNING_COLOR,
)


# ============================================================
# PDF FUNCTION
# ============================================================


def generate_pdf_report(
    filename,
    user_data,
    results
):

    # ========================================================
    # DATA
    # ========================================================

    city = user_data.get("city", "-")

    installation_type = user_data.get(
        "installation_type",
        "-"
    )

    consumption = user_data.get(
        "daily_consumption_kwh",
        0
    )

    orientation_user = user_data.get(
        "orientation",
        "-"
    )

    client_name = user_data.get(
    "client_name",
    "Client"
)

    panels = results.get("panels", {})
    battery = results.get("battery", {})
    inverter = results.get("inverter", {})
    installation = results.get("installation", {})
    solar = results.get("solar_data", {})
    cost = results.get("cost", {})
    roi = results.get("roi", {})
    recommendations = results.get(
        "recommendations",
        []
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    # ========================================================
    # COLORS
    # ========================================================

    PRIMARY = colors.HexColor("#2f8de4")
    LIGHT = colors.HexColor("#dfeefb")
    BORDER = colors.HexColor("#c7c7c7")

    # ========================================================
    # STYLES
    # ========================================================

    title_style = ParagraphStyle(
        "title",
        parent=styles["Heading1"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0d47a1"),
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "sub",
        parent=styles["BodyText"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=20,
    )

    section_style = ParagraphStyle(
        "section",
        parent=styles["Heading2"],
        backColor=LIGHT,
        textColor=colors.HexColor("#1565c0"),
        fontSize=12,
        leading=16,
        spaceBefore=12,
        spaceAfter=12,
        leftIndent=6,
        borderPadding=6,
    )

    body_style = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=20,
    )

    # ========================================================
    # ELEMENTS
    # ========================================================

    elements = []

    # ========================================================
    # TITLE
    # ========================================================

    elements.append(
        Paragraph(
            "RAPPORT : SYSTÈME PHOTOVOLTAÏQUE",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "Dimensionnement intelligent photovoltaïque",
            subtitle_style
        )
    )

    # ========================================================
    # INFORMATIONS CLIENT
    # ========================================================

    elements.append(
        Paragraph(
            "Informations Client",
            section_style
        )
    )

    info_data = [

        

        ["Client", client_name],

        ["Ville", city],

        [
            "Date",
            datetime.now().strftime("%d/%m/%Y")
        ],

        [
            "Type système",
            installation_type
        ],

        [
            "Consommation",
            f"{consumption} kWh/jour"
        ],

        [
            "Orientation",
            orientation_user
        ],

    ]

    table = Table(
        info_data,
        colWidths=[220, 220]
    )

    table.setStyle(TableStyle([

        ("GRID", (0,0), (-1,-1), 1, BORDER),

        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),

        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),

        ("BOTTOMPADDING", (0,0), (-1,-1), 10),

        ("TOPPADDING", (0,0), (-1,-1), 10),
         ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)

    ]))

    elements.append(table)

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # RÉSUMÉ IA
    # ========================================================

    elements.append(
        Paragraph(
            "Résumé Intelligent IA",
            section_style
        )
    )

    irradiation = solar.get(
        "irradiation",
        5.5
    )

    tilt = installation.get(
        "tilt_angle",
        30
    )

    orientation_opt = installation.get(
        "orientation",
        orientation_user
    )

    roi_years = roi.get(
        "roi_years",
        0
    )
    ai_analysis = results.get(
    "ai_analysis",
    {}
)

    ai_score = ai_analysis.get(
    "score",
    0
)
    project_status = results.get(
    "project_status",
    "-"
)
    environment = results.get(
    "environment",
    {}
)

    co2_saved = environment.get(
    "co2_saved_kg_per_year",
    0
)
    performance = results.get(
    "performance",
    {}
)

    coverage_rate = performance.get(
    "coverage_rate_percent",
    0
)

    if tilt < 15:
        tilt_comment = """
    • Inclinaison faible adaptée aux régions fortement ensoleillées.<br/>
    • Production estivale optimisée.
    """
    elif tilt <= 35:
     tilt_comment = """
    • Excellent compromis pour une production annuelle équilibrée.<br/>
    • Rendement photovoltaïque optimisé sur l'ensemble des saisons.
    """
    else:
     tilt_comment = """
    • Inclinaison favorisant la production hivernale.<br/>
    • Réduction de l'accumulation d'eau et de poussière.
    """
    
    summary = f"""
    Le système photovoltaïque proposé a été conçu
    spécialement pour répondre à une consommation énergétique
    quotidienne estimée à
    <b>{consumption} kWh/jour</b>.

    <br/><br/>

    Après analyse des besoins énergétiques,
    du budget disponible ainsi que des conditions
    d’ensoleillement de la région de
    <b>{city}</b>,
    la solution retenue est un système
    <b>{installation_type}</b>.

    <br/><br/>

    <b>Irradiation solaire moyenne :</b> {irradiation} kWh/m²/j

    <br/><br/>

    <b>Inclinaison optimale recommandée :</b> {tilt}°

    <br/><br/>

    <b>Analyse IA de l'inclinaison :</b>

<br/><br/>

{tilt_comment}

    <b>Orientation optimale :</b> {orientation_opt}
    <br/><br/>

    Le retour sur investissement estimé est de
    <b>{roi_years} ans</b>.
    <br/><br/>

    <b>Score IA :</b> {ai_score}/100
    <br/><br/>

    <b>Statut du projet :</b> {project_status}
    <br/><br/>

    <b>Taux de couverture énergétique :</b>
    {coverage_rate} %
    <br/><br/>
    """

    elements.append(
        Paragraph(
            summary,
            body_style
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # PANNEAUX
    # ========================================================

    elements.append(
        Paragraph(
            "Panneaux Solaires",
            section_style
        )
    )

    panel_table = Table([

        [
            "Marque",
            "Modèle",
            "Puissance",
            "Qté",
            "Production"
        ],

        [
            panels.get(
    "panel_brand",
    "-"
),

            panels.get(
                "panel_model",
                "-"
            ),

            f'{panels.get("panel_power_w", 0)} W',

            str(
                panels.get(
                    "panel_count",
                    0
                )
            ),

            f'{panels.get("estimated_daily_production_kwh", 0)} kWh/j'
        ]

    ], colWidths=[95,140,90,50,100])

    panel_table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), PRIMARY),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 1, BORDER),

        ("BOTTOMPADDING", (0,0), (-1,-1), 10),

        ("TOPPADDING", (0,0), (-1,-1), 10),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

    ]))

    elements.append(panel_table)

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # BATTERIES
    # ========================================================

    elements.append(
        Paragraph(
            "Système de Batteries",
            section_style
        )
    )

    battery_table = Table([

    [
        "Type",
        "Capacité",
        "Qté",
        "Prix unité",
        "Prix total"
    ],

    [

        battery.get(
            "battery_type",
            "-"
        ),

        f'{performance.get("storage_capacity_kwh",0)} kWh',

        str(
            battery.get(
                "battery_count",
                0
            )
        ),

        f'{cost.get("battery_unit_price",0)} DH',

        f'{cost.get("battery_cost",0)} DH'
    ]

], colWidths=[120,100,70,100,100])

    battery_table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), PRIMARY),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 1, BORDER),

        ("BOTTOMPADDING", (0,0), (-1,-1), 10),

        ("TOPPADDING", (0,0), (-1,-1), 10),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

    ]))

    elements.append(battery_table)

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # ONDULEUR
    # ========================================================

    elements.append(
        Paragraph(
    f"Onduleur {inverter.get('inverter_type','')}",
    section_style
)
    )

    inverter_table = Table([

    [
        "Modèle",
        "Puissance",
        "Type",
        "Fonction"
    ],

    [
    Paragraph(
        inverter.get("inverter_model", "-"),
        body_style
    ),

    Paragraph(
        f'{inverter.get("recommended_power_kw",0)} kW',
        body_style
    ),

    Paragraph(
        inverter.get("inverter_type", "-"),
        body_style
    ),

    Paragraph(
        inverter.get("description", "-"),
        body_style
    )
]

], colWidths=[140,100,100,120])

    inverter_table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), PRIMARY),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 1, BORDER),

        ("BOTTOMPADDING", (0,0), (-1,-1), 10),

        ("TOPPADDING", (0,0), (-1,-1), 10),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

    ]))

    elements.append(inverter_table)

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # BUDGET
    # ========================================================

    elements.append(
        Paragraph(
            "Budget Détaillé du Système",
            section_style
        )
    )

    budget_table = Table([

        [
            "Matériel",
            "Description",
            "Qté",
            "Prix Unitaire",
            "Prix Global"
        ],

        [
            "Panneaux",

            panels.get(
                "panel_model",
                "-"
            ),

            str(
                panels.get(
                    "panel_count",
                    0
                )
            ),

            f'{cost.get("panel_unit_price", 0)} DH',

            f'{cost.get("panels_cost", 0)} DH'
        ],

        [
            "Batteries",

            battery.get(
                "battery_type",
                "-"
            ),

            str(
                battery.get(
                    "battery_count",
                    0
                )
            ),

            f'{cost.get("battery_unit_price", 0)} DH',

            f'{cost.get("battery_cost", 0)} DH'
        ],

        [
            "Onduleur",

            inverter.get(
                "inverter_model",
                "-"
            ),

            "1",

            f'{cost.get("inverter_unit_price", 0)} DH',

            f'{cost.get("inverter_cost", 0)} DH'
        ],

        [
    "Installation",

    f"Main d'oeuvre système {panels.get('total_power_kwp',0)} kWp",

    "1",

    f'{cost.get("installation_cost_per_kw",0)} DH/kW',

    f'{cost.get("installation_cost",0)} DH'
],

        [
            "", "", "",

            "BUDGET FINAL",

            f'{cost.get("total_cost", 0)} DH'
        ]

    ], colWidths=[95,150,55,90,100])

    budget_table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), PRIMARY),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 1, BORDER),

        ("BOTTOMPADDING", (0,0), (-1,-1), 10),

        ("TOPPADDING", (0,0), (-1,-1), 10),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("FONTNAME", (3,-1), (4,-1), "Helvetica-Bold"),

        ("BACKGROUND", (3,-1), (4,-1), LIGHT),

    ]))

    elements.append(budget_table)

    elements.append(
        Spacer(1, 20)
    )

    elements.append(PageBreak())
    # ========================================================
    # GUIDE INSTALLATION
    # ========================================================

    elements.append(
        Paragraph(
            "Guide Installation",
            section_style
        )
    )

    guide_steps = [

    f"Installer {panels.get('panel_count',0)} panneaux solaires.",

    f"Orienter les panneaux vers {orientation_opt}.",

    f"Respecter une inclinaison optimale de {tilt}°.",

    f"Installer l'onduleur {inverter.get('inverter_model','-')}.",

    "Installer les protections AC/DC.",

    "Effectuer les tests de mise en service."
]
    if battery.get("battery_count",0) > 0:
        guide_steps.append(
          f"Installer {battery.get('battery_count')} batterie(s)."
    ),

    guide_text = ""

    for step in guide_steps:

     guide_text += f"• {step}<br/><br/>"

    elements.append(
      Paragraph(
        guide_text,
        body_style
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # MAINTENANCE
    # ========================================================
    elements.append(
        Paragraph(
            "Maintenance Préventive",
            section_style
        )
    )

    maintenance_tasks = []

    if panels.get("panel_count",0) > 10:

     maintenance_tasks.append(
        "Nettoyage des panneaux tous les 3 mois."
    )

    else:

     maintenance_tasks.append(
        "Nettoyage des panneaux tous les 6 mois."
    )

    maintenance_tasks.extend([

    "Inspection des connexions électriques.",

    "Vérification des protections AC/DC.",

    "Contrôle de la production énergétique.",

    f"Inspection de l'onduleur {inverter.get('inverter_model','-')}."

])

    if battery.get("battery_count",0) > 0:

     maintenance_tasks.append(
        "Contrôle périodique des batteries."
    )

    maintenance = ""

    for task in maintenance_tasks:

     maintenance += f"• {task}<br/><br/>"

    elements.append(
        Paragraph(
            maintenance,
            body_style
        )
    )
    elements.append(
    Spacer(1,20)
)

    elements.append(
    Paragraph(
        "Recommandations IA",
        section_style
    )
)

    if recommendations:

     recommendation_text = ""

     for rec in recommendations:

        recommendation_text += (
            f"• {rec}<br/><br/>"
        )
 
    else:

     recommendation_text = """
    Aucune recommandation spécifique disponible.
    """

    elements.append(
    Paragraph(
        recommendation_text,
        body_style
    )
)
    
    elements.append(
    Paragraph(
        "Impact Environnemental",
        section_style
    )
)

    elements.append(
    Paragraph(
        f"""
        Ce système permettra d'éviter environ
<b>{co2_saved} kg de CO2 par an</b>,
contribuant à la réduction de l'empreinte carbone.
        """,
        body_style
    )
)
    # ========================================================
    # BUILD
    # ========================================================
    doc.build(elements)

    return filename


def _generate_recommendation_pdf_report_legacy(filename: str, recommendation_result: dict) -> str:
    formatted = recommendation_result["formatted_recommendation"]
    data = formatted["recommendation_data"]
    scenario_analysis = data["scenario_analysis"]

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "recommendation_title",
        parent=styles["Heading1"],
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0d47a1"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "recommendation_section",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1565c0"),
        backColor=colors.HexColor("#dfeefb"),
        borderPadding=6,
        leftIndent=6,
        spaceBefore=12,
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "recommendation_body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=16,
    )

    def p(text: str):
        return Paragraph(text.replace("\n", "<br/>"), body_style)

    surface_check = data.get("surface_check") or {}
    scenarios = data["scenarios"]
    points_to_check = data.get("points_to_check", [])
    constraints_analysis = data.get("constraints_analysis", [])
    brands = data.get("brands", {})
    selected_inverter = brands.get("selected_inverter", "inverter_on_grid")
    panel_brands = brands.get("panels", {})
    battery_brands = brands.get("battery")
    inverter_brands = brands.get(selected_inverter, {})

    battery_text = (
        "Aucune batterie n'est nécessaire dans cette configuration, car le système est connecté au réseau et l'autonomie demandée est de 0 jour."
        if not data["battery_visible"]
        else "Vous avez choisi un système connecté au réseau, mais vous demandez une autonomie batterie. Pour répondre à ce besoin, une installation hybride serait plus adaptée."
        if "B" in scenario_analysis.get("detected_scenarios", [])
        else f"Batterie conseillée : {data['battery_range']}."
    )

    elements = [
        Paragraph("RAPPORT : SYSTÈME PHOTOVOLTAÏQUE", title_style),
        Paragraph("Informations du projet", section_style),
    ]

    info_table = Table(
        [
            ["Ville", data["city"]],
            ["Type de système", data["installation_type_label"]],
            ["Consommation", f"environ {data['daily_consumption_kwh']} kWh/jour"],
            ["Surface disponible", f"{data['available_area_m2']} m²"],
            ["Budget déclaré", data["budget_declared"]],
            ["Orientation", data.get("orientation") or "à vérifier"],
            ["Inclinaison", f"{data['tilt_angle']}°"],
            ["Ombrage", data.get("shading") or "à vérifier"],
        ],
        colWidths=[180, 300],
    )
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#c7c7c7")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f6fa")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.extend([info_table, Spacer(1, 14)])

    elements.extend([
        Paragraph("Synthèse intelligente", section_style),
        p(
            f"Le projet vise une installation photovoltaïque {data['installation_type_label']}. "
            f"Le besoin énergétique est d'environ {data['daily_consumption_kwh']} kWh/jour. "
            f"Le statut global est : {data['global_status']}."
        ),
        Paragraph("Analyse du besoin énergétique", section_style),
        p(
            f"La consommation demandée est d'environ {data['daily_consumption_kwh']} kWh/jour. "
            "Cette valeur doit être comparée à la surface disponible, à l'orientation, à l'ombrage et au budget. "
            "Le dimensionnement final doit être confirmé avec les appareils réellement utilisés et les habitudes de consommation."
        ),
        Paragraph("Statut global", section_style),
        p(
            f"Statut : {data['global_status']}."
        ),
        Paragraph("Analyse des contraintes détectées", section_style),
        p("\n".join(f"- {item}" for item in constraints_analysis) if constraints_analysis else "- Aucune contrainte majeure détectée."),
        Paragraph("Recommandation principale", section_style),
        p(
            f"Le modèle recommande {data['panels_range']} avec une puissance de module {data['panel_power_range']}. "
            f"La puissance solaire visée est {data['pv_power_range']}."
        ),
    ])

    if surface_check.get("status") == "insufficient":
        elements.extend([
            Paragraph("Solution réaliste selon contraintes", section_style),
            p(
                f"Avec {data['available_area_m2']} m², il est plus réaliste d'installer environ "
                f"{surface_check.get('realistic_panel_count')} panneaux. La couverture énergétique sera donc partielle "
                "sauf si une surface supplémentaire est disponible."
            ),
        ])

    elements.extend([
        Paragraph("Panneaux recommandés", section_style),
        p(
            "Type conseillé : panneaux monocristallins performants.<br/>"
            f"Nombre recommandé par le modèle : {data['panels_range']}.<br/>"
            f"Puissance conseillée par panneau : {data['panel_power_range']}.<br/>"
            f"Puissance totale recommandée : {data['pv_power_range']}."
        ),
        Paragraph("Onduleur recommandé", section_style),
        p(
            f"Type : {data['inverter_type']}.<br/>"
            f"Gamme conseillée : {data['inverter_range']}."
        ),
        Paragraph("Batterie", section_style),
        p(battery_text),
        Paragraph("Budget et rentabilité", section_style),
        p(
            f"Budget probable : {data['budget_estimated_range']}.<br/>"
            f"ROI estimatif : {data['roi_range']}.<br/>"
            f"Rentabilité : {data['roi_category']}."
        ),
        Paragraph("Points à vérifier", section_style),
        p("\n".join(f"- {item}" for item in points_to_check) if points_to_check else "- Aucun point bloquant détecté."),
        Paragraph("Scénarios proposés", section_style),
        p(
            f"Scénario économique : {scenarios['economic']}<br/><br/>"
            f"Scénario équilibré : {scenarios['balanced']}<br/><br/>"
            f"Scénario performance : {scenarios['performance']}"
        ),
        Paragraph("Marques et matériels à comparer", section_style),
        p(
            f"Panneaux : {panel_brands.get('type', 'panneaux à vérifier')} ; marques à comparer : {', '.join(panel_brands.get('brands', []))}.<br/><br/>"
            + (
                f"Batterie : {battery_brands.get('type')} ; marques à comparer : {', '.join(battery_brands.get('brands', []))}.<br/><br/>"
                if battery_brands else
                "Batterie : non nécessaire dans cette configuration.<br/><br/>"
            )
            + f"Onduleur : {inverter_brands.get('type', data['inverter_type'])} ; marques à comparer : {', '.join(inverter_brands.get('brands', []))}."
        ),
        Paragraph("Fournisseurs et sites à comparer", section_style),
        p(
            "Ces sites sont des pistes de comparaison, pas des recommandations obligatoires. "
            "Il faut vérifier la disponibilité, la garantie, la compatibilité technique et demander un devis installateur.<br/><br/>"
            + "<br/>".join(f"- {supplier}" for supplier in data.get("suppliers_to_compare", []))
        ),
        Paragraph("Guide d'installation", section_style),
        p("\n".join(f"- {item}" for item in data.get("installation_guide", []))),
        Paragraph("Maintenance préventive", section_style),
        p("\n".join(f"- {item}" for item in data.get("maintenance_tasks", []))),
        Paragraph("Impact environnemental", section_style),
        p(data.get("environmental_impact", {}).get("summary", "Impact à estimer selon la production réelle.")),
        Paragraph("Conclusion IA", section_style),
        p(
            data.get("conclusion", "La configuration doit être validée par un installateur avec une visite de site.")
        ),
    ])

    doc.build(elements)
    return filename


def _generate_recommendation_pdf_report_v2(filename: str, recommendation_result: dict) -> str:
    """Generate the public SolarAI recommendation PDF from recommendation_data only."""

    formatted = recommendation_result["formatted_recommendation"]
    data = formatted["recommendation_data"]
    scenario_analysis = data.get("scenario_analysis", {})

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=34,
        leftMargin=34,
        topMargin=82,
        bottomMargin=48,
    )

    page_width, page_height = A4
    usable_width = page_width - doc.leftMargin - doc.rightMargin
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo_solarai.png"
    report_date = datetime.now().strftime("%d/%m/%Y")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "solarai_pdf_title_v2",
        parent=styles["Heading1"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=PRIMARY_COLOR,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "solarai_pdf_subtitle_v2",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=MUTED_COLOR,
        spaceAfter=18,
    )
    section_style = ParagraphStyle(
        "solarai_pdf_section_v2",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=PRIMARY_COLOR,
        backColor=LIGHT_BG_COLOR,
        borderColor=PRIMARY_COLOR,
        borderWidth=0.5,
        borderPadding=7,
        spaceBefore=14,
        spaceAfter=9,
    )
    body_style = ParagraphStyle(
        "solarai_pdf_body_v2",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    small_style = ParagraphStyle(
        "solarai_pdf_small_v2",
        parent=body_style,
        fontSize=8.5,
        leading=12,
        textColor=MUTED_COLOR,
    )
    bullet_style = ParagraphStyle(
        "solarai_pdf_bullet_v2",
        parent=body_style,
        leftIndent=13,
        firstLineIndent=-7,
        spaceAfter=3,
    )
    alert_style = ParagraphStyle(
        "solarai_pdf_alert_v2",
        parent=body_style,
        fontSize=9,
        leading=13,
    )

    def clean_text(value, default="a verifier") -> str:
        if value is None:
            return default
        value = str(value).strip()
        return value or default

    def add_header(canvas, current_doc):
        canvas.saveState()
        canvas.setFillColor(PRIMARY_COLOR)
        canvas.rect(0, page_height - 58, page_width, 58, fill=1, stroke=0)

        x = current_doc.leftMargin
        if logo_path.exists():
            try:
                canvas.drawImage(
                    str(logo_path),
                    x,
                    page_height - 47,
                    width=32,
                    height=32,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                x += 40
            except Exception:
                pass

        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(x, page_height - 26, "SolarAI")
        canvas.setFont("Helvetica", 8.5)
        canvas.drawString(x, page_height - 41, "Assistant intelligent de dimensionnement photovoltaique")
        canvas.drawRightString(page_width - current_doc.rightMargin, page_height - 25, f"Date : {report_date}")
        canvas.drawRightString(
            page_width - current_doc.rightMargin,
            page_height - 40,
            f"Ville : {clean_text(data.get('city'))}",
        )
        canvas.restoreState()

    def add_footer(canvas, current_doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER_COLOR)
        canvas.line(current_doc.leftMargin, 31, page_width - current_doc.rightMargin, 31)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED_COLOR)
        canvas.drawString(current_doc.leftMargin, 18, "SolarAI - Rapport genere automatiquement")
        canvas.drawRightString(page_width - current_doc.rightMargin, 18, f"Page {current_doc.page}")
        canvas.restoreState()

    def draw_page(canvas, current_doc):
        add_header(canvas, current_doc)
        add_footer(canvas, current_doc)

    def add_section_title(title):
        return Paragraph(title, section_style)

    def add_paragraph(text):
        return Paragraph(clean_text(text).replace("\n", "<br/>"), body_style)

    def add_bullet_list(items):
        elements = []
        seen = set()
        for item in items or []:
            normalized = clean_text(item, "").strip(" -")
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            elements.append(Paragraph(f"- {normalized}", bullet_style))
        return elements or [Paragraph("- Aucun point bloquant detecte.", bullet_style)]

    def add_page_break_if_needed():
        return Spacer(1, 6)

    def table_cell(value, style=body_style):
        return Paragraph(clean_text(value), style)

    def add_table(headers, rows, column_widths=None):
        table_data = [[table_cell(header, small_style) for header in headers]]
        for row in rows:
            table_data.append([table_cell(cell) for cell in row])

        table = Table(table_data, colWidths=column_widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ]))
        return table

    def add_key_value_table(table_data):
        rows = [[key, value] for key, value in table_data]
        return add_table(["Element", "Valeur"], rows, [usable_width * 0.34, usable_width * 0.66])

    def add_alert_box(text, level="warning"):
        level_colors = {
            "success": SUCCESS_COLOR,
            "danger": DANGER_COLOR,
            "warning": WARNING_COLOR,
            "info": SECONDARY_COLOR,
        }
        level_backgrounds = {
            "success": colors.HexColor("#F0FDF4"),
            "danger": colors.HexColor("#FEF2F2"),
            "warning": colors.HexColor("#FFFBEB"),
            "info": colors.HexColor("#EFF6FF"),
        }
        table = Table(
            [[Paragraph(clean_text(text), alert_style)]],
            colWidths=[usable_width],
            hAlign="LEFT",
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), level_backgrounds.get(level, colors.HexColor("#FFFBEB"))),
            ("BOX", (0, 0), (-1, -1), 0.8, level_colors.get(level, WARNING_COLOR)),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return table

    def status_alert_level() -> str:
        status = clean_text(data.get("global_status"), "").lower()
        if "non faisable" in status:
            return "danger"
        if "condition" in status:
            return "warning"
        return "success"

    def supplier_rows():
        labels = {
            "Ecowatt": ("Solutions solaires et electriques", "Piste de comparaison pour devis et materiel solaire."),
            "Ecovolt Energy": ("Boutique solaire", "Panneaux, batteries, onduleurs et kits a verifier."),
            "Misterelec / MRELEC": ("Distributeur electrique et solaire", "Materiel electrique, protections, cables et composants PV."),
            "Tecas Solar": ("Vente et installation solaire", "A comparer pour accompagnement et devis installateur."),
            "panneauxsolaire.ma": ("Site specialise solaire", "Composants PV, batteries, onduleurs et accessoires."),
            "GreenWagic": ("Societe solaire", "Vente et installation pour projets residentiels."),
            "Jumia Maroc": ("Marketplace generaliste", "A utiliser avec prudence : verifier vendeur, garantie et compatibilite."),
        }
        rows = []
        for supplier in data.get("suppliers_to_compare", []):
            supplier_name = clean_text(supplier)
            site_type, note = labels.get(supplier_name, ("Piste de comparaison", "Disponibilite et garantie a verifier."))
            rows.append([supplier_name, site_type, note])
        return rows

    surface_check = data.get("surface_check") or {}
    scenarios = data.get("scenarios", {})
    constraints_analysis = data.get("constraints_analysis", [])
    points_to_check = data.get("points_to_check", [])
    brands = data.get("brands", {})
    selected_inverter = brands.get("selected_inverter", "inverter_on_grid")
    panel_brands = brands.get("panels", {})
    battery_brands = brands.get("battery")
    inverter_brands = brands.get(selected_inverter, {})
    battery_visible = bool(data.get("battery_visible"))
    detected_scenarios = scenario_analysis.get("detected_scenarios", [])

    surface_remark = (
        "Surface suffisante pour la recommandation proposee."
        if surface_check.get("status") == "ok"
        else clean_text(surface_check.get("message"), "Surface a verifier selon la toiture disponible.")
    )
    estimated_surface = (
        f"environ {surface_check.get('required_area_m2')} m2"
        if surface_check.get("required_area_m2") is not None
        else "a confirmer"
    )
    battery_note = (
        "Capacite a renforcer ou a confirmer selon l'autonomie demandee."
        if "W" in detected_scenarios
        else "Autonomie et secours, a confirmer par devis installateur."
    )
    inverter_function = (
        "gestion panneaux + batterie + reseau"
        if data.get("installation_type_raw") == "hybrid"
        else "fonctionnement hors reseau avec batterie"
        if data.get("installation_type_raw") == "off_grid"
        else "injection/autoconsommation connectee au reseau"
    )
    budget_gap = (
        "budget insuffisant"
        if "J" in detected_scenarios
        else "budget proche a confirmer"
        if "I" in detected_scenarios
        else "budget compatible a confirmer par devis"
    )

    brand_rows = [
        [
            "Panneaux",
            panel_brands.get("type", "panneaux monocristallins performants"),
            ", ".join(panel_brands.get("brands", ["Jinko Solar", "LONGi", "Canadian Solar"])),
        ],
    ]
    if battery_visible and battery_brands:
        brand_rows.append([
            "Batterie",
            battery_brands.get("type", "batterie lithium LiFePO4"),
            ", ".join(battery_brands.get("brands", ["Pylontech", "BYD", "Huawei Luna"])),
        ])
    brand_rows.append([
        "Onduleur",
        inverter_brands.get("type", data.get("inverter_type")),
        ", ".join(inverter_brands.get("brands", [])),
    ])

    elements = [
        Paragraph("RAPPORT PHOTOVOLTAIQUE SOLARAI", title_style),
        Paragraph("Dimensionnement intelligent photovoltaique", subtitle_style),
        add_alert_box(
            f"Statut global : {clean_text(data.get('global_status'))}. "
            "Les valeurs presentees sont arrondies ou donnees sous forme d'intervalles.",
            status_alert_level(),
        ),
        Spacer(1, 12),
        add_section_title("1. Informations du projet"),
        add_key_value_table([
            ("Client", clean_text(data.get("client_name"), "Client")),
            ("Ville", clean_text(data.get("city"))),
            ("Date", report_date),
            ("Type de systeme", clean_text(data.get("installation_type_label"))),
            ("Consommation journaliere", f"environ {clean_text(data.get('daily_consumption_kwh'))} kWh/jour"),
            ("Surface disponible", f"{clean_text(data.get('available_area_m2'))} m2"),
            ("Budget declare", clean_text(data.get("budget_declared"))),
            ("Orientation", clean_text(data.get("orientation"))),
            ("Inclinaison", f"{clean_text(data.get('tilt_angle'))} degres"),
            ("Ombrage", clean_text(data.get("shading"))),
            ("Autonomie batterie", f"{clean_text(data.get('autonomy_days'), '0')} jour(s)"),
        ]),
        add_section_title("2. Resume intelligent IA"),
        add_paragraph(
            f"Le projet concerne une installation {clean_text(data.get('installation_type_label'))} "
            f"pour une consommation d'environ {clean_text(data.get('daily_consumption_kwh'))} kWh/jour. "
            "La recommandation est construite a partir du modele ML, puis controlee par le backend pour signaler "
            "les contraintes de surface, de budget, d'orientation, d'ombrage et de batterie."
        ),
        add_section_title("3. Statut global"),
        add_alert_box(
            f"{clean_text(data.get('global_status'))}. {clean_text(data.get('conclusion'))}",
            status_alert_level(),
        ),
        add_section_title("4. Analyse des contraintes detectees"),
        *add_bullet_list(constraints_analysis),
        add_section_title("5. Recommandation principale du modele"),
        add_paragraph(
            f"Le modele recommande {clean_text(data.get('panels_range'))}, avec une puissance module "
            f"{clean_text(data.get('panel_power_range'))}. La puissance photovoltaique totale visee est "
            f"{clean_text(data.get('pv_power_range'))}. Ces valeurs sont volontairement presentees sous forme arrondie."
        ),
    ]

    if surface_check.get("status") == "insufficient":
        elements.extend([
            add_section_title("6. Solution realiste selon contraintes"),
            add_alert_box(
                f"Avec {clean_text(data.get('available_area_m2'))} m2, il est plus realiste d'installer environ "
                f"{clean_text(surface_check.get('realistic_panel_count'))} panneaux. La couverture energetique "
                "sera donc partielle sauf si une surface supplementaire est disponible.",
                "warning",
            ),
        ])

    elements.extend([
        add_page_break_if_needed(),
        add_section_title("7. Tableau des panneaux recommandes"),
        add_table(
            ["Type conseille", "Puissance module", "Nombre recommande", "Puissance totale", "Surface estimee", "Remarque"],
            [[
                panel_brands.get("type", "panneaux monocristallins performants"),
                clean_text(data.get("panel_power_range")),
                clean_text(data.get("panels_range")),
                clean_text(data.get("pv_power_range")),
                estimated_surface,
                surface_remark,
            ]],
            [82, 78, 82, 78, 74, 106],
        ),
        add_section_title("8. Batterie et autonomie"),
    ])

    if battery_visible:
        elements.append(add_table(
            ["Type conseille", "Capacite recommandee", "Role", "Remarque"],
            [[
                battery_brands.get("type", "batterie lithium LiFePO4") if battery_brands else "batterie lithium LiFePO4",
                clean_text(data.get("battery_range")),
                "autonomie et secours",
                battery_note,
            ]],
            [120, 115, 105, 160],
        ))
    else:
        elements.append(add_alert_box(
            "Aucune batterie n'est necessaire dans cette configuration, car le systeme est connecte au reseau "
            "et l'autonomie demandee est de 0 jour.",
            "info",
        ))

    elements.extend([
        add_section_title("9. Onduleur recommande"),
        add_table(
            ["Type", "Gamme conseillee", "Fonction", "Remarque"],
            [[
                clean_text(data.get("inverter_type")),
                clean_text(data.get("inverter_range")),
                inverter_function,
                "A confirmer selon la puissance reelle installee et la compatibilite batterie.",
            ]],
            [105, 110, 145, 140],
        ),
        add_section_title("10. Budget estimatif"),
        add_table(
            ["Poste", "Estimation", "Remarque"],
            [
                ["Panneaux", "inclus dans l'estimation globale", "A confirmer selon marque, puissance et garantie."],
                ["Batterie", "poste important" if battery_visible else "non necessaire", "A verifier seulement si stockage demande."],
                ["Onduleur", "inclus dans l'estimation globale", "Prix variable selon type on-grid, hybride ou off-grid."],
                ["Installation/protections", "a confirmer par devis", "Inclut protections AC/DC, cables, pose et mise en service."],
                ["Budget probable total", clean_text(data.get("budget_estimated_range")), "Intervalle issu du modele et du formatter backend."],
                ["Budget declare", clean_text(data.get("budget_declared")), "Budget indique par l'utilisateur."],
                ["Ecart budget", budget_gap, "A confirmer avec devis installateur."],
            ],
            [132, 168, 200],
        ),
        add_section_title("11. Rentabilite et ROI"),
        add_paragraph(
            f"ROI estimatif : {clean_text(data.get('roi_range'))}. "
            f"Rentabilite : {clean_text(data.get('roi_category'))}. "
            "La rentabilite depend du prix final installe, de la production reelle, du tarif d'electricite "
            "et du niveau d'autoconsommation."
        ),
        add_section_title("12. Points a verifier"),
        *add_bullet_list(points_to_check),
        add_section_title("13. Scenarios proposes"),
        add_table(
            ["Scenario", "Description"],
            [
                ["Economique", clean_text(scenarios.get("economic"))],
                ["Equilibre", clean_text(scenarios.get("balanced"))],
                ["Autonomie / performance", clean_text(scenarios.get("performance"))],
            ],
            [120, 380],
        ),
        add_section_title("14. Marques et materiels a comparer"),
        add_paragraph(
            "Les marques ci-dessous sont des exemples a comparer. Elles ne constituent pas une obligation d'achat "
            "et doivent etre validees selon disponibilite locale, garantie et compatibilite technique."
        ),
        add_table(
            ["Materiel", "Type conseille", "Marques a comparer"],
            brand_rows,
            [90, 170, 240],
        ),
        add_section_title("15. Fournisseurs et sites a comparer"),
        add_paragraph(
            "Ces sites sont proposes comme pistes de comparaison. Il faut verifier la disponibilite, les garanties, "
            "la compatibilite technique et demander un devis installateur."
        ),
        add_table(
            ["Fournisseur / site", "Type", "Remarque"],
            supplier_rows(),
            [115, 150, 235],
        ),
        add_section_title("16. Guide d'installation"),
        *add_bullet_list(data.get("installation_guide", [])),
        add_section_title("17. Maintenance preventive"),
        *add_bullet_list(data.get("maintenance_tasks", [])),
        add_section_title("18. Impact environnemental"),
        add_paragraph(
            clean_text(
                (data.get("environmental_impact") or {}).get("summary"),
                "L'impact environnemental dependra de la puissance reellement installee et de la production annuelle obtenue.",
            )
        ),
        add_section_title("19. Conclusion IA"),
        add_paragraph(
            clean_text(
                data.get("conclusion"),
                "La configuration doit etre validee par un installateur qualifie avec une visite de site.",
            )
        ),
    ])

    doc.build(elements, onFirstPage=draw_page, onLaterPages=draw_page)
    return filename


def generate_recommendation_pdf_report(filename: str, recommendation_result: dict) -> str:
    """Generate a themed SolarAI PDF using only recommendation_data."""

    formatted = recommendation_result["formatted_recommendation"]
    data = formatted["recommendation_data"]
    scenario_analysis = data.get("scenario_analysis", {})
    detected = set(scenario_analysis.get("detected_scenarios", []))

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=34,
        leftMargin=34,
        topMargin=86,
        bottomMargin=54,
    )

    page_width, page_height = A4
    usable_width = page_width - doc.leftMargin - doc.rightMargin
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo_solarai.png"
    report_date = datetime.now().strftime("%d/%m/%Y")

    styles = getSampleStyleSheet()
    regular_font = REPORT_FONTS["regular"]
    bold_font = REPORT_FONTS["bold"]

    title_style = ParagraphStyle(
        "solarai_title_final",
        parent=styles["Heading1"],
        fontName=bold_font,
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=PRIMARY_COLOR,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "solarai_subtitle_final",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=MUTED_COLOR,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "solarai_section_final",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=12,
        leading=16,
        textColor=PRIMARY_COLOR,
        backColor=LIGHT_BG_COLOR,
        borderColor=BORDER_COLOR,
        borderWidth=0.6,
        borderPadding=7,
        spaceBefore=14,
        spaceAfter=9,
    )
    body_style = ParagraphStyle(
        "solarai_body_final",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9.3,
        leading=13.5,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    small_style = ParagraphStyle(
        "solarai_small_final",
        parent=body_style,
        fontSize=8.2,
        leading=11.5,
        textColor=MUTED_COLOR,
    )
    bullet_style = ParagraphStyle(
        "solarai_bullet_final",
        parent=body_style,
        leftIndent=13,
        firstLineIndent=-7,
        spaceAfter=3,
    )
    kpi_label_style = ParagraphStyle(
        "solarai_kpi_label",
        parent=small_style,
        fontName=bold_font,
        textColor=MUTED_COLOR,
    )
    kpi_value_style = ParagraphStyle(
        "solarai_kpi_value",
        parent=body_style,
        fontName=bold_font,
        fontSize=10,
        leading=12,
        textColor=PRIMARY_COLOR,
    )

    def clean_text(value, default="à vérifier") -> str:
        if value is None:
            return default
        value = str(value).strip()
        return value or default

    def status_color():
        status = clean_text(data.get("global_status"), "").lower()
        if "non faisable" in status:
            return DANGER_COLOR
        if "condition" in status:
            return WARNING_COLOR
        return SUCCESS_COLOR

    def status_level() -> str:
        status = clean_text(data.get("global_status"), "").lower()
        if "non faisable" in status:
            return "danger"
        if "condition" in status:
            return "warning"
        return "success"

    def add_header(canvas, current_doc):
        canvas.saveState()
        canvas.setFillColor(PRIMARY_COLOR)
        canvas.rect(0, page_height - 62, page_width, 62, fill=1, stroke=0)

        x = current_doc.leftMargin
        if logo_path.exists():
            try:
                canvas.drawImage(
                    str(logo_path),
                    x,
                    page_height - 50,
                    width=34,
                    height=34,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                x += 43
            except Exception:
                pass

        canvas.setFillColor(SURFACE_COLOR)
        canvas.setFont(bold_font, 16)
        canvas.drawString(x, page_height - 27, "SolarAI")
        canvas.setFont(regular_font, 8.5)
        canvas.drawString(x, page_height - 43, "Assistant intelligent de dimensionnement photovoltaïque")
        canvas.drawRightString(page_width - current_doc.rightMargin, page_height - 27, f"Date : {report_date}")
        canvas.drawRightString(
            page_width - current_doc.rightMargin,
            page_height - 43,
            f"Ville : {clean_text(data.get('city'))}",
        )
        canvas.restoreState()

    def add_footer(canvas, current_doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER_COLOR)
        canvas.line(current_doc.leftMargin, 35, page_width - current_doc.rightMargin, 35)
        canvas.setFont(regular_font, 7.8)
        canvas.setFillColor(MUTED_COLOR)
        canvas.drawString(current_doc.leftMargin, 23, "SolarAI — Rapport généré automatiquement")
        canvas.drawString(current_doc.leftMargin, 12, "Données indicatives à confirmer par devis")
        canvas.drawRightString(page_width - current_doc.rightMargin, 18, f"Page {current_doc.page}")
        canvas.restoreState()

    def draw_page(canvas, current_doc):
        add_header(canvas, current_doc)
        add_footer(canvas, current_doc)

    def paragraph(text: str, style=body_style):
        return Paragraph(clean_text(text).replace("\n", "<br/>"), style)

    def add_section_title(title):
        return Paragraph(title, section_style)

    def add_paragraph(text):
        return paragraph(text, body_style)

    def table_cell(value, style=body_style):
        return Paragraph(clean_text(value), style)

    def add_table(headers, rows, column_widths=None):
        table_data = [[table_cell(header, small_style) for header in headers]]
        for row in rows:
            table_data.append([table_cell(cell) for cell in row])

        table = Table(table_data, colWidths=column_widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), SURFACE_COLOR),
            ("FONTNAME", (0, 0), (-1, 0), bold_font),
            ("FONTNAME", (0, 1), (-1, -1), regular_font),
            ("GRID", (0, 0), (-1, -1), 0.45, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE_COLOR, LIGHT_BG_COLOR]),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ]))
        return table

    def add_key_value_table(table_data):
        return add_table(
            ["Élément", "Valeur"],
            [[key, value] for key, value in table_data],
            [usable_width * 0.34, usable_width * 0.66],
        )

    def add_alert_box(text, level="warning"):
        level_colors = {
            "success": SUCCESS_COLOR,
            "danger": DANGER_COLOR,
            "warning": WARNING_COLOR,
            "info": SECONDARY_COLOR,
        }
        color = level_colors.get(level, WARNING_COLOR)
        table = Table(
            [[Paragraph(clean_text(text), body_style)]],
            colWidths=[usable_width],
            hAlign="LEFT",
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG_COLOR),
            ("BOX", (0, 0), (-1, -1), 0.9, color),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return table

    def add_bullet_list(items):
        elements = []
        seen = set()
        for item in items or []:
            normalized = clean_text(item, "").strip(" -")
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            elements.append(Paragraph(f"- {normalized}", bullet_style))
        return elements or [Paragraph("- Aucun point bloquant détecté.", bullet_style)]

    def add_page_break_if_needed():
        return Spacer(1, 6)

    def add_disclaimer():
        return add_alert_box(
            "Ce rapport est une estimation intelligente préliminaire. Il ne remplace pas une étude technique "
            "réalisée par un installateur qualifié. Les prix, disponibilités et compatibilités doivent être "
            "confirmés par devis.",
            "info",
        )

    def add_kpi_cards(kpis):
        cells = []
        for label, value, level in kpis:
            color = {
                "success": SUCCESS_COLOR,
                "warning": WARNING_COLOR,
                "danger": DANGER_COLOR,
                "accent": ACCENT_COLOR,
            }.get(level, PRIMARY_COLOR)
            card = Table(
                [[Paragraph(label, kpi_label_style)], [Paragraph(value, kpi_value_style)]],
                colWidths=[usable_width / 3 - 8],
            )
            card.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE_COLOR),
                ("BOX", (0, 0), (-1, -1), 0.8, color),
                ("LINEABOVE", (0, 0), (-1, 0), 3, color),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]))
            cells.append(card)

        rows = [cells[:3], cells[3:6]]
        table = Table(rows, colWidths=[usable_width / 3] * 3, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def analysis_for(category: str, mapping: dict[str, tuple[str, str]]) -> tuple[str, str]:
        status = (scenario_analysis.get(category) or {}).get("status", "unknown")
        return mapping.get(status, ("À vérifier", "Information à confirmer avec un installateur qualifié."))

    def constraints_table_rows():
        surface_state, surface_text = analysis_for("surface", {
            "ok": ("OK", "La surface disponible semble suffisante pour installer la recommandation proposée."),
            "insufficient": ("À vérifier", "La surface est limitée : une solution réaliste doit être prévue selon la toiture exploitable."),
            "very_insufficient": ("Bloquant", "La surface est trop limitée pour couvrir correctement la consommation."),
            "unknown": ("À vérifier", "La surface exploitable doit être confirmée sur site."),
        })
        budget_state, budget_text = analysis_for("budget", {
            "ok": ("OK", "Le budget déclaré semble compatible avec l’installation recommandée."),
            "near": ("À revoir", "Le budget est proche du coût probable et doit être confirmé par devis."),
            "insufficient": ("Insuffisant", "Le budget déclaré est inférieur au coût probable d’une installation complète."),
            "unknown": ("À vérifier", "Le budget doit être confirmé par devis."),
        })
        orientation_state, orientation_text = analysis_for("orientation", {
            "good": ("Favorable", "L’orientation Sud est favorable pour maximiser la production solaire."),
            "acceptable": ("Moyenne", "L’orientation Est/Ouest peut fonctionner mais produit moins qu’une orientation Sud."),
            "bad": ("Défavorable", "L’orientation Nord est défavorable et une autre toiture doit être étudiée."),
            "unknown": ("À vérifier", "L’orientation doit être confirmée."),
        })
        battery_state, battery_text = analysis_for("battery", {
            "not_needed": ("Non nécessaire", "Aucune batterie n’est nécessaire pour cette configuration."),
            "needed": ("Recommandée", "La batterie est nécessaire ou fortement recommandée pour ce type de système."),
            "insufficient": ("À renforcer", "La capacité batterie doit être renforcée pour l’autonomie demandée."),
            "oversized": ("À revoir", "La batterie peut être surdimensionnée et augmenter inutilement le coût."),
            "hybrid_recommended": ("À revoir", "Une installation hybride serait plus adaptée si l’autonomie est conservée."),
            "unknown": ("À vérifier", "La batterie doit être confirmée selon l’autonomie réelle demandée."),
        })
        inverter_state, inverter_text = analysis_for("inverter", {
            "ok": ("Cohérent", "La gamme d’onduleur semble cohérente avec la puissance photovoltaïque visée."),
            "too_small": ("À vérifier", "L’onduleur peut être trop faible par rapport aux panneaux."),
            "too_large": ("À vérifier", "L’onduleur peut être trop élevé par rapport à la puissance installée."),
            "unknown": ("À vérifier", "La compatibilité onduleur doit être confirmée."),
        })
        consumption_state, consumption_text = analysis_for("consumption", {
            "low": ("Faible", "Une petite installation peut suffire."),
            "medium": ("Moyenne", "Une installation résidentielle standard peut être adaptée."),
            "high": ("Élevée", "Il faut prévoir une surface suffisante et un budget plus important."),
            "very_high": ("Très élevée", "Une étude technique détaillée est nécessaire."),
            "unknown": ("À vérifier", "La consommation doit être confirmée."),
        })
        return [
            ["Surface", surface_state, surface_text],
            ["Budget", budget_state, budget_text],
            ["Orientation", orientation_state, orientation_text],
            ["Batterie", battery_state, battery_text],
            ["Onduleur", inverter_state, inverter_text],
            ["Consommation", consumption_state, consumption_text],
        ]

    def scenario_rows():
        installation_type = data.get("installation_type_raw")
        scenarios = data.get("scenarios", {})
        if installation_type == "on_grid":
            return [
                ["Économique", clean_text(scenarios.get("economic"), "Petite installation sans batterie."), "Coût réduit.", "Couverture énergétique plus limitée."],
                ["Équilibré", clean_text(scenarios.get("balanced"), "Optimiser surface et puissance."), "Bon compromis surface/budget.", "Dépend de la toiture exploitable."],
                ["Performance", clean_text(scenarios.get("performance"), "Augmenter surface ou améliorer orientation."), "Meilleure production.", "Investissement plus élevé."],
            ]
        if installation_type == "off_grid":
            return [
                ["Économique", clean_text(scenarios.get("economic"), "Limiter les usages prioritaires."), "Réduit le coût initial.", "Autonomie plus limitée."],
                ["Équilibré", clean_text(scenarios.get("balanced"), "Dimensionnement pour besoins essentiels."), "Compromis autonomie/budget.", "Demande une gestion des usages."],
                ["Autonomie renforcée", clean_text(scenarios.get("performance"), "Plus de batterie et marge solaire."), "Sécurité énergétique plus forte.", "Coût plus élevé et ROI plus long."],
            ]
        return [
            ["Économique", clean_text(scenarios.get("economic"), "Réduire ou reporter une partie de la batterie."), "Réduit le coût initial.", "Autonomie plus limitée."],
            ["Équilibré", clean_text(scenarios.get("balanced"), "Puissance solaire correcte avec batterie moyenne."), "Bon compromis technique.", "À confirmer par devis."],
            ["Performance", clean_text(scenarios.get("performance"), "Renforcer batterie et autonomie."), "Meilleure continuité de service.", "Budget plus élevé."],
        ]

    def risks_if_no_correction():
        risks = []
        if "J" in detected:
            risks.append("Budget dépassé par rapport à l’enveloppe déclarée.")
        if "F" in detected or "G" in detected:
            risks.append("Production inférieure aux attentes si la surface réellement exploitable reste limitée.")
        if "W" in detected:
            risks.append("Autonomie insuffisante et batterie déchargée rapidement.")
        if "M" in detected or "T" in detected:
            risks.append("Production réelle fortement réduite sans correction de l’orientation ou de l’ombrage.")
        if "AE" in detected:
            risks.append("Besoin d’une étude technique détaillée à cause d’une consommation très élevée.")
        if not risks:
            risks.append("Écart possible entre estimation et devis réel si les composants ne sont pas confirmés.")
        risks.append("ROI potentiellement plus long si le coût final augmente.")
        return risks

    def recommended_actions():
        actions = [
            "Demander 2 à 3 devis installateurs.",
            "Vérifier la surface réellement exploitable.",
            "Confirmer la capacité batterie si une autonomie est demandée.",
            "Vérifier la compatibilité onduleur/batterie.",
            "Comparer les garanties des marques proposées.",
            "Confirmer le budget final avec un professionnel.",
        ]
        if "J" in detected:
            actions.insert(1, "Revoir le budget ou réduire le dimensionnement.")
        if "F" in detected or "G" in detected:
            actions.insert(2, "Chercher une surface supplémentaire ou accepter une couverture partielle.")
        return actions

    def supplier_rows():
        labels = {
            "Ecowatt": ("Solutions solaires et électriques", "Piste de comparaison pour devis et matériel solaire."),
            "Ecovolt Energy": ("Boutique solaire", "Panneaux, batteries, onduleurs et kits à vérifier."),
            "Misterelec / MRELEC": ("Distributeur électrique et solaire", "Matériel électrique, protections, câbles et composants PV."),
            "Tecas Solar": ("Vente et installation solaire", "À comparer pour accompagnement et devis installateur."),
            "panneauxsolaire.ma": ("Site spécialisé solaire", "Composants PV, batteries, onduleurs et accessoires."),
            "GreenWagic": ("Société solaire", "Vente et installation pour projets résidentiels."),
            "Jumia Maroc": ("Marketplace généraliste", "À utiliser avec prudence : vérifier vendeur, garantie et compatibilité."),
        }
        rows = []
        for supplier in data.get("suppliers_to_compare", []):
            supplier_name = clean_text(supplier)
            site_type, note = labels.get(supplier_name, ("Piste de comparaison", "Disponibilité et garantie à vérifier."))
            rows.append([supplier_name, site_type, note])
        return rows

    surface_check = data.get("surface_check") or {}
    brands = data.get("brands", {})
    selected_inverter = brands.get("selected_inverter", "inverter_on_grid")
    panel_brands = brands.get("panels", {})
    battery_brands = brands.get("battery")
    inverter_brands = brands.get(selected_inverter, {})
    battery_visible = bool(data.get("battery_visible"))

    surface_remark = (
        "Surface suffisante pour la recommandation proposée."
        if surface_check.get("status") == "ok"
        else clean_text(surface_check.get("message"), "Surface à vérifier selon la toiture disponible.")
    )
    estimated_surface = (
        f"environ {surface_check.get('required_area_m2')} m²"
        if surface_check.get("required_area_m2") is not None
        else "à confirmer"
    )
    battery_note = (
        "Capacité à renforcer ou à confirmer selon l’autonomie demandée."
        if "W" in detected
        else "Autonomie et secours, à confirmer par devis installateur."
    )
    inverter_function = (
        "gestion panneaux + batterie + réseau"
        if data.get("installation_type_raw") == "hybrid"
        else "fonctionnement hors réseau avec batterie"
        if data.get("installation_type_raw") == "off_grid"
        else "injection/autoconsommation connectée au réseau"
    )
    budget_gap = (
        "budget insuffisant"
        if "J" in detected
        else "budget proche à confirmer"
        if "I" in detected
        else "budget compatible à confirmer par devis"
    )

    brand_rows = [
        [
            "Panneaux",
            panel_brands.get("type", "panneaux monocristallins performants"),
            ", ".join(panel_brands.get("brands", ["Jinko Solar", "LONGi", "Canadian Solar"])),
        ],
    ]
    if battery_visible and battery_brands:
        brand_rows.append([
            "Batterie",
            battery_brands.get("type", "batterie lithium LiFePO4"),
            ", ".join(battery_brands.get("brands", ["Pylontech", "BYD", "Huawei Luna"])),
        ])
    brand_rows.append([
        "Onduleur",
        inverter_brands.get("type", data.get("inverter_type")),
        ", ".join(inverter_brands.get("brands", [])),
    ])

    kpis = [
        ("Statut global", clean_text(data.get("global_status")), status_level()),
        ("Puissance PV", clean_text(data.get("pv_power_range")), "accent"),
        ("Budget probable", clean_text(data.get("budget_estimated_range")), "warning" if "J" in detected else "success"),
        ("ROI estimatif", clean_text(data.get("roi_range")), "accent"),
        ("Batterie", clean_text(data.get("battery_range")), "warning" if battery_visible else "success"),
        ("Surface", f"{clean_text(data.get('available_area_m2'))} m²", "warning" if surface_check.get("status") == "insufficient" else "success"),
    ]

    elements = [
        Paragraph("Rapport SolarAI — Système photovoltaïque", title_style),
        Paragraph("Dimensionnement intelligent photovoltaïque", subtitle_style),
        add_alert_box(
            f"Statut global : {clean_text(data.get('global_status'))}. Les valeurs sont arrondies ou présentées sous forme d’intervalles.",
            status_level(),
        ),
        Spacer(1, 10),
        add_section_title("1. Informations du projet"),
        add_key_value_table([
            ("Client", clean_text(data.get("client_name"), "Client")),
            ("Ville", clean_text(data.get("city"))),
            ("Date", report_date),
            ("Type de système", clean_text(data.get("installation_type_label"))),
            ("Consommation journalière", f"environ {clean_text(data.get('daily_consumption_kwh'))} kWh/jour"),
            ("Surface disponible", f"{clean_text(data.get('available_area_m2'))} m²"),
            ("Budget déclaré", clean_text(data.get("budget_declared"))),
            ("Orientation", clean_text(data.get("orientation"))),
            ("Inclinaison", f"{clean_text(data.get('tilt_angle'))} degrés"),
            ("Ombrage", clean_text(data.get("shading"))),
            ("Autonomie batterie", f"{clean_text(data.get('autonomy_days'), '0')} jour(s)"),
        ]),
        add_section_title("2. Résumé intelligent IA"),
        add_paragraph(
            f"Le projet concerne une installation {clean_text(data.get('installation_type_label'))} "
            f"pour une consommation d’environ {clean_text(data.get('daily_consumption_kwh'))} kWh/jour. "
            "La recommandation provient du modèle ML, puis elle est vérifiée par les contrôles backend pour éviter "
            "les contradictions entre surface, budget, batterie, onduleur et conditions de toiture."
        ),
        add_section_title("3. Cartes KPI"),
        add_kpi_cards(kpis),
        add_section_title("4. Statut global"),
        add_alert_box(clean_text(data.get("conclusion")), status_level()),
        add_section_title("5. Analyse des contraintes détectées"),
        add_table(
            ["Contrainte", "État", "Analyse"],
            constraints_table_rows(),
            [90, 92, 318],
        ),
        add_section_title("6. Recommandation principale du modèle"),
        add_paragraph(
            f"Le modèle recommande {clean_text(data.get('panels_range'))}, avec une puissance module "
            f"{clean_text(data.get('panel_power_range'))}. La puissance photovoltaïque totale visée est "
            f"{clean_text(data.get('pv_power_range'))}. Ces valeurs sont volontairement arrondies pour rester lisibles."
        ),
    ]

    if surface_check.get("status") == "insufficient":
        elements.extend([
            add_section_title("7. Solution réaliste selon contraintes"),
            add_alert_box(
                f"Avec {clean_text(data.get('available_area_m2'))} m², il est plus réaliste d’installer environ "
                f"{clean_text(surface_check.get('realistic_panel_count'))} panneaux. La couverture énergétique "
                "sera donc partielle sauf si une surface supplémentaire est disponible.",
                "warning",
            ),
        ])

    elements.extend([
        add_page_break_if_needed(),
        add_section_title("8. Panneaux recommandés"),
        add_table(
            ["Type conseillé", "Puissance module", "Nombre recommandé", "Puissance totale", "Surface estimée", "Remarque"],
            [[
                panel_brands.get("type", "panneaux monocristallins performants"),
                clean_text(data.get("panel_power_range")),
                clean_text(data.get("panels_range")),
                clean_text(data.get("pv_power_range")),
                estimated_surface,
                surface_remark,
            ]],
            [82, 78, 82, 78, 74, 106],
        ),
        add_section_title("9. Batterie et autonomie"),
    ])

    if battery_visible:
        elements.append(add_table(
            ["Type conseillé", "Capacité recommandée", "Rôle", "Remarque"],
            [[
                battery_brands.get("type", "batterie lithium LiFePO4") if battery_brands else "batterie lithium LiFePO4",
                clean_text(data.get("battery_range")),
                "autonomie et secours",
                battery_note,
            ]],
            [120, 115, 105, 160],
        ))
    else:
        elements.append(add_alert_box(
            "Aucune batterie n’est nécessaire dans cette configuration, car le système est connecté au réseau "
            "et l’autonomie demandée est de 0 jour.",
            "info",
        ))

    elements.extend([
        add_section_title("10. Onduleur recommandé"),
        add_table(
            ["Type", "Gamme conseillée", "Fonction", "Remarque"],
            [[
                clean_text(data.get("inverter_type")),
                clean_text(data.get("inverter_range")),
                inverter_function,
                "À confirmer selon la puissance réelle installée et la compatibilité batterie.",
            ]],
            [105, 110, 145, 140],
        ),
        add_section_title("11. Budget estimatif"),
        add_table(
            ["Poste", "Estimation", "Remarque"],
            [
                ["Panneaux", "inclus dans l’estimation globale", "À confirmer selon marque, puissance et garantie."],
                ["Batterie", "poste important" if battery_visible else "non nécessaire", "À vérifier seulement si stockage demandé."],
                ["Onduleur", "inclus dans l’estimation globale", "Prix variable selon type on-grid, hybride ou off-grid."],
                ["Installation/protections", "à confirmer par devis", "Inclut protections AC/DC, câbles, pose et mise en service."],
                ["Budget probable total", clean_text(data.get("budget_estimated_range")), "Intervalle issu du modèle et du formatter backend."],
                ["Budget déclaré", clean_text(data.get("budget_declared")), "Budget indiqué par l’utilisateur."],
                ["Écart budget", budget_gap, "À confirmer avec devis installateur."],
            ],
            [132, 168, 200],
        ),
        add_section_title("12. Rentabilité et ROI"),
        add_paragraph(
            f"ROI estimatif : {clean_text(data.get('roi_range'))}. "
            f"Rentabilité : {clean_text(data.get('roi_category'))}. "
            "La rentabilité dépend du prix final installé, de la production réelle, du tarif d’électricité "
            "et du niveau d’autoconsommation."
        ),
        add_section_title("13. Points à vérifier"),
        *add_bullet_list(data.get("points_to_check", [])),
        add_section_title("14. Scénarios proposés"),
        add_table(
            ["Scénario", "Description", "Avantage", "Limite"],
            scenario_rows(),
            [86, 198, 106, 110],
        ),
        add_section_title("15. Marques et matériels à comparer"),
        add_paragraph(
            "Les marques ci-dessous sont des exemples à comparer. Elles ne constituent pas une obligation d’achat "
            "et doivent être validées selon disponibilité locale, garantie et compatibilité technique."
        ),
        add_table(
            ["Matériel", "Type conseillé", "Marques à comparer"],
            brand_rows,
            [90, 170, 240],
        ),
        add_section_title("16. Fournisseurs et sites à comparer"),
        add_paragraph(
            "Ces sites sont proposés comme pistes de comparaison. Il faut vérifier la disponibilité, les garanties, "
            "la compatibilité technique et demander un devis installateur."
        ),
        add_table(
            ["Fournisseur / site", "Type", "Remarque"],
            supplier_rows(),
            [115, 150, 235],
        ),
        add_section_title("17. Guide d’installation"),
        *add_bullet_list(data.get("installation_guide", [])),
        add_section_title("18. Maintenance préventive"),
        *add_bullet_list(data.get("maintenance_tasks", [])),
        add_section_title("19. Risques si aucune correction"),
        *add_bullet_list(risks_if_no_correction()),
        add_section_title("20. Actions recommandées"),
        *add_bullet_list(recommended_actions()),
        add_section_title("21. Impact environnemental"),
        add_paragraph(
            "Cette installation permettrait de réduire la consommation d’énergie non renouvelable. "
            "L’impact exact dépendra de la puissance réellement installée, de la production annuelle "
            "et du taux d’autoconsommation."
        ),
        add_section_title("22. Conclusion IA"),
        add_paragraph(
            clean_text(
                data.get("conclusion"),
                "La configuration doit être validée par un installateur qualifié avec une visite de site.",
            )
        ),
        add_section_title("23. Disclaimer final"),
        add_disclaimer(),
    ])

    doc.build(elements, onFirstPage=draw_page, onLaterPages=draw_page)
    return filename
