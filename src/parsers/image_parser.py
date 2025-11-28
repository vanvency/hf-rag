from pathlib import Path

from PIL import Image
import pytesseract

from .base import BaseParser


class ImageParser(BaseParser):
    content_type = "image/ocr"
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, path: Path) -> str:
        image = Image.open(path)
        return pytesseract.image_to_string(image)

