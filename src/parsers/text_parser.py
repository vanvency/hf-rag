from pathlib import Path

from .base import BaseParser


class TextParser(BaseParser):
    content_type = "text/markdown"
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

