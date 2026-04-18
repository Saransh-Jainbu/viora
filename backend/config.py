"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # --- OpenAI ---
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # --- Ollama ---
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")

    # --- Default LLM ---
    default_model: str = Field(default="gpt", alias="DEFAULT_MODEL")

    # --- Firebase ---
    firebase_project_id: str = Field(default="", alias="FIREBASE_PROJECT_ID")
    firebase_private_key: str = Field(default="", alias="FIREBASE_PRIVATE_KEY")
    firebase_client_email: str = Field(default="", alias="FIREBASE_CLIENT_EMAIL")
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
