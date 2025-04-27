import spacy
import requests
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import os
import dateparser

app = FastAPI()

nlp = spacy.load("en_core_web_sm")

# Hugging Face API endpoints
SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
CHECKLIST_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
SENTIMENT_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

API_TOKEN = "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"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Predefined categories
CATEGORIES = {
    "academic": ["assignment", "exam", "quiz", "study", "lecture"],
    "health": ["doctor", "gym", "exercise", "sleep", "meditate"],
    "social": ["party", "meet", "call", "hangout", "birthday"],
    "personal": ["buy", "read", "watch", "clean", "cook"],
    "finance": ["pay", "fee", "deposit", "bill", "bank"],
    "career": ["interview", "resume", "job", "career", "apply"],
    "travel": ["trip", "travel", "book", "flight", "hotel"],
    "household": ["clean", "repair", "organize", "laundry", "groceries"],
    "shopping": ["buy", "order", "purchase", "shop", "checkout"],
    "others": []
}

def parse_task_entities(text):
    doc = nlp(text)
    entities = []

    for ent in doc.ents:
        if ent.label_ == "DATE":
            parsed_date = dateparser.parse(ent.text)
            if parsed_date:
                entities.append({"text": parsed_date.strftime("%Y-%m-%d"), "label": "DATE"})
            else:
                entities.append({"text": ent.text, "label": "DATE"})

        elif ent.label_ == "TIME":
            parsed_time = dateparser.parse(ent.text)
            if parsed_time:
                entities.append({"text": parsed_time.strftime("%H:%M"), "label": "TIME"})
            else:
                entities.append({"text": ent.text, "label": "TIME"})

    # Add title entity (first 6 words or 50 chars)
    title = " ".join(text.split()[:6])
    if len(title) > 50:
        title = title[:50] + "..."
    entities.append({"text": title, "label": "TITLE"})

    return entities

def categorize_task(text):
    text_lower = text.lower()
    category = "others"
    for cat, keywords in CATEGORIES.items():
        if any(keyword in text_lower for keyword in keywords):
            category = cat
            break
    return category.capitalize()

def summarize_text(text):
    # Using Hugging Face's bart-large-cnn model for summarization instead of OpenAI
    payload = {
        "inputs": text,
        "parameters": {"max_length": 100, "min_length": 30}
    }
    
    response = requests.post(SUMMARIZATION_API_URL, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()[0]["summary_text"]
    else:
        # Fallback to simple truncation if API fails
        return text[:200] + "..." if len(text) > 200 else text

def generate_checklist(goal):
    prompt = f"Break down the goal '{goal}' into a checklist of 5 actionable steps."

    payload = {"inputs": prompt}
    response = requests.post(CHECKLIST_API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        text = response.json()[0]["generated_text"]
        checklist = text.split("\n")
        checklist = [step.strip() for step in checklist if step.strip()]
        return checklist
    else:
        return [f"Error {response.status_code}: {response.json()}"]

def sort_tasks_based_on_mood(mood: str, tasks: list) -> list:
    # Using Hugging Face for sentiment analysis and task sorting
    # First, analyze the mood using sentiment analysis
    mood_payload = {"inputs": mood}
    mood_response = requests.post(SENTIMENT_API_URL, headers=HEADERS, json=mood_payload)
    
    if mood_response.status_code != 200:
        # If sentiment analysis fails, just return the original task list
        return tasks
        
    # Prepare prompt for task sorting based on mood analysis result
    sentiment_result = mood_response.json()[0]
    sentiment = "positive" if sentiment_result["score"] > 0.5 else "negative"
    
    # Create a prompt for the T5 model to sort tasks
    sort_prompt = f"Sort these tasks for someone in a {sentiment} mood: {', '.join(tasks)}"
    
    sort_payload = {"inputs": sort_prompt}
    sort_response = requests.post(CHECKLIST_API_URL, headers=HEADERS, json=sort_payload)
    
    if sort_response.status_code == 200:
        sorted_text = sort_response.json()[0]["generated_text"]
        # Parse the response into a list of tasks
        sorted_tasks = [task.strip() for task in sorted_text.split(",") if task.strip()]
        
        # If parsing failed or returned insufficient results, return original tasks
        if len(sorted_tasks) < len(tasks) // 2:
            return tasks
            
        return sorted_tasks
    else:
        # If API call fails, return original tasks
        return tasks