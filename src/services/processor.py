from pathlib import Path
from typing import Iterable, Optional, Tuple, List

from src.chunking.catalog_splitter import CatalogBasedSplitter
from src.chunking.catalog_extractor import CatalogItem
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
        self.chunker = CatalogBasedSplitter(
            min_chunk_size=settings.chunk_size // 2,
            max_chunk_size=settings.chunk_size * 2,
        )
        self.embedder = EmbeddingGenerator(
            EmbeddingConfig(
                model_name=settings.embedding_model,
                api_base=settings.embedding_api_base,
                api_key=settings.embedding_api_key or settings.openai_api_key,
            )
        )

    def process_path(self, path: Path) -> Optional[str]:
        parser, content_type = get_parser(path)
        text = parser.parse(path)
        if not text.strip():
            self.logger.warning("No text extracted from %s", path)
            return None
        
        # Use catalog-based splitting
        catalog_items, chunks, chunk_metadata_list = self.chunker.split(text)
        if not chunks:
            self.logger.warning("Chunking produced no output for %s", path)
            return None
        
        self.logger.info("Extracted %d catalog items, created %d chunks", len(catalog_items), len(chunks))
        
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
            catalog_items=catalog_items,
            chunk_metadata_list=chunk_metadata_list,
        )
        self.logger.info(
            "Processed %s into %s chunks with %s catalog items (doc_id=%s)",
            path.name,
            len(chunks),
            len(catalog_items),
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
        upload_dir = Path("data/upload")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = filename.replace(" ", "_")
        target = upload_dir / safe_name
        with target.open("wb") as fh:
            fh.write(data)
        return target

