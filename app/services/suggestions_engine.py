from app.database import db
from datetime import datetime, timedelta
import random

def analyze_user_tasks(user_id: str):
    user_ref = db.collection("users").document(user_id)
    tasks = user_ref.collection("tasks").stream()

    times = []
    categories = []

    for task in tasks:
        data = task.to_dict()
        if data.get('startTime'):
            start_time = datetime.fromisoformat(data['startTime'])
            times.append(start_time.hour)
        if data.get('category'):
            categories.append(data['category'])

    return times, categories

def generate_adaptive_suggestions(user_id: str):
    times, categories = analyze_user_tasks(user_id)

    if not times or not categories:
        return []  # No data

    # Find most frequent category and preferred time
    preferred_hour = max(set(times), key=times.count)
    preferred_category = max(set(categories), key=categories.count)

    suggestions = []

    # Create 3 suggestions
    for _ in range(3):
        suggested_time = datetime.utcnow().replace(hour=preferred_hour, minute=0, second=0) + timedelta(days=random.randint(1, 5))
        suggestions.append({
            "title": f"Suggested {preferred_category} task",
            "suggested_time": suggested_time.isoformat(),
            "category": preferred_category,
            "confidence_score": round(random.uniform(0.75, 0.95), 2)
        })

    return suggestions