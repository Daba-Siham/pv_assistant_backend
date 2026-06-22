# =========================================
# app/services/rag/rag_engine.py
# =========================================

import os
from dotenv import load_dotenv
from groq import Groq

from app.services.rag.retriever import get_retriever

# =========================================
# LOAD ENV
# =========================================

load_dotenv()

# =========================================
# GROQ CLIENT FACTORY
# =========================================

def get_groq_client():
    """
    Crée le client Groq uniquement quand nécessaire
    (évite les erreurs d'import FastAPI / uvicorn)
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY introuvable. Vérifie ton fichier .env"
        )

    return Groq(api_key=api_key)


# =========================================
# SYSTEM PROMPT
# =========================================

SYSTEM_PROMPT = """
Tu es un expert photovoltaïque marocain.

Tu aides les utilisateurs à :

- dimensionner installation solaire
- choisir panneaux
- choisir batteries
- calculer ROI
- optimiser orientation
- expliquer photovoltaïque simplement

Règles :
- réponses claires
- utiliser les documents fournis (RAG)
- ne jamais inventer de chiffres
- être précis et professionnel
- répondre en français
"""


# =========================================
# ASK QUESTION
# =========================================

def ask_question(question: str):

    try:
        # 1. Retriever
        retriever = get_retriever()

        docs = retriever.invoke(question)

        context = "\n\n".join(
            doc.page_content for doc in docs
        )

        # 2. Prompt final
        final_prompt = f"""
CONTEXTE DOCUMENTS :

{context}

QUESTION :

{question}
"""

        # 3. Client Groq (créé au moment de l'appel)
        client = get_groq_client()

        # 4. Appel LLM
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": final_prompt
                }
            ],
            temperature=0.3,
            max_tokens=1200
        )

        # 5. Réponse finale
        answer = completion.choices[0].message.content

        return answer

    except Exception as e:
        print("RAG ERROR =", e)
        return "Erreur pendant génération IA."