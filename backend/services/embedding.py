"""
Embedding service using sentence-transformers.

Loads the model lazily as a singleton to avoid re-downloading on every request.
"""

from openai import OpenAI
from config import settings

_model: OpenAI | None = None


def _get_model() -> OpenAI:
    """Lazily load and cache the OpenAI client."""
    global _model
    if _model is None:
        _model = OpenAI(api_key=settings.openai_api_key)
    return _model


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings.

    Returns a list of embedding vectors (each a list of floats).
    """
    client = _get_model()
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    return [item.embedding for item in response.data]


def get_single_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text string."""
    return get_embeddings([text])[0]


def warmup():
    """Warmup OpenAI client (optional lightweight call)."""
    _get_model()
