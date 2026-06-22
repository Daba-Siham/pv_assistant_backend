from app.services.rag.vector_store import SimpleVectorStore


def main():
    print("\n===== BUILDING SOLARAI RAG INDEX =====\n")
    store = SimpleVectorStore()
    print(f"Documents directory: data/rag_docs")
    print(f"Vector store path: {store.store_path}")
    result = store.build()
    print(result)

    if not result.get("success"):
        raise SystemExit(1)

    print("\nRAG index created successfully.\n")


if __name__ == "__main__":
    main()
