# app/main.py
from fastapi import FastAPI
from app.routes import sample
from app.schemas import TextInput  # <-- add this
from app import nlp_utils         # <-- and this

app = FastAPI()

# Include your routes
app.include_router(sample.router)

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

@app.post("/parse-task")
def parse_task(input: TextInput):
    entities = nlp_utils.parse_task_details(input.text)
    return {"entities": entities}

@app.post("/summarize-note")
def summarize_note(input: TextInput):
    summary = nlp_utils.summarize_text(input.text)
    return {"summary": summary}

@app.post("/categorize-task")
def categorize_task(input: TextInput):
    category = nlp_utils.categorize_task(input.text)
    return {"category": category}
