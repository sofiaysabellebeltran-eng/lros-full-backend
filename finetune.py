# finetune.py - Collect high-quality training data

import json
import os
from datetime import datetime

FINETUNE_FILE = "finetune_data.jsonl"

def save_training_pair(user_input, ai_response, rating, pattern_used):
    """Save high-quality Q&A pairs for fine-tuning (only good responses)"""
    if rating < 1:  # Only save good responses
        return False
    
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": user_input,
        "output": ai_response,
        "pattern": pattern_used,
        "rating": rating
    }
    
    with open(FINETUNE_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')
    
    return True

def get_training_data(min_rating=4, limit=100):
    """Get collected training data"""
    if not os.path.exists(FINETUNE_FILE):
        return []
    
    data = []
    with open(FINETUNE_FILE, 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get('rating', 0) >= min_rating:
                data.append(entry)
                if len(data) >= limit:
                    break
    return data

def get_training_stats():
    """Get stats about collected training data"""
    if not os.path.exists(FINETUNE_FILE):
        return {"total": 0, "by_pattern": {}}
    
    total = 0
    by_pattern = {}
    with open(FINETUNE_FILE, 'r') as f:
        for line in f:
            entry = json.loads(line)
            total += 1
            pattern = entry.get('pattern', 'unknown')
            by_pattern[pattern] = by_pattern.get(pattern, 0) + 1
    
    return {"total": total, "by_pattern": by_pattern}
