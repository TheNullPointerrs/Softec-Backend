# app/main.py
from app.routes import sample
from app.schemas import TextInput  # <-- add this
from app import nlp_utils         # <-- and this

from fastapi import FastAPI, UploadFile, File
import easyocr
import io


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

@app.post("/ocr/")
async def ocr(file: UploadFile = File(...)):
    # Read the uploaded file as bytes
    img_bytes = await file.read()

    # OCR the image bytes directly
    results = reader.readtext(img_bytes)

    # Extract the detected text
    extracted_text = " ".join([text for _, text, _ in results])

    return {"extracted_text": extracted_text}


@router.post("/generate-checklist")
def checklist(data: TextInput):
    checklist = task_utils.generate_checklist(data.text)
    return {"goal": data.text, "checklist": checklist}
