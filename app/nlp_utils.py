import spacy
import requests
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
import dateparser


# OpenAI API key (store it securely, like in environment variables)
openaiKey = "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"

app = FastAPI()



nlp = spacy.load("en_core_web_sm")

# Summarization model (Bart)
SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
# Checklist generator model (Flan-T5-small)
CHECKLIST_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"

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
    payload = {"inputs": text}
    response = requests.post(SUMMARIZATION_API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        summary = response.json()[0]["summary_text"]
        return summary
    else:
        return f"Error {response.status_code}: {response.json()}"

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






# Function to interact with OpenAI API for mood-based task sorting
def sort_tasks_based_on_mood(mood: str, tasks: list) -> list:
    # Prepare prompt for OpenAI API to prioritize tasks based on the mood
    prompt = f"User's current mood: {mood}\n\nTasks:\n" + "\n".join(tasks) + "\n\nPrioritize the tasks based on the mood and sort them in the most appropriate order."
    client = OpenAI(
    # This is the default and can be omitted
    api_key=openaiKey,
)
    # Call OpenAI API to process the tasks and mood
    response = client.responses.create(
        model="text-davinci-003",  # Choose the engine (e.g., text-davinci-003 for GPT-3)
        instruction="Sort the tasks based on the user's mood.",
        input=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7
    )

    sorted_tasks = response.choices[0].text.strip().split('\n')
    return sorted_tasks
