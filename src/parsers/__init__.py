from pathlib import Path
from typing import List, Optional, Tuple
import logging

from .base import BaseParser
from .doc_parser import DocParser
from .pdf_parser import PDFParser
from .text_parser import TextParser

logger = logging.getLogger(__name__)

# Try to import ImageParser, but make it optional
ImageParser = None
try:
    from .image_parser import ImageParser
except Exception as e:
    logger.warning(f"ImageParser (MinerU OCR) not available: {e}. Image files will not be supported.")

PARSERS: List[BaseParser] = [
    TextParser(),
    PDFParser(),
    DocParser(),
]

# Only add ImageParser if it was successfully imported
if ImageParser is not None:
    PARSERS.append(ImageParser())


def get_parser(path: Path) -> Tuple[BaseParser, str]:
    for parser in PARSERS:
        if parser.supports(path):
            return parser, parser.content_type
    return TextParser(), TextParser.content_type

