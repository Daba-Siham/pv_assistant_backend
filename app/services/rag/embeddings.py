
# =========================================
# app/services/rag/embeddings.py
# =========================================

from langchain_huggingface import (
    HuggingFaceEmbeddings
)

# =========================================
# EMBEDDINGS
# =========================================

def get_embeddings():

    return HuggingFaceEmbeddings(

        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
