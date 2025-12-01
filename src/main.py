from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.api.middleware import LoggingMiddleware
from src.api.routes import router as api_router
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor
from src.services.llm_service import LLMService


def create_app() -> FastAPI:
    settings = get_settings()
    logger = configure_logging()
    vector_store = VectorStore(settings.vector_store_path)
    
    # Initialize processor and LLM service with error handling
    # Allow app to start even if APIs aren't configured (will fail on actual use)
    processor = None
    llm_service = None
    
    try:
        processor = DocumentProcessor(settings=settings, vector_store=vector_store, logger=logger)
    except ValueError as e:
        logger.warning(f"DocumentProcessor initialization failed (API may not be configured): {e}")
        logger.warning("App will start but document processing will fail until APIs are configured")
    
    try:
        llm_service = LLMService(settings=settings)
    except Exception as e:
        logger.warning(f"LLMService initialization failed: {e}")
        logger.warning("App will start but LLM features will fail until APIs are configured")

    app = FastAPI(
        title="RAG System",
        version="1.0.0",
        docs_url="/docs",
    )
    
    # Add CORS middleware to allow frontend to communicate with API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router)
    # Add logging middleware (must be added after CORS)
    app.add_middleware(LoggingMiddleware, logger=logger)
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    web_dir = project_root / "src" / "web"
    
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        try:
            app_logger = request.app.state.logger
            index_path = web_dir / "index.html"
            if not index_path.exists():
                app_logger.error(f"UI file not found at {index_path}")
                return HTMLResponse(
                    content=f"<h1>Error</h1><p>UI file not found at {index_path}</p>",
                    status_code=404
                )
            # Read and return HTML content
            content = index_path.read_text(encoding="utf-8")
            return HTMLResponse(content=content)
        except Exception as e:
            # Fallback to module logger if app state logger not available
            import logging
            error_logger = logging.getLogger(__name__)
            error_logger.error(f"Error serving index page: {e}", exc_info=True)
            return HTMLResponse(
                content=f"<h1>Internal Server Error</h1><p>{str(e)}</p>",
                status_code=500
            )
    
    # Serve static files from web directory
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
    else:
        logger.warning(f"Web directory not found at {web_dir}")

    app.state.settings = settings
    app.state.logger = logger
    app.state.vector_store = vector_store
    app.state.processor = processor
    app.state.llm_service = llm_service
    
    # Add startup event to verify logging
    @app.on_event("startup")
    async def startup_event():
        logger.info("=" * 60)
        logger.info("RAG System 服务器已启动")
        logger.info("所有API请求将记录到控制台")
        logger.info("=" * 60)

    return app


app = create_app()

