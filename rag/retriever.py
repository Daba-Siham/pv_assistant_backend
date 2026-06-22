from pathlib import Path
from langchain_community.vectorstores import FAISS

from app.services.rag.embeddings import get_embeddings
from app.services.rag.vectorstore import create_vectorstore


BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "faiss_index"


def get_retriever():
    index_file = DB_PATH / "index.faiss"
    pkl_file = DB_PATH / "index.pkl"

    if not index_file.exists() or not pkl_file.exists():
        create_vectorstore()

    embeddings = get_embeddings()

    db = FAISS.load_local(
        str(DB_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return db.as_retriever(
        search_kwargs={"k": 3}
    )