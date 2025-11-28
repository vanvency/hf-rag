from pathlib import Path

import fitz

from .base import BaseParser


class PDFParser(BaseParser):
    content_type = "application/pdf"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> str:
        document = fitz.open(str(path))
        texts = []
        for page in document:
            texts.append(page.get_text("text"))
        return "\n".join(texts)

