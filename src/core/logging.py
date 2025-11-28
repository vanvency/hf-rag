import logging
from logging import Logger

from rich.console import Console
from rich.logging import RichHandler


def configure_logging() -> Logger:
    console = Console()
    handler = RichHandler(console=console, show_time=False)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[handler],
    )
    return logging.getLogger("rag-system")

