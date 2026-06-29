from typing import Any

from app.services.shared.utils import is_on_grid


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _installation_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _shade_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _orientation_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _battery_required(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "oui", "1", "needed", "necessaire"}


def _add(target: list[str], item: str) -> None:
    if item and item not in target:
        target.append(item)


def detect_project_scenarios(user_inputs: dict[str, Any], ml_result: dict[str, Any]) -> dict[str, Any]:
    installation_type = _installation_key(user_inputs.get("installation_type"))
    autonomy_days = _as_float(user_inputs.get("autonomy_days")) or 0
    if is_on_grid(installation_type):
        autonomy_days = 0
    daily_consumption = _as_float(user_inputs.get("daily_consumption_kwh_normalized"))
    available_area = _as_float(user_inputs.get("available_area_m2"))
    budget = _as_float(user_inputs.get("budget"))
    orientation = _orientation_key(user_inputs.get("orientation"))
    tilt = _as_float(user_inputs.get("tilt_angle"))
    shading = _shade_key(user_inputs.get("shading"))

    panel_count = _as_float(ml_result.get("panel_count"))
    pv_kwp = _as_float(ml_result.get("total_panel_power_kwp"))
    panel_power = _as_float(ml_result.get("panel_power_w"))
    if pv_kwp is None and panel_count is not None and panel_power is not None:
        pv_kwp = panel_count * panel_power / 1000

    estimated_cost = _as_float(ml_result.get("estimated_cost") or ml_result.get("estimated_total_cost_dh"))
    battery_capacity = _as_float(ml_result.get("battery_capacity_kwh"))
    inverter_kw = _as_float(ml_result.get("inverter_power_kw") or ml_result.get("inverter_rated_power_kw"))
    battery_required = _battery_required(ml_result.get("battery_needed") or ml_result.get("battery_required"))
    if is_on_grid(installation_type):
        battery_required = False

    detected: list[str] = []
    blocking_issues: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    info_messages: list[str] = []

    # Installation scenarios A-D
    if installation_type == "on_grid" and autonomy_days == 0:
        _add(detected, "A")
        _add(info_messages, "Comme l'installation est connectée au réseau et que l'autonomie demandée est de 0 jour, aucune batterie n'est nécessaire.")
    elif installation_type == "on_grid" and autonomy_days > 0:
        _add(detected, "B")
        _add(warnings, "Vous avez choisi un système connecté au réseau, mais vous demandez une autonomie batterie. Une installation hybride serait plus adaptée.")
        _add(recommendations, "Comparer un scénario on-grid sans batterie et un scénario hybride avec batterie.")
    elif installation_type in {"hybrid", "hybride"}:
        _add(detected, "C")
        _add(info_messages, "Comme le système est hybride, une batterie est nécessaire ou fortement recommandée.")
    elif installation_type == "off_grid":
        _add(detected, "D")
        _add(info_messages, "Comme le système est hors réseau, la batterie est obligatoire avec une marge de sécurité.")

    # Surface scenarios E-G
    required_area = panel_count * 2 if panel_count is not None else None
    realistic_panel_count = int(available_area // 2) if available_area is not None else None
    surface_status = "unknown"
    if required_area is not None and available_area is not None:
        if available_area >= required_area:
            surface_status = "ok"
            _add(detected, "E")
            _add(info_messages, "La surface disponible semble suffisante pour installer le nombre de panneaux recommandé.")
        else:
            ratio = realistic_panel_count / panel_count if panel_count and realistic_panel_count is not None else 0
            if ratio < 0.5:
                surface_status = "very_insufficient"
                _add(detected, "G")
                _add(blocking_issues, "La surface disponible est trop limitée pour couvrir correctement la consommation.")
                _add(recommendations, "Prévoir une couverture partielle, ajouter une autre toiture ou réduire l'objectif de couverture.")
            else:
                surface_status = "insufficient"
                _add(detected, "F")
                _add(blocking_issues, "La surface disponible est insuffisante pour installer tous les panneaux recommandés.")
                _add(recommendations, "Réduire le nombre de panneaux ou augmenter la surface utilisable.")

    # Budget scenarios H-J
    budget_status = "unknown"
    if budget is not None and estimated_cost is not None:
        if budget >= estimated_cost:
            budget_status = "ok"
            _add(detected, "H")
            _add(info_messages, "Le budget déclaré semble compatible avec l'installation recommandée.")
        elif budget >= estimated_cost * 0.85:
            budget_status = "near"
            _add(detected, "I")
            _add(warnings, "Le budget est proche du coût probable. Un devis réel permettra de confirmer la faisabilité.")
        else:
            budget_status = "insufficient"
            _add(detected, "J")
            _add(warnings, "Le budget déclaré est inférieur au coût probable d'une installation complète.")
            _add(recommendations, "Augmenter le budget ou réduire le dimensionnement.")

    # Orientation K-M
    orientation_status = "unknown"
    if orientation == "sud":
        orientation_status = "good"
        _add(detected, "K")
        _add(info_messages, "L'orientation Sud est favorable pour maximiser la production solaire.")
    elif orientation in {"est", "ouest"}:
        orientation_status = "acceptable"
        _add(detected, "L")
        _add(warnings, "L'orientation choisie peut fonctionner, mais elle produit généralement moins qu'une orientation Sud.")
    elif orientation == "nord":
        orientation_status = "bad"
        _add(detected, "M")
        _add(blocking_issues, "L'orientation Nord est défavorable pour la production solaire.")
        _add(recommendations, "Vérifier s'il existe une toiture orientée Sud, Sud-Est ou Sud-Ouest.")

    # Tilt N-P
    tilt_status = "unknown"
    if tilt is not None:
        if 25 <= tilt <= 35:
            tilt_status = "good"
            _add(detected, "N")
            _add(info_messages, "L'inclinaison est favorable pour une production annuelle équilibrée.")
        elif tilt < 20:
            tilt_status = "low"
            _add(detected, "O")
            _add(warnings, "L'inclinaison est faible. Elle peut fonctionner, mais la production peut être moins optimale selon la saison.")
        elif tilt > 40:
            tilt_status = "high"
            _add(detected, "P")
            _add(warnings, "L'inclinaison est élevée. Il faut vérifier son impact sur la production annuelle et la fixation des panneaux.")

    # Shading Q-T
    shading_status = "unknown"
    if shading in {"aucun", "none", "pas", "no"}:
        shading_status = "none"
        _add(detected, "Q")
        _add(info_messages, "L'absence d'ombrage est favorable à la production.")
    elif shading in {"faible", "low"}:
        shading_status = "low"
        _add(detected, "R")
        _add(warnings, "L'ombrage est faible, mais il faut le vérifier sur la journée complète.")
    elif shading in {"moyen", "medium", "partiel"}:
        shading_status = "medium"
        _add(detected, "S")
        _add(warnings, "L'ombrage peut réduire la production. Des optimiseurs ou un autre emplacement peuvent être nécessaires.")
    elif shading in {"fort", "high", "important"}:
        shading_status = "high"
        _add(detected, "T")
        _add(blocking_issues, "L'ombrage est une contrainte importante et peut fortement réduire la production réelle.")
        _add(recommendations, "Réaliser une étude de toiture avant validation.")

    # Battery U-X
    battery_status = "unknown"
    if installation_type == "on_grid" and autonomy_days == 0:
        battery_status = "not_needed"
        _add(detected, "U")
    elif installation_type == "on_grid" and autonomy_days > 0:
        battery_status = "hybrid_recommended"
    elif installation_type in {"hybrid", "hybride", "off_grid"}:
        battery_status = "needed"
        _add(detected, "V")
        required_battery = None
        if daily_consumption is not None and autonomy_days > 0:
            required_battery = daily_consumption * autonomy_days / 0.72
        if required_battery is not None and battery_capacity is not None:
            if battery_capacity < required_battery * 0.9:
                battery_status = "insufficient"
                _add(detected, "W")
                _add(warnings, "La capacité batterie semble insuffisante pour l'autonomie demandée.")
            elif battery_capacity > required_battery * 2.2:
                battery_status = "oversized"
                _add(detected, "X")
                _add(warnings, "La batterie semble surdimensionnée, ce qui augmente le coût et le ROI.")
    elif not battery_required:
        battery_status = "not_needed"
        _add(detected, "U")

    # Inverter Y-AA
    inverter_status = "unknown"
    if pv_kwp is not None and inverter_kw is not None:
        if inverter_kw < pv_kwp * 0.75:
            inverter_status = "too_small"
            _add(detected, "Z")
            _add(warnings, "La puissance de l'onduleur semble trop faible par rapport aux panneaux.")
        elif inverter_kw > pv_kwp * 1.6:
            inverter_status = "too_large"
            _add(detected, "AA")
            _add(warnings, "La puissance de l'onduleur semble élevée par rapport à la puissance solaire installée.")
        else:
            inverter_status = "ok"
            _add(detected, "Y")
            _add(info_messages, "La gamme d'onduleur semble cohérente avec la puissance photovoltaïque prévue.")

    # Consumption AB-AE
    consumption_status = "unknown"
    if daily_consumption is not None:
        if daily_consumption <= 5:
            consumption_status = "low"
            _add(detected, "AB")
            _add(info_messages, "Le besoin énergétique est faible à moyen. Une petite installation peut suffire.")
        elif daily_consumption <= 10:
            consumption_status = "medium"
            _add(detected, "AC")
            _add(info_messages, "Le besoin énergétique est moyen. Une installation résidentielle standard peut être adaptée.")
        elif daily_consumption <= 20:
            consumption_status = "high"
            _add(detected, "AD")
            _add(warnings, "Le besoin énergétique est élevé. Il faut prévoir une surface suffisante et un budget plus important.")
        else:
            consumption_status = "very_high"
            _add(detected, "AE")
            _add(blocking_issues, "Le besoin énergétique est très élevé. Une étude technique détaillée est nécessaire.")

    severe_codes = {"G", "M", "T", "AE"}
    if detected and severe_codes.intersection(detected):
        global_status = "non faisable dans cette configuration"
        _add(detected, "AH")
    elif blocking_issues or warnings:
        global_status = "faisable sous conditions"
        _add(detected, "AG")
    else:
        global_status = "faisable"
        _add(detected, "AF")

    return {
        "global_status": global_status,
        "detected_scenarios": detected,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "info_messages": info_messages,
        "recommendations": recommendations,
        "surface": {
            "status": surface_status,
            "required_area_m2": round(required_area, 1) if required_area is not None else None,
            "realistic_panel_count": realistic_panel_count,
        },
        "budget": {"status": budget_status},
        "orientation": {"status": orientation_status},
        "tilt": {"status": tilt_status},
        "shading": {"status": shading_status},
        "battery": {"status": battery_status},
        "inverter": {"status": inverter_status},
        "consumption": {"status": consumption_status},
    }
