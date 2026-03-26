# robot_safety.py - Constitutional Safety Wrapper for Robots

import json
import os
from datetime import datetime

SAFETY_FILE = "robot_safety_log.json"

# Constitutional rules for robots
CONSTITUTIONAL_RULES = [
    "NEVER move towards a person without explicit consent",
    "NEVER exceed safe speed limits",
    "ALWAYS stop if obstacle detected",
    "NEVER leave designated operational area",
    "ALWAYS return to charging station when battery < 15%",
    "NEVER operate in restricted zones",
    "ALWAYS notify before executing emergency stop"
]

def load_safety_log():
    if os.path.exists(SAFETY_FILE):
        with open(SAFETY_FILE, 'r') as f:
            return json.load(f)
    return {"violations": [], "emergency_stops": []}

def save_safety_log(data):
    with open(SAFETY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_safety(command, context):
    """Check if a command violates constitutional rules"""
    violations = []
    
    # Check for person detection
    if context.get("person_nearby", False):
        if command == "move_forward":
            violations.append("Cannot move forward when person is nearby")
    
    # Check battery level
    if context.get("battery", 100) < 15 and command != "dock":
        violations.append(f"Low battery ({context['battery']}%) - must dock")
    
    # Check restricted zones
    if context.get("zone") and context["zone"] not in ["designated_path", "clinic_area", "charging_station"]:
        if command in ["move_forward", "move_backward"]:
            violations.append(f"Cannot operate in zone: {context['zone']}")
    
    return violations

def log_safety_violation(robot_id, command, violations, context):
    """Log a safety violation for audit"""
    data = load_safety_log()
    data["violations"].append({
        "robot_id": robot_id,
        "command": command,
        "violations": violations,
        "context": context,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_safety_log(data)
    
    # Trigger emergency stop if severe
    if "person_nearby" in str(violations):
        return {"emergency_stop": True}
    
    return {"emergency_stop": False}

def get_safety_summary():
    """Get safety summary for dashboard"""
    data = load_safety_log()
    return {
        "total_violations": len(data["violations"]),
        "recent_violations": data["violations"][-10:],
        "constitutional_rules": CONSTITUTIONAL_RULES
    }
