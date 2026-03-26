# pattern_manager.py - Pattern registry management

import json
import os

PATTERN_FILE = "pattern_registry.json"

def load_patterns():
    if os.path.exists(PATTERN_FILE):
        with open(PATTERN_FILE, "r") as f:
            return json.load(f)
    return {"patterns": {}}

def get_pattern(pattern_name):
    patterns = load_patterns()
    return patterns["patterns"].get(pattern_name, patterns["patterns"].get("single", {
        "version": 1,
        "system_prompt": "You are a helpful assistant.",
        "temperature": 0.7,
        "max_tokens": 500
    }))

def get_pattern_list():
    patterns = load_patterns()
    return list(patterns["patterns"].keys())