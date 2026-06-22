import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.services.rag.chunker import TextChunker
from app.services.rag.loader import DocumentLoader


class SimpleVectorStore:
    def __init__(self, store_dir: Path | None = None):
        self.store_dir = store_dir or settings.VECTOR_STORE_DIR
        self.store_path = self.store_dir / "rag_store.pkl"

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            max_features=5000
        )

        self.chunks: list[dict] = []
        self.matrix = None

    def build(self) -> dict:
        loader = DocumentLoader()
        chunker = TextChunker()

        documents = loader.load_documents()
        chunks = chunker.chunk_documents(documents)

        if not chunks:
            return {
                "success": False,
                "message": "Aucun document RAG trouvé",
                "chunks_count": 0
            }

        texts = [chunk["content"] for chunk in chunks]
        matrix = self.vectorizer.fit_transform(texts)

        self.chunks = chunks
        self.matrix = matrix

        self._save()

        return {
            "success": True,
            "message": "Base RAG construite avec succès",
            "documents_count": len(documents),
            "chunks_count": len(chunks)
        }

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        self._ensure_loaded()

        if self.matrix is None or not self.chunks:
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.matrix).flatten()

        ranked_indexes = similarities.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indexes:
            score = float(similarities[index])

            if score <= 0:
                continue

            chunk = self.chunks[index]

            results.append(
                {
                    "source": chunk["source"],
                    "path": chunk["path"],
                    "content": chunk["content"],
                    "score": score
                }
            )

        return results

    def _save(self) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "vectorizer": self.vectorizer,
            "chunks": self.chunks,
            "matrix": self.matrix
        }

        with open(self.store_path, "wb") as file:
            pickle.dump(data, file)

    def _load(self) -> bool:
        if not self.store_path.exists():
            return False

        with open(self.store_path, "rb") as file:
            data = pickle.load(file)

        self.vectorizer = data["vectorizer"]
        self.chunks = data["chunks"]
        self.matrix = data["matrix"]

        return True

    def _ensure_loaded(self) -> None:
        if self.matrix is None or not self.chunks:
            loaded = self._load()

            if not loaded:
                self.build()