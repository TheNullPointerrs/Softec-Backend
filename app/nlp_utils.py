import spacy
import requests
import dateparser
from datetime import datetime

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
