from pathlib import Path

from docx import Document

from .base import BaseParser


class DocParser(BaseParser):
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    SUPPORTED_EXTENSIONS = {".docx"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, path: Path) -> str:
        document = Document(str(path))
        lines = [para.text for para in document.paragraphs if para.text.strip()]
        return "\n\n".join(lines)

