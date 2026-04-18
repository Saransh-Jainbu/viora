"""
Viora RAG Backend — FastAPI entry point.

Initialises ChromaDB, warms up the embedding model,
registers CORS middleware and all route modules.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.retrieval import init_chroma
from services.embedding import warmup as warmup_embeddings
from routes import upload, chat, model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    # ── Startup ──────────────────────────────────────────────────────────
    print("[startup] Initialising ChromaDB...")
    init_chroma()

    print("[startup] Loading embedding model...")
    warmup_embeddings()

    print("[startup] Backend ready.")
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────
    print("[shutdown] Shutting down.")


app = FastAPI(
    title="Viora — Chat with Documents",
    description="RAG-powered document Q&A API with Firebase authentication.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow the Next.js frontend) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────────────────
app.include_router(upload.router, tags=["Upload"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(model.router, tags=["Model"])


@app.get("/", tags=["Health"])
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "viora-rag-backend"}
