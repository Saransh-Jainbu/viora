"""
LLM dispatch service.

Supports two backends:
  • **gpt**   — OpenAI ChatCompletion (gpt-4)
  • **llama** — Hugging Face Serverless API (Llama 3)
"""

import httpx
from openai import OpenAI
from config import settings

_openai_client: OpenAI | None = None

SYSTEM_PROMPT = (
    "You are an expert document intelligence assistant. Your goal is to provide "
    "COMPREHENSIVE and DETAILED answers based on the provided context. "
    "NEVER USE BOLD TEXT. NEVER use double asterisks (**) for emphasis or titles. "
    "Use clear, professional language. If a question is complex, break down your "
    "explanation into logical sections or bullet points for better readability. "
    "Always reference the relevant parts of the context. If the context does not "
    "contain the answer, state that you cannot find it in the current document. "
    "Do not hallucinate or use external knowledge."
)


def _get_openai_client() -> OpenAI:
    """Lazily initialise the OpenAI client."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _build_messages(query: str, context_chunks: list[str]) -> list[dict]:
    """Build the chat messages list with system prompt, context, and user query."""
    context_block = "\n\n---\n\n".join(context_chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Context:\n{context_block}\n\n"
                f"Question: {query}\n\n"
                "Please answer based on the context above."
            ),
        },
    ]


async def generate_response(
    query: str,
    context_chunks: list[str],
    model_name: str = "gpt",
) -> str:
    """
    Generate an LLM response for the given query using retrieved context.

    Parameters
    ----------
    query : str
        The user's question.
    context_chunks : list[str]
        Relevant text chunks retrieved from ChromaDB.
    model_name : str
        Either ``"gpt"`` or ``"llama"``.

    Returns
    -------
    str
        The model's answer.
    """
    messages = _build_messages(query, context_chunks)

    if model_name == "gpt":
        return _call_openai(messages)
    elif model_name == "llama":
        return await _call_huggingface(messages)
    else:
        raise ValueError(f"Unknown model: '{model_name}'. Use 'gpt' or 'llama'.")


# ── OpenAI GPT ────────────────────────────────────────────────────────────────

def _call_openai(messages: list[dict]) -> str:
    """Call OpenAI ChatCompletion API synchronously."""
    client = _get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )
    content = response.choices[0].message.content.strip()
    # Forcefully remove markdown bolding as a safety measure
    return content.replace("**", "")


# ── Hugging Face (Llama) ────────────────────────────────────────────────────────────

async def _call_huggingface(messages: list[dict]) -> str:
    """Call Hugging Face Serverless Inference API asynchronously."""
    url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
        "Content-Type": "application/json",
    }
    
    # Convert messages to a single prompt string
    prompt = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt += f"{role.upper()}: {content}\n"
    prompt += "ASSISTANT:"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.3,
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # HF API returns list of dicts with "generated_text" key
        if isinstance(data, list) and len(data) > 0:
            content = data[0].get("generated_text", "").strip()
        else:
            content = data.get("generated_text", "").strip()
        
        # Forcefully remove markdown bolding as a safety measure
        return content.replace("**", "")
