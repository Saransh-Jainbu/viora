"""
ChromaDB retrieval service.

Manages a persistent ChromaDB collection for document chunks.
Provides add / query operations used by the upload and chat routes.
"""

import chromadb
import os
import tempfile
from config import settings

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "documents"


def init_chroma():
    """
    Initialise the persistent ChromaDB client and get-or-create the collection.
    Called once at application startup.
    """
    global _client, _collection
    primary_path = settings.chroma_persist_dir
    try:
        os.makedirs(primary_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=primary_path)
        print(f"[chroma] Using persistence path: {primary_path}")
    except Exception as exc:
        fallback_path = os.path.join(tempfile.gettempdir(), "viora_chroma_db")
        os.makedirs(fallback_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=fallback_path)
        print(f"[chroma] Failed to use '{primary_path}' ({exc}). Falling back to: {fallback_path}")

    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _sanitize_metadata_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if value is None:
        return ""
    return str(value)


def _sanitize_metadata(metadata: dict) -> dict:
    return {str(k): _sanitize_metadata_value(v) for k, v in metadata.items()}


def get_collection() -> chromadb.Collection:
    """Return the active ChromaDB collection, initialising if needed.

    If the collection was deleted while the server was running (stale reference),
    re-initialises ChromaDB automatically instead of crashing.
    """
    global _collection
    if _collection is None:
        init_chroma()
        return _collection
    
    try:
        _collection.count()  # lightweight check to confirm collection still exists
    except Exception:
        init_chroma()
    return _collection


def add_document(
    doc_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadata: dict | None = None,
) -> int:
    """
    Upsert document chunks into ChromaDB.

    Each chunk gets a unique ID like ``{doc_id}_chunk_0``.
    Returns the number of chunks stored.
    """
    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts do not match")
    if not chunks:
        raise ValueError("No chunks to store")

    collection = get_collection()
    
    chunk_meta_list = (metadata or {}).pop("chunk_metadata", None)
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = []

    for i in range(len(chunks)):
        # Merge global metadata (uid, filename) with chunk-specific metadata (page, heading)
        m = {
            "doc_id": doc_id,
            "chunk_index": i,
            **(metadata or {}),
        }
        if chunk_meta_list and i < len(chunk_meta_list):
            m.update(chunk_meta_list[i])
        metadatas.append(_sanitize_metadata(m))

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(chunks)


def query(
    query_embedding: list[float], 
    top_k: int = 5,
    uid: str | None = None,
    doc_id: str | None = None
) -> list[dict]:
    """
    Query ChromaDB for the most relevant chunks, optionally filtered by uid/doc_id.

    Returns a list of dicts with keys: text, doc_id, chunk_index, distance.
    """
    collection = get_collection()

    # Build filter
    where_filter = {}
    if uid and doc_id:
        where_filter = {"$and": [{"uid": uid}, {"doc_id": doc_id}]}
    elif uid:
        where_filter = {"uid": uid}
    elif doc_id:
        where_filter = {"doc_id": doc_id}

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        print(f"[chroma] query failed: {exc}")
        return []

    items: list[dict] = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc_text in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else None
            items.append(
                {
                    "text": doc_text,
                    "doc_id": meta.get("doc_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "page": meta.get("page", 1),
                    "distance": distance,
                }
            )
    return items
