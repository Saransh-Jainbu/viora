"""
Pydantic request / response schemas for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User's question")
    session_id: Optional[str] = Field(default=None, description="Chat session ID")
    doc_id: Optional[str] = Field(default=None, description="Optional document ID for context filtering")


class SourceChunk(BaseModel):
    text: str
    doc_id: str
    chunk_index: int
    page: int = 1


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = []
    session_id: str
    model_used: str


# ── Chat History ──────────────────────────────────────────────────────────────

class ChatHistoryItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    sources: list[SourceChunk] = []


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatHistoryItem] = []


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    num_chunks: int
    message: str = "Document processed and stored successfully."


# ── Model Selection ──────────────────────────────────────────────────────────

class ModelSelection(BaseModel):
    model: str = Field(
        ...,
        pattern=r"^(gpt|llama)$",
        description="Select 'gpt' or 'llama'",
    )


class CurrentModelResponse(BaseModel):
    model: str
