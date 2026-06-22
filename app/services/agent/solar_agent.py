from app.services.calculation.calculation_service import calculate_system

def detect_solar_project(question):

    keywords = [
        "kwh",
        "budget",
        "m²",
        "surface",
        "orientation",
        "ville",
        "consommation"
    ]

    return any(word in question.lower() for word in keywords)