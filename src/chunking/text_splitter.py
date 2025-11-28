from typing import List


class MarkdownTextSplitter:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        cleaned = text.replace("\r\n", "\n").strip()
        if not cleaned:
            return []

        tokens = cleaned.split()
        chunks: List[str] = []
        start = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk = " ".join(tokens[start:end])
            chunks.append(chunk)
            if end == len(tokens):
                break
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
        return chunks

