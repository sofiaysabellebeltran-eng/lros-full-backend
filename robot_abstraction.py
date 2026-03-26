# robot_abstraction.py - Unified Robot Control Layer

import json
import os
from datetime import datetime

ROBOT_STATE_FILE = "robot_state.json"

def load_robot_state():
    if os.path.exists(ROBOT_STATE_FILE):
        with open(ROBOT_STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "robots": {},
        "fleet_learning": {
            "shared_behaviors": [],
            "last_sync": None
        }
    }

def save_robot_state(data):
    with open(ROBOT_STATE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def register_robot(robot_id, robot_type, capabilities=None):
    data = load_robot_state()
    data["robots"][robot_id] = {
        "type": robot_type,
        "status": "idle",
        "capabilities": capabilities or ["move", "speak"],
        "last_contact": datetime.utcnow().isoformat(),
        "position": {"x": 0, "y": 0, "orientation": 0},
        "battery": 100,
        "registered_at": datetime.utcnow().isoformat()
    }
    save_robot_state(data)
    return data["robots"][robot_id]

def execute_command(robot_id, command, params=None):
    print(f"[ROBOT] {robot_id} executing {command} with params {params}")
    return {"success": True, "message": "Command executed", "command": command}

def get_fleet_stats():
    data = load_robot_state()
    active_robots = [r for r in data["robots"].values() if r["status"] != "offline"]
    return {
        "total_robots": len(data["robots"]),
        "active_robots": len(active_robots),
        "robots_by_type": {}
    }

def simulate_robot(robot_id, duration=10):
    return {
        "success": True,
        "duration": duration,
        "path": [(0, 0), (1, 0), (2, 0)],
        "actions": ["move_forward", "move_forward", "stop"]
    }
