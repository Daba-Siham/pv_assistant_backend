from reportlab.platypus import Paragraph, Spacer, PageBreak
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv


load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
    max_tokens=500
)

def build_recommendation_page(elements, styles, data):

    title = Paragraph(
        "Recommandations IA",
        styles["Heading1"]
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    try:

        prompt = f"""
        Donne des recommandations pour une installation solaire.
        Consommation: {data.get("consumption", "N/A")}
        Budget: {data.get("budget", "N/A")}
        """

        response = llm.invoke(prompt)

        recommendation_text = response.content

    except Exception as e:

        recommendation_text = f"Erreur IA : {str(e)}"

    content = Paragraph(
        recommendation_text,
        styles["BodyText"]
    )

    elements.append(content)

    elements.append(PageBreak())

    return elements