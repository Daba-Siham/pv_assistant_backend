from pathlib import Path
from langchain_community.vectorstores import FAISS

from app.services.rag.loader import load_documents
from app.services.rag.splitter import split_documents
from app.services.rag.embeddings import get_embeddings


BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "faiss_index"


def create_vectorstore():
    docs = load_documents()
    chunks = split_documents(docs)
    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    vectorstore.save_local(str(DB_PATH))

    print(f"FAISS index créé dans : {DB_PATH}")