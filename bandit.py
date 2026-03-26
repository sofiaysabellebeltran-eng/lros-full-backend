# bandit.py - Multi-armed bandit for pattern selection

import json
import os
import random
from datetime import datetime

BANDIT_FILE = "bandit_data.json"

def load_bandit_data():
    """Load bandit performance data"""
    if os.path.exists(BANDIT_FILE):
        with open(BANDIT_FILE, 'r') as f:
            return json.load(f)
    return {
        "patterns": {
            "single": {"rewards": 0, "pulls": 0, "avg_reward": 0},
            "chain": {"rewards": 0, "pulls": 0, "avg_reward": 0},
            "parallel": {"rewards": 0, "pulls": 0, "avg_reward": 0}
        },
        "exploration_rate": 0.2,
        "total_pulls": 0,
        "last_updated": datetime.utcnow().isoformat()
    }

def save_bandit_data(data):
    """Save bandit data"""
    with open(BANDIT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_bandit(pattern, reward):
    """Update bandit with new feedback (reward: 1 for good, 0 for bad)"""
    data = load_bandit_data()
    
    if pattern in data["patterns"]:
        data["patterns"][pattern]["pulls"] += 1
        data["patterns"][pattern]["rewards"] += reward
        data["patterns"][pattern]["avg_reward"] = (
            data["patterns"][pattern]["rewards"] / 
            data["patterns"][pattern]["pulls"]
        )
        data["total_pulls"] += 1
        data["last_updated"] = datetime.utcnow().isoformat()
        save_bandit_data(data)
        return True
    return False

def select_pattern():
    """Select pattern using epsilon-greedy algorithm"""
    data = load_bandit_data()
    patterns = data["patterns"]
    exploration_rate = data["exploration_rate"]
    
    # Exploration: pick random pattern
    if random.random() < exploration_rate:
        pattern = random.choice(list(patterns.keys()))
    else:
        # Exploitation: pick pattern with highest average reward
        best_pattern = max(patterns.keys(), key=lambda p: patterns[p]["avg_reward"])
        pattern = best_pattern
    
    return pattern

def get_bandit_stats():
    """Get current bandit statistics"""
    data = load_bandit_data()
    return {
        "patterns": data["patterns"],
        "exploration_rate": data["exploration_rate"],
        "total_pulls": data["total_pulls"]
    }
