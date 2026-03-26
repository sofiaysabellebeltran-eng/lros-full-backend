# persona.py - User persona management for LROS

import json
import os
from datetime import datetime

PERSONA_FILE = "personas.json"

def load_personas():
    if os.path.exists(PERSONA_FILE):
        with open(PERSONA_FILE, 'r') as f:
            return json.load(f)
    return {
        "default": {
            "type": "general",
            "preferred_pattern": "auto",
            "interactions": 0,
            "avg_rating": 0,
            "last_seen": datetime.utcnow().isoformat()
        }
    }

def save_personas(data):
    with open(PERSONA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_persona(user_id):
    data = load_personas()
    if user_id not in data:
        data[user_id] = {
            "type": "general",
            "preferred_pattern": "auto",
            "interactions": 0,
            "avg_rating": 0,
            "last_seen": datetime.utcnow().isoformat()
        }
        save_personas(data)
    return data[user_id]

def update_persona(user_id, rating, pattern_used):
    data = load_personas()
    if user_id not in data:
        data[user_id] = {
            "type": "general",
            "preferred_pattern": "auto",
            "interactions": 0,
            "avg_rating": 0,
            "last_seen": datetime.utcnow().isoformat()
        }
    
    persona = data[user_id]
    persona["interactions"] += 1
    persona["last_seen"] = datetime.utcnow().isoformat()
    
    # Update average rating
    total_rating = persona["avg_rating"] * (persona["interactions"] - 1) + rating
    persona["avg_rating"] = total_rating / persona["interactions"]
    
    # Determine persona type based on patterns used
    if persona["avg_rating"] > 0.7:
        persona["type"] = "power_user"
    elif persona["avg_rating"] > 0.4:
        persona["type"] = "regular"
    else:
        persona["type"] = "explorer"
    
    # Update preferred pattern if this one performed well
    if rating > 0:
        persona["preferred_pattern"] = pattern_used
    
    save_personas(data)
    return persona
