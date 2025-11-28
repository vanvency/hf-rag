from pathlib import Path
from typing import List, Optional, Tuple

from .base import BaseParser
from .doc_parser import DocParser
from .image_parser import ImageParser
from .pdf_parser import PDFParser
from .text_parser import TextParser

PARSERS: List[BaseParser] = [
    TextParser(),
    PDFParser(),
    DocParser(),
    ImageParser(),
]


def get_parser(path: Path) -> Tuple[BaseParser, str]:
    for parser in PARSERS:
        if parser.supports(path):
            return parser, parser.content_type
    return TextParser(), TextParser.content_type

