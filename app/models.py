from pydantic import BaseModel
from typing import List

class SuggestionRequest(BaseModel):
    user_id: str

class SuggestedTask(BaseModel):
    title: str
    suggested_time: str
    category: str
    confidence_score: float
