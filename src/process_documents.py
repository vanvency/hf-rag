from pathlib import Path

import typer
from rich.console import Console

from src.core.config import get_settings
from src.core.logging import configure_logging
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor

app = typer.Typer(help="Document processing pipeline")
console = Console()


@app.command()
def run(directory: str = "data/origin"):
    """Process files from the origin directory and update the vector store."""
    settings = get_settings()
    logger = configure_logging()
    vector_store = VectorStore(settings.vector_store_path)
    processor = DocumentProcessor(settings=settings, vector_store=vector_store, logger=logger)

    processed = processor.process_directory(Path(directory))
    docs, chunks = vector_store.stats()
    console.print(
        f"[green]Processed {processed} new files. Store now tracks {docs} documents / {chunks} chunks.[/green]"
    )


if __name__ == "__main__":
    app()

