"""
Chat routes — POST /chat  &  GET /chat-history

Handles query → embed → retrieve → LLM → respond flow,
and persists chat history to Firebase Realtime DB.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from auth import get_current_user, get_user_ref
from models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryItem,
    ChatHistoryResponse,
    SourceChunk,
)
from services.embedding import get_single_embedding
from services.retrieval import query as retrieval_query
from services.llm import generate_response

router = APIRouter()


# ── In-memory model selection per user (uid → model name) ────────────────────
_user_model_selection: dict[str, str] = {}


def get_selected_model(uid: str) -> str:
    """Return the currently selected model for a user, default 'gpt'."""
    from config import settings

    return _user_model_selection.get(uid, settings.default_model)


def set_selected_model(uid: str, model: str):
    """Set the selected model for a user."""
    _user_model_selection[uid] = model


# ── POST /chat ────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """
    RAG chat endpoint.

    1. Embed the user query
    2. Retrieve top-5 relevant chunks from ChromaDB
    3. Call the selected LLM with context + query
    4. Persist conversation to Firebase Realtime DB
    5. Return answer + sources
    """
    uid = user["uid"]
    session_id = body.session_id or str(uuid.uuid4())
    model_name = get_selected_model(uid)
    now = datetime.now(timezone.utc).isoformat()

    # ── 1. Embed query ───────────────────────────────────────────────────
    try:
        query_embedding = get_single_embedding(body.query)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create query embedding: {str(exc)}",
        )

    # ── 2. Retrieve relevant chunks (filtered by uid & doc_id) ────────────
    results = retrieval_query(
        query_embedding, 
        top_k=5, 
        uid=uid, 
        doc_id=body.doc_id
    )

    # If document-scoped retrieval returns nothing, retry with user-wide retrieval.
    if body.doc_id and not results:
        results = retrieval_query(
            query_embedding,
            top_k=5,
            uid=uid,
            doc_id=None,
        )

    if results:
        context_chunks = [r["text"] for r in results]
        sources = [
            SourceChunk(
                text=r["text"][:200],  # truncate for response
                doc_id=r["doc_id"],
                chunk_index=r["chunk_index"],
                page=r.get("page", 1),
            )
            for r in results
        ]
    else:
        context_chunks = []
        sources = []

    # ── 3. Generate LLM response ────────────────────────────────────────
    if not context_chunks:
        answer = (
            "I could not find relevant indexed context for this question yet. "
            "Please upload a supported file (PDF, DOCX, TXT), wait for indexing to complete, "
            "and try again."
        )
    else:
        try:
            answer = await generate_response(body.query, context_chunks, model_name)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM call failed: {str(exc)}",
            )

    # ── 4. Persist to Firebase Realtime DB ───────────────────────────────
    try:
        user_ref = get_user_ref(uid)
        history_ref = user_ref.child("chat_history").child(session_id)

        # Save user message
        history_ref.push(
            {
                "role": "user",
                "content": body.query,
                "timestamp": now,
            }
        )

        # Save assistant response
        history_ref.push(
            {
                "role": "assistant",
                "content": answer,
                "timestamp": now,
                "sources": [s.model_dump() for s in sources],
            }
        )
    except Exception:
        pass  # non-critical

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=session_id,
        model_used=model_name,
    )


# ── GET /chat-history ────────────────────────────────────────────────────────

@router.get("/chat-history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str = Query(..., description="Chat session ID"),
    user: dict = Depends(get_current_user),
):
    """Retrieve chat history for a session from Firebase Realtime DB."""
    uid = user["uid"]

    try:
        user_ref = get_user_ref(uid)
        history_data = user_ref.child("chat_history").child(session_id).get()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(exc)}",
        )

    messages: list[ChatHistoryItem] = []
    if history_data and isinstance(history_data, dict):
        for _key, msg in sorted(history_data.items()):
            sources_raw = msg.get("sources", [])
            sources = [
                SourceChunk(**s) for s in sources_raw
            ] if sources_raw else []

            messages.append(
                ChatHistoryItem(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    timestamp=msg.get("timestamp", ""),
                    sources=sources,
                )
            )

    return ChatHistoryResponse(session_id=session_id, messages=messages)
