# robot_abstraction.py - Unified Robot Control Layer

import json
import os
from datetime import datetime
from enum import Enum

ROBOT_STATE_FILE = "robot_state.json"

class RobotType(Enum):
    LISA = "lisa"
    TEMI = "temi"
    KETTYBOT = "kettybot"
    SIMULATION = "simulation"

class RobotCommand(Enum):
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    STOP = "stop"
    SPEAK = "speak"
    FOLLOW = "follow"
    DOCK = "dock"
    EMERGENCY_STOP = "emergency_stop"

# Safe movement limits
MAX_MOVE_DISTANCE = 5.0  # meters
MAX_TURN_ANGLE = 180  # degrees
SAFE_ZONES = ["charging_station", "designated_path", "clinic_area"]

# Dangerous commands that require approval
DANGEROUS_COMMANDS = [
    RobotCommand.EMERGENCY_STOP,
    RobotCommand.DOCK
]

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
    """Register a new robot in the fleet"""
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

def validate_command(robot_id, command, params=None):
    """Validate if command is safe to execute"""
    data = load_robot_state()
    robot = data["robots"].get(robot_id)
    if not robot:
        return False, "Robot not found"
    
    # Check robot status
    if robot["status"] == "emergency":
        return False, "Robot in emergency state"
    
    # Validate move distances
    if command == RobotCommand.MOVE_FORWARD.value or command == RobotCommand.MOVE_BACKWARD.value:
        distance = params.get("distance", 0) if params else 0
        if distance > MAX_MOVE_DISTANCE:
            return False, f"Move distance {distance}m exceeds safe limit {MAX_MOVE_DISTANCE}m"
    
    # Validate turn angles
    if command == RobotCommand.TURN_LEFT.value or command == RobotCommand.TURN_RIGHT.value:
        angle = params.get("angle", 0) if params else 0
        if abs(angle) > MAX_TURN_ANGLE:
            return False, f"Turn angle {angle} exceeds safe limit {MAX_TURN_ANGLE}°"
    
    return True, "OK"

def execute_command(robot_id, command, params=None):
    """Execute a command on a robot (simulated or real)"""
    # Validate first
    valid, message = validate_command(robot_id, command, params)
    if not valid:
        return {"success": False, "message": message}
    
    # For simulation, just log
    print(f"[ROBOT] {robot_id} executing {command} with params {params}")
    
    # Log command for fleet learning
    log_robot_action(robot_id, command, params)
    
    return {"success": True, "message": "Command executed", "command": command}

def log_robot_action(robot_id, command, params):
    """Log robot action for fleet learning"""
    data = load_robot_state()
    if robot_id not in data["robots"]:
        return
    
    robot = data["robots"][robot_id]
    robot["last_action"] = {
        "command": command,
        "params": params,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add to fleet learning
    data["fleet_learning"]["shared_behaviors"].append({
        "robot_id": robot_id,
        "command": command,
        "success": True,
        "timestamp": datetime.utcnow().isoformat()
    })
    # Keep only last 1000
    data["fleet_learning"]["shared_behaviors"] = data["fleet_learning"]["shared_behaviors"][-1000:]
    
    save_robot_state(data)

def get_fleet_stats():
    """Get statistics about the robot fleet"""
    data = load_robot_state()
    active_robots = [r for r in data["robots"].values() if r["status"] != "offline"]
    return {
        "total_robots": len(data["robots"]),
        "active_robots": len(active_robots),
        "robots_by_type": {}
    }

def simulate_robot(robot_id, duration=10):
    """Run a simulation for testing robot behaviors"""
    # Simulate robot movement
    return {
        "success": True,
        "duration": duration,
        "path": [(0, 0), (1, 0), (2, 0)],
        "actions": ["move_forward", "move_forward", "stop"]
    }
