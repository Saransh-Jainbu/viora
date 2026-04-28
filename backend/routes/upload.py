"""
Upload route — POST /upload

Accepts PDF, TXT, or DOCX files, extracts text, chunks it,
generates embeddings, and stores everything in ChromaDB.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from auth import get_current_user, get_user_ref
from models.schemas import UploadResponse
from services.chunking import extract_text_with_metadata, split_into_chunks_with_metadata, SUPPORTED_EXTENSIONS
from services.embedding import get_embeddings
from services.retrieval import add_document

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Upload a document for RAG indexing.

    1. Validate file type
    2. Extract text
    3. Split into chunks
    4. Generate embeddings
    5. Store in ChromaDB
    6. Log upload in Firebase Realtime DB
    """
    # ── 1. Validate extension ────────────────────────────────────────────
    filename = file.filename or "unknown"
    ext = filename[filename.rfind("."):].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # ── 2. Deduplication check (via hash) ─────────────────────────────────
    file_bytes = await file.read()
    import hashlib
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    
    uid = user["uid"]
    user_ref = get_user_ref(uid)
    existing_docs = user_ref.child("documents").get()
    
    if existing_docs and isinstance(existing_docs, dict):
        for doc_id, data in existing_docs.items():
            if data.get("content_hash") == content_hash:
                return UploadResponse(
                    doc_id=doc_id,
                    filename=data.get("filename", filename),
                    num_chunks=data.get("num_chunks", 0),
                    message="Document already exists. Using previous indexing."
                )

    # ── 3. Read & extract text with metadata ────────────────────────────
    try:
        docs = extract_text_with_metadata(file_bytes, filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text: {str(exc)}",
        )

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded document contains no extractable text.",
        )

    # ── 3. Chunk with metadata ──────────────────────────────────────────
    chunks_with_meta = split_into_chunks_with_metadata(docs)
    chunk_texts = [c["text"] for c in chunks_with_meta]
    if not chunk_texts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded document produced no indexable chunks.",
        )

    # ── 4. Embed ────────────────────────────────────────────────────────
    try:
        embeddings = get_embeddings(chunk_texts)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create embeddings: {str(exc)}",
        )

    # ── 5. Store in ChromaDB ────────────────────────────────────────────
    doc_id = str(uuid.uuid4())
    uid = user["uid"]
    
    # Pack metadata properly
    try:
        num_stored = add_document(
            doc_id=doc_id,
            chunks=chunk_texts,
            embeddings=embeddings,
            metadata={
                "filename": filename,
                "uid": uid,
                # Pass custom chunk-level metadata
                "chunk_metadata": [c["metadata"] for c in chunks_with_meta],
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store document in vector database: {str(exc)}",
        )

    # ── 6. Log to Firebase Realtime DB ───────────────────────────────────
    try:
        user_ref.child("documents").child(doc_id).set(
            {
                "filename": filename,
                "num_chunks": num_stored,
                "doc_id": doc_id,
                "content_hash": content_hash,
            }
        )
    except Exception:
        pass  # non-critical — don't fail the upload if logging fails

    return UploadResponse(
        doc_id=doc_id,
        filename=filename,
        num_chunks=num_stored,
    )
