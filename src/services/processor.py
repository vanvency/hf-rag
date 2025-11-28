from pathlib import Path
from typing import Iterable, Optional

from src.chunking.text_splitter import MarkdownTextSplitter
from src.core.config import Settings
from src.embeddings.generator import EmbeddingGenerator, EmbeddingConfig
from src.parsers import get_parser
from src.retrieval.search import VectorStore


class DocumentProcessor:
    def __init__(
        self,
        settings: Settings,
        vector_store: VectorStore,
        logger,
    ):
        self.settings = settings
        self.vector_store = vector_store
        self.logger = logger
        self.chunker = MarkdownTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedder = EmbeddingGenerator(
            EmbeddingConfig(
                model_name=settings.embedding_model,
                api_base=settings.embedding_api_base,
                api_key=settings.openai_api_key,
            )
        )

    def process_path(self, path: Path) -> Optional[str]:
        parser, content_type = get_parser(path)
        text = parser.parse(path)
        if not text.strip():
            self.logger.warning("No text extracted from %s", path)
            return None
        chunks = self.chunker.split(text)
        if not chunks:
            self.logger.warning("Chunking produced no output for %s", path)
            return None
        vectors = self.embedder.embed(chunks)
        parsed_name = f"{path.stem}.md"
        parsed_path = Path("data/parse") / parsed_name
        parsed_path.parent.mkdir(parents=True, exist_ok=True)
        parsed_path.write_text(text, encoding="utf-8")

        metadata = self.vector_store.add_document(
            filename=path.name,
            source_path=path,
            parsed_path=parsed_path,
            chunks=chunks,
            vectors=vectors,
            content_type=content_type,
        )
        self.logger.info(
            "Processed %s into %s chunks (doc_id=%s)",
            path.name,
            len(chunks),
            metadata.document_id,
        )
        return metadata.document_id

    def process_directory(self, directory: Path) -> int:
        processed = 0
        for path in directory.glob("*"):
            if path.is_file():
                doc_id = self.process_path(path)
                if doc_id:
                    processed += 1
        return processed

    def save_upload(self, filename: str, data: bytes) -> Path:
        origin_dir = Path("data/origin")
        origin_dir.mkdir(parents=True, exist_ok=True)
        safe_name = filename.replace(" ", "_")
        target = origin_dir / safe_name
        with target.open("wb") as fh:
            fh.write(data)
        return target

