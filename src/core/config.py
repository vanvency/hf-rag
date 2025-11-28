from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    openai_api_base: Optional[str] = None
    openai_api_key: Optional[str] = None
    model_name: str = "gpt-3.5-turbo"

    vector_store_path: Path = Path("./data/db/")
    embedding_api_base: Optional[str] = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 800
    chunk_overlap: int = 200

    ocr_dpi: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)
    return settings

