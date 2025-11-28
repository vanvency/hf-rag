from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    content_type: str = "text/plain"

    @abstractmethod
    def supports(self, path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, path: Path) -> str:
        raise NotImplementedError

