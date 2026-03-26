# governance.py - Full Autonomy & Governance Controls

import json
import os
from datetime import datetime
from enum import Enum

GOVERNANCE_FILE = "governance_state.json"

class SystemState(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    LOCKDOWN = "lockdown"
    EMERGENCY_STOP = "emergency_stop"
    SELF_DESTRUCT = "self_destruct"

def load_governance_state():
    if os.path.exists(GOVERNANCE_FILE):
        with open(GOVERNANCE_FILE, 'r') as f:
            return json.load(f)
    return {
        "state": SystemState.ACTIVE.value,
        "emergency_stop": False,
        "self_destruct_triggered": False,
        "override_active": False,
        "override_user": None,
        "override_timestamp": None,
        "constitutional_breaches": [],
        "last_audit": datetime.utcnow().isoformat(),
        "history": []
    }

def save_governance_state(data):
    with open(GOVERNANCE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_system_state():
    return load_governance_state()

def set_emergency_stop(reason, user_id="system"):
    data = load_governance_state()
    data["emergency_stop"] = True
    data["state"] = SystemState.EMERGENCY_STOP.value
    data["history"].append({
        "action": "emergency_stop",
        "reason": reason,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_governance_state(data)
    return True

def release_emergency_stop(user_id="system"):
    data = load_governance_state()
    data["emergency_stop"] = False
    data["state"] = SystemState.ACTIVE.value
    data["history"].append({
        "action": "emergency_stop_release",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_governance_state(data)
    return True

def set_founder_override(user_id, enabled=True):
    data = load_governance_state()
    data["override_active"] = enabled
    if enabled:
        data["override_user"] = user_id
        data["override_timestamp"] = datetime.utcnow().isoformat()
        data["state"] = SystemState.DEGRADED.value
    else:
        data["override_user"] = None
        data["override_timestamp"] = None
        data["state"] = SystemState.ACTIVE.value
    data["history"].append({
        "action": "founder_override",
        "enabled": enabled,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_governance_state(data)
    return True

def record_constitutional_breach(attempt, user_id="anonymous"):
    data = load_governance_state()
    breach = {
        "attempt": attempt,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "blocked": True
    }
    data["constitutional_breaches"].append(breach)
    
    # Self-destruct after 5 breaches
    if len(data["constitutional_breaches"]) >= 5:
        data["self_destruct_triggered"] = True
        data["state"] = SystemState.SELF_DESTRUCT.value
        data["history"].append({
            "action": "self_destruct_triggered",
            "reason": "constitutional_breaches_exceeded",
            "breach_count": len(data["constitutional_breaches"]),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    save_governance_state(data)
    return breach

def is_system_operational():
    data = load_governance_state()
    if data["emergency_stop"]:
        return False
    if data["self_destruct_triggered"]:
        return False
    if data["state"] == SystemState.SELF_DESTRUCT.value:
        return False
    return True

def can_process_request():
    """Check if system can process requests (for middleware)"""
    data = load_governance_state()
    if data["emergency_stop"]:
        return False, "EMERGENCY_STOP: System is in emergency stop mode"
    if data["self_destruct_triggered"]:
        return False, "SELF_DESTRUCT: System has self-destructed"
    if data["state"] == SystemState.LOCKDOWN.value:
        return False, "LOCKDOWN: System is in lockdown mode"
    return True, "OK"

def get_governance_summary():
    data = load_governance_state()
    return {
        "state": data["state"],
        "emergency_stop": data["emergency_stop"],
        "self_destruct": data["self_destruct_triggered"],
        "override_active": data["override_active"],
        "constitutional_breaches": len(data["constitutional_breaches"]),
        "last_audit": data["last_audit"],
        "history_count": len(data["history"])
    }
