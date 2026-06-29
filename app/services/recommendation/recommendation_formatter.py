import math
from typing import Any

from app.services.recommendation.scenario_detector import detect_project_scenarios
from app.services.shared.utils import has_battery_system, is_on_grid, normalize_installation_type


SCENARIO_LABELS = {
    "A": "Type d'installation : connectée au réseau, sans besoin de batterie.",
    "B": "Type d'installation : autonomie demandée avec un choix on-grid ; une configuration hybride est à comparer.",
    "C": "Type d'installation : hybride, donc batterie recommandée pour l'autonomie et le secours.",
    "D": "Type d'installation : hors réseau, donc batterie obligatoire et marge de sécurité recommandée.",
    "E": "Surface : suffisante pour la recommandation proposée.",
    "F": "Surface : insuffisante pour installer toute la puissance recommandée.",
    "G": "Surface : très insuffisante ; une couverture partielle ou une surface supplémentaire est nécessaire.",
    "H": "Budget : compatible avec l'estimation du modèle.",
    "I": "Budget : proche du coût probable, à confirmer par devis.",
    "J": "Budget : inférieur au coût probable d'une installation complète.",
    "K": "Orientation : Sud, favorable à la production.",
    "L": "Orientation : Est/Ouest, fonctionnelle mais moins performante qu'une orientation Sud.",
    "M": "Orientation : Nord, défavorable pour la production solaire.",
    "N": "Inclinaison : favorable pour une production annuelle équilibrée.",
    "O": "Inclinaison : faible, à vérifier selon la saison et la toiture.",
    "P": "Inclinaison : élevée, à vérifier pour la production et la fixation.",
    "Q": "Ombrage : aucun ombrage déclaré, condition favorable.",
    "R": "Ombrage : faible, à vérifier sur une journée complète.",
    "S": "Ombrage : moyen, optimiseurs ou autre emplacement à envisager.",
    "T": "Ombrage : fort, étude de toiture nécessaire avant validation.",
    "U": "Batterie : non nécessaire pour cette configuration.",
    "V": "Batterie : nécessaire ou fortement recommandée.",
    "W": "Batterie : capacité à renforcer pour l'autonomie demandée.",
    "X": "Batterie : possiblement surdimensionnée, avec impact sur le coût.",
    "Y": "Onduleur : gamme cohérente avec la puissance photovoltaïque visée.",
    "Z": "Onduleur : puissance potentiellement trop faible.",
    "AA": "Onduleur : puissance potentiellement trop élevée par rapport aux panneaux.",
    "AB": "Consommation : faible à moyenne.",
    "AC": "Consommation : moyenne, adaptée à une installation résidentielle standard.",
    "AD": "Consommation : élevée, nécessitant surface et budget suffisants.",
    "AE": "Consommation : très élevée, étude technique détaillée nécessaire.",
    "AF": "Projet : faisable.",
    "AG": "Projet : faisable sous conditions.",
    "AH": "Projet : non faisable dans la configuration actuelle.",
}

SUPPLIERS_TO_COMPARE = [
    "Ecowatt",
    "Ecovolt Energy",
    "Misterelec / MRELEC",
    "Tecas Solar",
    "panneauxsolaire.ma",
    "GreenWagic",
    "Jumia Maroc, uniquement avec vérification du vendeur et de la garantie",
]


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _installation_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def format_money_range(value: Any) -> str:
    amount = _as_float(value)
    if amount is None:
        return "à estimer"

    if amount <= 20000:
        step = 5000
    elif amount <= 100000:
        step = 10000
    else:
        step = 20000

    lower = int(amount // step) * step
    upper = lower + step
    return f"entre {lower:,} et {upper:,} DH".replace(",", " ")


def format_count_range(value: Any) -> str:
    count = _as_float(value)
    if count is None:
        return "à vérifier"

    rounded = max(1, int(round(count)))
    if rounded <= 2:
        return f"environ {rounded} panneaux"
    return f"environ {max(1, rounded - 1)} à {rounded} panneaux"


def format_kwp_range(value: Any) -> str:
    power = _as_float(value)
    if power is None:
        return "à vérifier"

    lower = math.floor(power)
    upper = lower + 1
    if lower < 1:
        return "moins de 1 kWc"
    return f"environ {lower} à {upper} kWc"


def format_panel_power_range(value: Any) -> str:
    power = _as_float(value)
    if power is None:
        return "à vérifier"

    lower = int(power // 50) * 50
    upper = lower + 50
    return f"environ {lower} à {upper} W"


def format_inverter_range(pv_kwp: Any) -> str:
    power = _as_float(pv_kwp)
    if power is None:
        return "à vérifier"

    if power <= 2:
        return "environ 2 à 3 kW"
    if power <= 4:
        return "environ 3 à 5 kW"
    if power <= 6:
        return "environ 5 à 6 kW"
    if power <= 8:
        return "environ 6 à 8 kW"
    if power <= 10:
        return "environ 8 à 10 kW"
    return "plus de 10 kW"


def format_battery_range(
    installation_type: Any,
    autonomy_days: Any,
    battery_required: Any,
    battery_capacity_kwh: Any,
) -> str:
    key = _installation_key(installation_type)
    autonomy = _as_float(autonomy_days) or 0

    if is_on_grid(key):
        return "aucune batterie nécessaire"

    if str(battery_required).strip().lower() in {"no", "false", "0", "none", "non"}:
        return "aucune batterie nécessaire"

    capacity = _as_float(battery_capacity_kwh)
    if capacity is None:
        return "capacité batterie à confirmer"

    if capacity <= 5:
        return "environ 3 à 5 kWh"
    if capacity <= 10:
        return "environ 5 à 10 kWh"
    if capacity <= 15:
        return "environ 10 à 15 kWh"
    if capacity <= 25:
        return "environ 15 à 25 kWh"
    return "plus de 25 kWh"


def format_roi_range(value: Any) -> str:
    roi = _as_float(value)
    if roi is None:
        return "à estimer"

    if roi <= 5:
        return "moins de 5 ans"
    if roi <= 10:
        return "environ 5 à 10 ans"
    if roi <= 15:
        return "environ 10 à 15 ans"
    if roi <= 20:
        return "environ 15 à 20 ans"
    return "plus de 20 ans"


def roi_category(value: Any) -> str:
    roi = _as_float(value)
    if roi is None:
        return "non estimée"
    if roi <= 5:
        return "rapide"
    if roi <= 10:
        return "correcte"
    if roi <= 15:
        return "moyenne"
    return "longue"


def installation_label(value: Any) -> str:
    labels = {
        "on_grid": "connectée au réseau",
        "hybrid": "hybride",
        "hybride": "hybride",
        "off_grid": "autonome hors réseau",
    }
    return labels.get(_installation_key(value), str(value or "à vérifier"))


def inverter_type_label(installation_type: Any) -> str:
    key = _installation_key(installation_type)
    if key == "on_grid":
        return "onduleur on-grid"
    if key in {"hybrid", "hybride"}:
        return "onduleur hybride"
    if key == "off_grid":
        return "onduleur off-grid"
    return "onduleur à vérifier"


def estimate_panel_area(panel_count: Any, area_per_panel: float = 2.0) -> float | None:
    count = _as_float(panel_count)
    if count is None:
        return None
    return round(count * area_per_panel, 1)


def realistic_panel_count_by_area(available_area_m2: Any, area_per_panel: float = 2.0) -> int | None:
    area = _as_float(available_area_m2)
    if area is None:
        return None
    return max(0, int(area // area_per_panel))


def check_surface(panel_count: Any, available_area_m2: Any) -> dict[str, Any] | None:
    required_area = estimate_panel_area(panel_count)
    area = _as_float(available_area_m2)
    realistic_count = realistic_panel_count_by_area(available_area_m2)

    if required_area is None or area is None:
        return None

    if required_area > area:
        return {
            "status": "insufficient",
            "message": (
                f"Surface insuffisante : le modèle recommande {format_count_range(panel_count)}, "
                f"ce qui demande environ {required_area} m². "
                f"Avec {area:g} m², il est plus réaliste d'installer environ {realistic_count} panneaux."
            ),
            "realistic_panel_count": realistic_count,
            "required_area_m2": required_area,
        }

    return {
        "status": "ok",
        "message": "Surface suffisante pour la recommandation proposée.",
        "realistic_panel_count": realistic_count,
        "required_area_m2": required_area,
    }


def build_scenarios(installation_type: Any, surface_status: str | None) -> dict[str, str]:
    key = _installation_key(installation_type)

    if key == "on_grid":
        return {
            "economic": "Réduire le nombre de panneaux pour respecter la surface disponible et le budget.",
            "balanced": "Augmenter légèrement la surface disponible ou choisir des panneaux plus puissants pour mieux couvrir la consommation.",
            "performance": "Prévoir une surface plus grande ou une extension future de panneaux pour atteindre une meilleure couverture énergétique.",
        }

    if key in {"hybrid", "hybride"}:
        return {
            "economic": "Réduire ou reporter une partie de la batterie si le budget est prioritaire.",
            "balanced": "Conserver une bonne puissance solaire et ajuster la capacité batterie selon le budget réel.",
            "performance": "Renforcer la batterie et garder une marge sur l'onduleur pour améliorer l'autonomie.",
        }

    return {
        "economic": "Limiter les usages prioritaires et réduire la puissance installée si le budget est contraint.",
        "balanced": "Dimensionner panneaux et batteries pour couvrir les besoins essentiels avec une marge raisonnable.",
        "performance": "Augmenter la batterie et la surface solaire pour sécuriser l'autonomie hors réseau.",
    }


def build_scenarios_from_analysis(
    installation_type: Any,
    surface_status: str | None,
    scenario_analysis: dict[str, Any],
) -> dict[str, str]:
    if "B" in scenario_analysis.get("detected_scenarios", []):
        return {
            "economic": "Rester en on-grid sans batterie pour limiter le coût.",
            "balanced": "Passer en hybride avec une batterie adaptée si l'autonomie est réellement nécessaire.",
            "performance": "Prévoir une batterie plus tard avec un onduleur hybride compatible.",
        }

    return build_scenarios(installation_type, surface_status)


def scenario_labels_for_user(codes: list[str]) -> list[str]:
    excluded_debug_only = set()
    labels = []
    for code in codes:
        if code in excluded_debug_only:
            continue
        label = SCENARIO_LABELS.get(code)
        if label and label not in labels:
            labels.append(label)
    return labels


def clean_points_to_check(
    checks: list[dict[str, Any]],
    scenario_analysis: dict[str, Any],
    surface_check: dict[str, Any] | None,
) -> list[str]:
    points: list[str] = []

    def add(message: str | None) -> None:
        if message and message not in points:
            points.append(message)

    if surface_check and surface_check.get("status") in {"insufficient", "very_insufficient"}:
        add(surface_check.get("message"))

    for message in scenario_analysis.get("blocking_issues", []):
        if surface_check and surface_check.get("status") != "ok" and "surface" in message.lower():
            continue
        add(message)

    for message in scenario_analysis.get("warnings", []):
        add(message)

    for check in checks:
        code = check.get("code")
        status = check.get("status")
        message = check.get("message")
        if status == "ok":
            continue
        if code == "surface" and surface_check and surface_check.get("status") != "ok":
            continue
        if code == "battery_policy" and "B" in scenario_analysis.get("detected_scenarios", []):
            continue
        if code == "budget" and any(code in scenario_analysis.get("detected_scenarios", []) for code in ["H", "I", "J"]):
            continue
        if code == "battery_capacity" and any(code in scenario_analysis.get("detected_scenarios", []) for code in ["W", "X"]):
            continue
        if code == "inverter_power" and any(code in scenario_analysis.get("detected_scenarios", []) for code in ["Y", "Z", "AA"]):
            continue
        add(message)

    return points or ["Aucun point bloquant détecté à ce stade."]


def brand_recommendations(installation_type: Any, battery_visible: bool) -> dict[str, Any]:
    key = _installation_key(installation_type)
    inverter_key = "inverter_off_grid" if key == "off_grid" else "inverter_hybrid" if key in {"hybrid", "hybride"} else "inverter_on_grid"

    brands = {
        "panels": {
            "type": "panneaux monocristallins performants",
            "brands": ["Jinko Solar", "LONGi", "Canadian Solar"],
        },
        "inverter_on_grid": {
            "type": "onduleur on-grid",
            "brands": ["Huawei", "SMA", "Fronius"],
        },
        "inverter_hybrid": {
            "type": "onduleur hybride",
            "brands": ["Huawei", "Victron", "GoodWe"],
        },
        "inverter_off_grid": {
            "type": "onduleur off-grid ou hybride compatible batterie",
            "brands": ["Victron", "Growatt", "Deye"],
        },
        "selected_inverter": inverter_key,
    }

    if battery_visible:
        brands["battery"] = {
            "type": "batterie lithium LiFePO4",
            "brands": ["Pylontech", "BYD", "Huawei Luna"],
        }

    return brands


def installation_guide(data: dict[str, Any]) -> list[str]:
    guide = [
        "Vérifier la surface réellement exploitable sur la toiture.",
        "Prioriser une zone sans ombrage pendant les heures principales de production.",
        "Vérifier la compatibilité entre panneaux, onduleur, protections AC/DC et câbles.",
        "Faire valider le dimensionnement par un installateur qualifié.",
    ]

    if data.get("orientation") and str(data["orientation"]).lower() != "sud":
        guide.insert(2, "Si possible, améliorer l'orientation vers le Sud, Sud-Est ou Sud-Ouest.")

    if data.get("tilt_angle") and not (25 <= float(data["tilt_angle"]) <= 35):
        guide.insert(3, "Si la toiture le permet, viser une inclinaison plus proche de 25° à 35°.")

    if data.get("battery_visible"):
        guide.extend([
            "Prévoir un espace batterie ventilé, protégé et accessible.",
            "Vérifier la compatibilité tension/capacité entre batterie et onduleur.",
        ])

    return guide


def maintenance_tasks(data: dict[str, Any]) -> list[str]:
    tasks = [
        "Nettoyer les panneaux régulièrement selon la poussière locale.",
        "Vérifier les connexions électriques et les protections AC/DC.",
        "Contrôler l'état de l'onduleur et surveiller les alertes.",
        "Comparer la production réelle avec la production attendue.",
        "Faire une vérification annuelle complète par un professionnel.",
    ]

    if data.get("battery_visible"):
        tasks.insert(3, "Surveiller l'état de charge batterie et éviter les décharges profondes répétées.")

    return tasks


def environmental_impact(data: dict[str, Any]) -> dict[str, str]:
    return {
        "summary": (
            "Cette installation permettrait de réduire la consommation d'énergie non renouvelable "
            "et de limiter les émissions de CO2. L'impact exact dépendra de la puissance réellement "
            "installée, de la production annuelle et du taux d'autoconsommation."
        )
    }


def personalized_conclusion(data: dict[str, Any], scenario_analysis: dict[str, Any]) -> str:
    status = scenario_analysis.get("global_status")
    key = _installation_key(data.get("installation_type_raw"))

    if status == "non faisable dans cette configuration":
        return (
            "Le projet doit être ajusté avant validation. Les contraintes détectées rendent la configuration actuelle "
            "difficile à recommander sans correction de la surface, de l'orientation, de l'ombrage ou du budget."
        )

    if data.get("surface_check", {}).get("status") in {"insufficient", "very_insufficient"}:
        return (
            "Le projet n'est pas impossible, mais la surface disponible limite la puissance installable. "
            "La meilleure option est d'augmenter la surface solaire, d'accepter une couverture partielle ou "
            "de réduire l'objectif énergétique."
        )

    if key == "off_grid":
        return (
            "Le projet est techniquement intéressant, mais une installation hors réseau exige une batterie fiable, "
            "une marge de sécurité et un budget suffisant. La validation par un installateur est indispensable."
        )

    if key in {"hybrid", "hybride"}:
        return (
            "Le projet est cohérent pour une solution hybride, sous réserve d'ajuster la capacité batterie au budget "
            "et à l'autonomie réellement souhaitée."
        )

    return (
        "Le projet est cohérent pour une installation connectée au réseau. La priorité est de valider la surface, "
        "le devis installateur et l'orientation réelle avant lancement."
    )


def build_user_recommendation_data(
    user_inputs: dict[str, Any],
    ml_result: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    panel_count = ml_result.get("panel_count")
    panel_power_w = ml_result.get("panel_power_w")
    count = _as_float(panel_count)
    power = _as_float(panel_power_w)
    pv_kwp = _as_float(ml_result.get("total_panel_power_kwp"))

    if pv_kwp is None and count is not None and power is not None:
        pv_kwp = round((count * power) / 1000, 2)

    installation_type = user_inputs.get("installation_type")
    autonomy_days = user_inputs.get("autonomy_days") or user_inputs.get("battery_autonomy_days") or 0
    available_area = user_inputs.get("available_area_m2") or user_inputs.get("surface")
    surface_check = check_surface(panel_count=panel_count, available_area_m2=available_area)
    scenario_analysis = detect_project_scenarios(user_inputs=user_inputs, ml_result=ml_result)
    key = _installation_key(installation_type)
    battery_required = ml_result.get("battery_required") or ml_result.get("battery_needed")
    battery_visible = has_battery_system(installation_type, ml_result.get("battery_capacity_kwh"))
    surface_status = surface_check.get("status") if surface_check else None

    if is_on_grid(key):
        autonomy_days = 0

    recommendation_data = {
        "city": user_inputs.get("city") or "votre région",
        "installation_type_raw": installation_type,
        "installation_type_label": installation_label(installation_type),
        "daily_consumption_kwh": round(_as_float(user_inputs.get("daily_consumption_kwh_normalized")) or 0, 1),
        "available_area_m2": round(_as_float(available_area) or 0, 1),
        "budget_declared": format_money_range(user_inputs.get("budget")),
        "orientation": user_inputs.get("orientation"),
        "tilt_angle": round(_as_float(user_inputs.get("tilt_angle")) or 0),
        "shading": user_inputs.get("shading") or user_inputs.get("shade_level"),
        "autonomy_days": round(_as_float(autonomy_days) or 0, 1),
        "global_status": scenario_analysis["global_status"],
        "detected_scenarios": scenario_analysis["detected_scenarios"],
        "feasibility": scenario_analysis["global_status"],
        "panels_range": format_count_range(panel_count),
        "panel_power_range": format_panel_power_range(panel_power_w),
        "pv_power_range": format_kwp_range(pv_kwp),
        "battery_visible": battery_visible,
        "battery_range": format_battery_range(
            installation_type=installation_type,
            autonomy_days=autonomy_days,
            battery_required=battery_required,
            battery_capacity_kwh=ml_result.get("battery_capacity_kwh"),
        ),
        "inverter_type": (
            "onduleur on-grid si réseau seul, onduleur hybride si autonomie conservée"
            if "B" in scenario_analysis["detected_scenarios"]
            else inverter_type_label(installation_type)
        ),
        "inverter_range": format_inverter_range(pv_kwp),
        "budget_estimated_range": format_money_range(
            ml_result.get("estimated_total_cost_dh") or ml_result.get("estimated_cost")
        ),
        "roi_range": format_roi_range(ml_result.get("roi_years")),
        "roi_category": roi_category(ml_result.get("roi_years")),
        "surface_check": surface_check,
        "scenarios": build_scenarios_from_analysis(installation_type, surface_status, scenario_analysis),
        "scenario_analysis": scenario_analysis,
        "checks": checks,
    }

    recommendation_data["constraints_analysis"] = scenario_labels_for_user(
        scenario_analysis["detected_scenarios"]
    )
    recommendation_data["points_to_check"] = clean_points_to_check(
        checks=checks,
        scenario_analysis=scenario_analysis,
        surface_check=surface_check,
    )
    recommendation_data["brands"] = brand_recommendations(
        installation_type=installation_type,
        battery_visible=battery_visible,
    )
    recommendation_data["suppliers_to_compare"] = SUPPLIERS_TO_COMPARE
    recommendation_data["installation_guide"] = installation_guide(recommendation_data)
    recommendation_data["maintenance_tasks"] = maintenance_tasks(recommendation_data)
    recommendation_data["environmental_impact"] = environmental_impact(recommendation_data)
    recommendation_data["conclusion"] = personalized_conclusion(
        data=recommendation_data,
        scenario_analysis=scenario_analysis,
    )

    return recommendation_data


def format_ml_recommendation(
    user_inputs: dict[str, Any],
    ml_result: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    recommendation_data = build_user_recommendation_data(user_inputs, ml_result, checks)

    return {
        "project_summary": {
            "city": recommendation_data["city"],
            "installation_type": recommendation_data["installation_type_label"],
            "daily_consumption_kwh": recommendation_data["daily_consumption_kwh"],
            "available_area_m2": recommendation_data["available_area_m2"],
            "budget_dh": user_inputs.get("budget"),
        },
        "user_friendly_recommendation": {
            "feasibility": recommendation_data["feasibility"],
            "system_size": recommendation_data["pv_power_range"],
            "panels": recommendation_data["panels_range"],
            "panel_power": recommendation_data["panel_power_range"],
            "pv_power": recommendation_data["pv_power_range"],
            "battery": recommendation_data["battery_range"],
            "battery_visible": recommendation_data["battery_visible"],
            "inverter_type": recommendation_data["inverter_type"],
            "inverter": recommendation_data["inverter_range"],
            "budget_estimation": recommendation_data["budget_estimated_range"],
            "budget_status": "à vérifier selon devis installateur",
            "roi": recommendation_data["roi_range"],
            "roi_category": recommendation_data["roi_category"],
            "orientation": user_inputs.get("orientation") or "à vérifier",
            "tilt": f"environ {recommendation_data['tilt_angle']}°",
        },
        "recommendation_data": recommendation_data,
        "checks": checks,
    }
