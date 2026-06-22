class TextChunker:
    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_documents(self, documents: list[dict]) -> list[dict]:
        chunks = []

        for document in documents:
            document_chunks = self.chunk_text(document["content"])

            for index, chunk in enumerate(document_chunks):
                chunks.append(
                    {
                        "chunk_id": f"{document['source']}_{index}",
                        "source": document["source"],
                        "path": document["path"],
                        "content": chunk,
                        "chunk_index": index
                    }
                )

        return chunks

    def chunk_text(self, text: str) -> list[str]:
        if not text:
            return []

        clean_text = self._clean_text(text)

        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        chunks = []
        start = 0

        while start < len(clean_text):
            end = start + self.chunk_size
            chunk = clean_text[start:end]

            last_dot = chunk.rfind(".")
            last_newline = chunk.rfind("\n")

            split_position = max(last_dot, last_newline)

            if split_position > int(self.chunk_size * 0.5):
                chunk = chunk[: split_position + 1]
                end = start + split_position + 1

            chunks.append(chunk.strip())

            start = max(end - self.chunk_overlap, end)

        return [chunk for chunk in chunks if chunk]

    def _clean_text(self, text: str) -> str:
        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)