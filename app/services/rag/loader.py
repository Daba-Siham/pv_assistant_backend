from pathlib import Path

from app.config import settings


class DocumentLoader:
    def __init__(self, docs_dir: Path | None = None):
        self.docs_dir = docs_dir or settings.RAG_DOCS_DIR

    def load_documents(self) -> list[dict]:
        documents = []

        if not self.docs_dir.exists():
            return documents

        for file_path in self.docs_dir.iterdir():
            if file_path.is_file():
                content = self.load_file(file_path)

                if content:
                    documents.append(
                        {
                            "source": file_path.name,
                            "path": str(file_path),
                            "content": content
                        }
                    )

        return documents

    def load_file(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()

        if suffix in [".txt", ".md"]:
            return self._load_text_file(file_path)

        if suffix == ".pdf":
            return self._load_pdf_file(file_path)

        return ""

    def _load_text_file(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1")
        except Exception:
            return ""

    def _load_pdf_file(self, file_path: Path) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            pages_text = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            return "\n".join(pages_text)

        except Exception:
            return ""