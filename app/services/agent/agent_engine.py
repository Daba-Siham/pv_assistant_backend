import re

from app.services.calculation.calculation_service import calculate_system
from app.services.rag.rag_engine import ask_question


conversation_memory = []


def detect_solar_project(question):
    keywords = [
        "kwh",
        "budget",
        "surface",
        "m2",
        "m²",
        "consommation",
        "orientation",
        "ville",
        "autonomie",
    ]
    question = question.lower()
    return any(word in question for word in keywords)


def extract_project_data(question):
    question = question.lower()

    city = "casablanca"
    if "marrakech" in question:
        city = "marrakech"
    elif "agadir" in question:
        city = "agadir"
    elif "oujda" in question:
        city = "oujda"
    elif "paris" in question:
        city = "paris"

    consumption = 10
    consumption_match = re.search(r"(\d+)\s*kwh", question)
    if consumption_match:
        consumption = float(consumption_match.group(1))

    surface = 20
    surface_match = re.search(r"(\d+)\s*m", question)
    if surface_match:
        surface = float(surface_match.group(1))

    budget = 30000
    budget_match = re.search(r"(\d+)\s*dh", question)
    if budget_match:
        budget = float(budget_match.group(1))

    orientation = "Sud"
    if "est" in question:
        orientation = "Est"
    elif "ouest" in question:
        orientation = "Ouest"

    return {
        "city": city,
        "daily_consumption_kwh": consumption,
        "available_area_m2": surface,
        "budget": budget,
        "orientation": orientation,
        "installation_type": "on-grid",
        "autonomy_days": 1,
        "shade_factor": 0.1,
        "roof_type": "terrasse",
        "distance_to_load_m": 10,
    }


def process_chat(question):
    global conversation_memory

    try:
        conversation_memory.append({"role": "user", "content": question})

        if detect_solar_project(question):
            data = extract_project_data(question)

            class FakeData:
                pass

            fake = FakeData()
            for key, value in data.items():
                setattr(fake, key, value)

            result = calculate_system(fake)
            final_prompt = f"""
Utilisateur :
{question}

Résultat backend :
{result}

Explique le résultat clairement comme un expert photovoltaïque.

Donne :
- pourquoi ce choix
- avantages
- conseils
- optimisation possible

Ne jamais inventer des chiffres.
Utilise uniquement les valeurs backend.
Réponds dans la même langue que le dernier message utilisateur.
"""
            response = ask_question(final_prompt)
        else:
            response = ask_question(question)

        conversation_memory.append({"role": "assistant", "content": response})
        conversation_memory = conversation_memory[-10:]
        return response

    except Exception as e:
        print("AGENT ERROR =", e)
        return "Erreur IA pendant le traitement."
