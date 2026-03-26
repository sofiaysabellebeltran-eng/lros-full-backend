# predictive.py - Predictive alerts and performance monitoring

import json
import os
from datetime import datetime, timedelta

ALERTS_FILE = "alerts.json"
PERFORMANCE_HISTORY_FILE = "performance_history.json"

def load_performance_history():
    if os.path.exists(PERFORMANCE_HISTORY_FILE):
        with open(PERFORMANCE_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"daily": [], "weekly": [], "monthly": []}

def save_performance_history(data):
    with open(PERFORMANCE_HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def record_performance_metric(metric_name, value):
    """Record a performance metric for trending"""
    data = load_performance_history()
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "metric": metric_name,
        "value": value
    }
    
    data["daily"].append(entry)
    # Keep only last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    data["daily"] = [e for e in data["daily"] if datetime.fromisoformat(e["timestamp"]) > cutoff]
    
    save_performance_history(data)
    return True

def get_performance_trend(metric_name, days=7):
    """Get trend for a metric over last N days"""
    data = load_performance_history()
    entries = [e for e in data["daily"] if e["metric"] == metric_name]
    
    # Filter by days
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) > cutoff]
    
    if len(recent) < 3:
        return {"trend": "insufficient_data", "values": recent}
    
    # Calculate trend
    values = [e["value"] for e in recent]
    first_half = sum(values[:len(values)//2]) / (len(values)//2)
    second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
    
    if second_half > first_half * 1.1:
        trend = "improving"
    elif second_half < first_half * 0.9:
        trend = "declining"
    else:
        trend = "stable"
    
    return {"trend": trend, "values": recent, "first_half_avg": first_half, "second_half_avg": second_half}

def check_alerts():
    """Check for conditions that need alerts"""
    alerts = []
    
    # Check bandit performance
    from bandit import load_bandit_data
    bandit_data = load_bandit_data()
    total_pulls = bandit_data.get("total_pulls", 0)
    
    if total_pulls > 100:
        # Check if any pattern is underperforming
        for pattern, stats in bandit_data["patterns"].items():
            if stats["pulls"] > 10 and stats["avg_reward"] < 0.3:
                alerts.append({
                    "type": "low_performance",
                    "pattern": pattern,
                    "avg_reward": stats["avg_reward"],
                    "pulls": stats["pulls"],
                    "message": f"Pattern '{pattern}' has low avg reward ({stats['avg_reward']:.2f})"
                })
    
    # Check for declining trend
    trend = get_performance_trend("avg_rating", days=7)
    if trend["trend"] == "declining" and len(trend["values"]) > 5:
        alerts.append({
            "type": "declining_trend",
            "message": "User satisfaction is declining over the last 7 days",
            "data": trend
        })
    
    return alerts

def create_alert(alert_type, message, severity="info"):
    """Create a new alert"""
    data = load_alerts()
    
    alert = {
        "id": len(data["alerts"]) + 1,
        "type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
        "resolved": False
    }
    
    data["alerts"].append(alert)
    save_alerts(data)
    return alert

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'r') as f:
            return json.load(f)
    return {"alerts": []}

def save_alerts(data):
    with open(ALERTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_active_alerts():
    data = load_alerts()
    return [a for a in data["alerts"] if not a.get("resolved", False)]
