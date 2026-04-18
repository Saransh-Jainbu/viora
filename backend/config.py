"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # --- OpenAI ---
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # --- Ollama ---
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    # --- Default LLM ---
    default_model: str = Field(default="gpt", alias="DEFAULT_MODEL")

    # --- Firebase ---
    firebase_service_account_key: str = Field(
        default="./firebase-service-account.json",
        alias="FIREBASE_SERVICE_ACCOUNT_KEY",
    )
    firebase_database_url: str = Field(default="", alias="FIREBASE_DATABASE_URL")

    # --- Embedding ---
    embedding_model_name: str = Field(default="text-embedding-3-large", alias="EMBEDDING_MODEL_NAME")

    # --- ChromaDB ---
    chroma_persist_dir: str = Field(default="./storage/chroma_db", alias="CHROMA_PERSIST_DIR")

    # --- Chunking ---
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = Settings()
