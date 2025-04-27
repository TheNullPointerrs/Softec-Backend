import spacy
import requests
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import os
import dateparser
import re

app = FastAPI()

nlp = spacy.load("en_core_web_sm")

SUMMARIZATION_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
CHECKLIST_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
SENTIMENT_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

API_TOKEN = "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"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

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
    payload = {
        "inputs": text,
        "parameters": {"max_length": 100, "min_length": 30}
    }
    
    response = requests.post(SUMMARIZATION_API_URL, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        summary = response.json()[0]["summary_text"]
        
        sentences = [sentence.strip() for sentence in summary.split('.') if sentence.strip()]
        
        bullet_points = "\n".join([f"- {sentence}." for sentence in sentences])
        
        return bullet_points
    else:
        fallback = text[:200] + "..." if len(text) > 200 else text
        fallback_sentences = [sentence.strip() for sentence in fallback.split('.') if sentence.strip()]
        bullet_points = "\n".join([f"- {sentence}." for sentence in fallback_sentences])
        return bullet_points


def generate_checklist(goal):
    # Create a more specific prompt to get better results
    prompt = f"""Generate a numbered list of 5 specific, actionable steps to achieve the goal: '{goal}'
    Format each step as a clear instruction that begins with a verb.
    Example format:
    1. [Action verb] [specific task]
    2. [Action verb] [specific task]
    """

    payload = {"inputs": prompt}
    
    try:
        response = requests.post(CHECKLIST_API_URL, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            raw_text = response.json()[0]["generated_text"]
            
            # Process the response to extract actual steps
            steps = []
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            
            for line in lines:
                # Remove number prefixes and common list markers
                cleaned_line = re.sub(r"^\d+[\.\)]\s*|\-\s*|\*\s*", "", line).strip()
                
                # Only add if it's a substantial step (not just a heading or empty line)
                if cleaned_line and len(cleaned_line) > 3:
                    # Capitalize first letter for consistency
                    if not cleaned_line[0].isupper() and cleaned_line[0].isalpha():
                        cleaned_line = cleaned_line[0].upper() + cleaned_line[1:]
                    steps.append(cleaned_line)
            
            # If we got enough steps, return them (limit to 5)
            if len(steps) >= 3:
                return steps[:5]
            
            # If we didn't get enough steps, try a backup approach
            backup_prompt = f"List 5 concrete tasks to complete to {goal}:"
            backup_payload = {"inputs": backup_prompt}
            
            backup_response = requests.post(CHECKLIST_API_URL, headers=HEADERS, json=backup_payload, timeout=10)
            
            if backup_response.status_code == 200:
                backup_text = backup_response.json()[0]["generated_text"]
                backup_steps = []
                
                for line in backup_text.split("\n"):
                    cleaned_line = re.sub(r"^\d+[\.\)]\s*|\-\s*|\*\s*", "", line).strip()
                    if cleaned_line and len(cleaned_line) > 3:
                        if not cleaned_line[0].isupper() and cleaned_line[0].isalpha():
                            cleaned_line = cleaned_line[0].upper() + cleaned_line[1:]
                        backup_steps.append(cleaned_line)
                
                if len(backup_steps) >= 3:
                    return backup_steps[:5]
        
        # If we reach here, both attempts failed or didn't provide enough steps
        # Generate generic steps based on the goal itself
        return generate_generic_steps(goal)
    
    except Exception as e:
        print(f"Error generating checklist: {str(e)}")
        return generate_generic_steps(goal)

def generate_generic_steps(goal):
    """Generate generic but still somewhat relevant steps based on goal keywords"""
    goal_words = goal.lower().split()
    
    # Extract key verbs and nouns
    key_term = goal_words[-1] if goal_words else "goal"
    
    # Common action verbs that work for most goals
    action_verbs = ["Research", "Plan", "Practice", "Evaluate", "Improve"]
    
    steps = [
        f"{action_verbs[0]} the fundamentals of {key_term}",
        f"{action_verbs[1]} a structured approach to {goal}",
        f"{action_verbs[2]} with basic {key_term} exercises daily",
        f"{action_verbs[3]} your progress with {key_term}",
        f"{action_verbs[4]} your skills by joining a {key_term} community"
    ]
    
    return steps

def sort_tasks_based_on_mood(mood: str, tasks: list) -> list:

    mood_payload = {"inputs": mood}
    mood_response = requests.post(SENTIMENT_API_URL, headers=HEADERS, json=mood_payload)
    
    if mood_response.status_code != 200:
        return tasks
        
    sentiment_result = mood_response.json()[0]
    sentiment = "positive" if sentiment_result["score"] > 0.5 else "negative"
    
    sort_prompt = f"Sort these tasks for someone in a {sentiment} mood: {', '.join(tasks)}"
    
    sort_payload = {"inputs": sort_prompt}
    sort_response = requests.post(CHECKLIST_API_URL, headers=HEADERS, json=sort_payload)
    
    if sort_response.status_code == 200:
        sorted_text = sort_response.json()[0]["generated_text"]
        sorted_tasks = [task.strip() for task in sorted_text.split(",") if task.strip()]
        
        if len(sorted_tasks) < len(tasks) // 2:
            return tasks
            
        return sorted_tasks
    else:
        return tasks