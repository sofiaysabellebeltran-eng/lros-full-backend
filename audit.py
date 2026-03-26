# audit.py - Simple file-based logging

import csv
from datetime import datetime
import os

AUDIT_FILE = "audit_log.csv"

def ensure_file():
    if not os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Session ID', 'User Input', 'Pattern', 'Model', 'Response', 'Rating', 'Feedback'])

def log_interaction(session_id, user_input, pattern, model, response, rating=None, feedback_text=None):
    try:
        ensure_file()
        timestamp = datetime.utcnow().isoformat()
        with open(AUDIT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, session_id, user_input, pattern, model, response, rating or "", feedback_text or ""])
        
        with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
            row_count = sum(1 for _ in f) - 1
        return row_count
    except Exception as e:
        print(f"Log error: {e}")
        return None

def update_feedback(row_index, rating, feedback_text=""):
    print(f"Feedback received: Row {row_index}, Rating {rating}")
    return True