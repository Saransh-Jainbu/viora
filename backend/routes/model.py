"""
Model switching routes — POST /set-model  &  GET /current-model

Allows the user to switch between GPT and Llama backends.
"""

from fastapi import APIRouter, Depends
from auth import get_current_user
from models.schemas import ModelSelection, CurrentModelResponse
from routes.chat import get_selected_model, set_selected_model

router = APIRouter()


@router.post("/set-model", response_model=CurrentModelResponse)
async def set_model(
    body: ModelSelection,
    user: dict = Depends(get_current_user),
):
    """Set the active LLM model for the current user."""
    uid = user["uid"]
    set_selected_model(uid, body.model)
    return CurrentModelResponse(model=body.model)


@router.get("/current-model", response_model=CurrentModelResponse)
async def current_model(
    user: dict = Depends(get_current_user),
):
    """Return the currently selected LLM model for the user."""
    uid = user["uid"]
    model = get_selected_model(uid)
    return CurrentModelResponse(model=model)
