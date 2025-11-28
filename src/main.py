from fastapi import FastAPI

from src.api.middleware import LoggingMiddleware
from src.api.routes import router as api_router
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor


def create_app() -> FastAPI:
    settings = get_settings()
    logger = configure_logging()
    vector_store = VectorStore(settings.vector_store_path)
    processor = DocumentProcessor(settings=settings, vector_store=vector_store, logger=logger)

    app = FastAPI(
        title="RAG System",
        version="1.0.0",
        docs_url="/",
    )
    app.include_router(api_router)
    app.add_middleware(LoggingMiddleware, logger=logger)

    app.state.settings = settings
    app.state.logger = logger
    app.state.vector_store = vector_store
    app.state.processor = processor

    return app


app = create_app()

