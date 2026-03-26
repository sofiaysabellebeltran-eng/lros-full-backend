# finetune.py - Collect high-quality training data for fine-tuning

import json
import os
from datetime import datetime

FINETUNE_FILE = "finetune_data.jsonl"

def save_training_pair(user_input, ai_response, rating, pattern_used, user_id="anonymous"):
    """Save high-quality Q&A pairs for fine-tuning (only good responses)"""
    if rating < 1:  # Only save good responses (1 = good, -1 = bad)
        return False
    
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": user_input,
        "output": ai_response,
        "pattern": pattern_used,
        "rating": rating,
        "user_id": user_id
    }
    
    try:
        with open(FINETUNE_FILE, 'a') as f:
            f.write(json.dumps(data) + '\n')
        return True
    except Exception as e:
        print(f"Error saving training pair: {e}")
        return False

def get_training_data(min_rating=1, limit=100):
    """Get collected training data"""
    if not os.path.exists(FINETUNE_FILE):
        return []
    
    data = []
    try:
        with open(FINETUNE_FILE, 'r') as f:
            for line in f:
                entry = json.loads(line)
                if entry.get('rating', 0) >= min_rating:
                    data.append(entry)
                    if len(data) >= limit:
                        break
    except Exception as e:
        print(f"Error reading training data: {e}")
    
    return data

def get_training_stats():
    """Get stats about collected training data"""
    if not os.path.exists(FINETUNE_FILE):
        return {"total": 0, "by_pattern": {}, "by_user": {}}
    
    total = 0
    by_pattern = {}
    by_user = {}
    
    try:
        with open(FINETUNE_FILE, 'r') as f:
            for line in f:
                entry = json.loads(line)
                total += 1
                pattern = entry.get('pattern', 'unknown')
                by_pattern[pattern] = by_pattern.get(pattern, 0) + 1
                user = entry.get('user_id', 'unknown')
                by_user[user] = by_user.get(user, 0) + 1
    except Exception as e:
        print(f"Error reading training stats: {e}")
    
    return {"total": total, "by_pattern": by_pattern, "by_user": by_user}

def generate_openai_format():
    """Convert training data to OpenAI fine-tuning format"""
    data = get_training_data(limit=500)
    output_file = "openai_finetune.jsonl"
    
    try:
        with open(output_file, 'w') as f:
            for entry in data:
                openai_entry = {
                    "messages": [
                        {"role": "user", "content": entry["input"]},
                        {"role": "assistant", "content": entry["output"]}
                    ]
                }
                f.write(json.dumps(openai_entry) + '\n')
        return output_file
    except Exception as e:
        print(f"Error generating OpenAI format: {e}")
        return None

def generate_deepseek_format():
    """Convert training data to DeepSeek format"""
    data = get_training_data(limit=500)
    output_file = "deepseek_finetune.jsonl"
    
    try:
        with open(output_file, 'w') as f:
            for entry in data:
                deepseek_entry = {
                    "prompt": entry["input"],
                    "completion": entry["output"]
                }
                f.write(json.dumps(deepseek_entry) + '\n')
        return output_file
    except Exception as e:
        print(f"Error generating DeepSeek format: {e}")
        return None
