# app/main.py
from fastapi import FastAPI
from app.routes import sample

app = FastAPI()

# Include your routes
app.include_router(sample.router)

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}