import os
from langchain_core.documents import Document
from pathlib import Path


def load_documents():

    documents = []

    
    BASE_DIR = Path(__file__).resolve().parents[3]
    data_path = BASE_DIR / "data" / "rag_docs"

    for file in os.listdir(data_path):

        if file.endswith(".md"):

            with open(
                os.path.join(data_path, file),
                "r",
                encoding="utf-8"
            ) as f:

                text = f.read()

                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": file}
                    )
                )

    return documents