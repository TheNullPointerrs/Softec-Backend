from typing import List
from fastapi import APIRouter
from app.models import SuggestionRequest, SuggestedTask
from app.services.suggestions_engine import generate_adaptive_suggestions

router = APIRouter()

@router.post("/suggestions", response_model=List[SuggestedTask])
async def get_adaptive_suggestions(request: SuggestionRequest):
    suggestions = generate_adaptive_suggestions(request.user_id)
    return suggestions
