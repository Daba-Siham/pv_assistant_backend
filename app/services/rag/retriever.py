from app.services.rag.vector_store import SimpleVectorStore


class SimpleRetriever:
    def __init__(self):
        self.store = SimpleVectorStore()

    def invoke(self, query: str):
        results = self.store.search(query, top_k=4)

        return [
            type(
                "Document",
                (),
                {"page_content": result["content"]}
            )()
            for result in results
        ]


def get_retriever():
    return SimpleRetriever()


class RAGRetriever(SimpleRetriever):
    def retrieve_context_only(self, query: str, top_k: int = 4) -> str:
        results = self.store.search(query, top_k=top_k)
        return "\n\n".join(result["content"] for result in results)
