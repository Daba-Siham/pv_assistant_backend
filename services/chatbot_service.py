import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from rag.retriever import get_retriever


load_dotenv()

retriever = get_retriever()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
    max_tokens=500,
)

chat_history = []


def build_context(docs, max_chars=3000):
    unique_docs = []
    seen = set()

    for doc in docs:
        text = doc.page_content.strip()

        if text not in seen:
            seen.add(text)
            unique_docs.append(text)

    context = "\n\n".join(unique_docs)
    return context[:max_chars]


def chat(question):
    docs = retriever.get_relevant_documents(question)
    docs = docs[:3]
    context = build_context(docs)
    history_text = "\n".join(chat_history[-4:])

    prompt = f"""
You are SolarAI.

Photovoltaic expert.

Answer clearly and simply.
Answer in the same language as the user's last message.

History:
{history_text}

Context:
{context}

User's last message:
{question}

Answer:
"""

    response = llm.invoke(prompt)
    answer = response.content

    chat_history.append(f"Human: {question}")
    chat_history.append(f"Assistant: {answer}")

    return answer
