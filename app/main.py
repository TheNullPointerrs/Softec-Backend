# app/main.py
from fastapi import FastAPI, UploadFile, File, APIRouter
from typing import List
from pydantic import BaseModel

import easyocr
import io

from app.routes import sample
from app.routes import suggestions
from app.schemas import TextInput  
from app import nlp_utils  
from app.routes import suggestions      
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
import easyocr
import io

from typing import List
from fastapi import APIRouter
from app.models import SuggestionRequest, SuggestedTask
from app.services.suggestions_engine import generate_adaptive_suggestions


router = APIRouter()

app = FastAPI()

app.include_router(sample.router)
app.include_router(suggestions.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

@app.post("/parse-task")
def parse_task(input: TextInput):
    entities = nlp_utils.parse_task_entities(input.text)
    return {"entities": entities}

@app.post("/summarize-note")
def summarize_note(input: TextInput):
    summary = nlp_utils.summarize_text(input.text)
    return {"summary": summary}

@app.post("/categorize-task")
def categorize_task(input: TextInput):
    category = nlp_utils.categorize_task(input.text)
    return {"category": category}

@app.post("/ocr/")
async def ocr(file: UploadFile = File(...)):
    img_bytes = await file.read()
    reader = easyocr.Reader(['en'])  

    results = reader.readtext(img_bytes)

    extracted_text = " ".join([text for _, text, _ in results])

    return {"extracted_text": extracted_text}


@app.post("/generate-checklist")
def checklist(data: TextInput):
    checklist = nlp_utils.generate_checklist(data.text)
    return {"goal": data.text, "checklist": checklist}



@router.post("/suggestions", response_model=List[SuggestedTask])
async def get_adaptive_suggestions(request: SuggestionRequest):
    suggestions = generate_adaptive_suggestions(request.user_id)
    return suggestions

class UserMoodTask(BaseModel):
    mood: str
    tasks: list 

@app.post("/mood_task_sort/")
async def mood_task_sort(user_mood_task: UserMoodTask):
    try:
        sorted_tasks = nlp_utils.sort_tasks_based_on_mood(user_mood_task.mood, user_mood_task.tasks)
        return {"sorted_tasks": sorted_tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
