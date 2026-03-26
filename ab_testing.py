# ab_testing.py - A/B testing framework for patterns

import json
import os
import random
from datetime import datetime

AB_TEST_FILE = "ab_tests.json"

def load_tests():
    if os.path.exists(AB_TEST_FILE):
        with open(AB_TEST_FILE, 'r') as f:
            return json.load(f)
    return {
        "active_tests": {},
        "completed_tests": [],
        "history": []
    }

def save_tests(data):
    with open(AB_TEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def create_test(name, variant_a, variant_b, traffic_split=0.5):
    """Create a new A/B test"""
    data = load_tests()
    data["active_tests"][name] = {
        "variant_a": variant_a,
        "variant_b": variant_b,
        "traffic_split": traffic_split,
        "exposures_a": 0,
        "exposures_b": 0,
        "conversions_a": 0,
        "conversions_b": 0,
        "started": datetime.utcnow().isoformat()
    }
    save_tests(data)
    return name

def get_variant(test_name):
    """Get which variant to show to a user"""
    data = load_tests()
    if test_name not in data["active_tests"]:
        return None, None
    
    test = data["active_tests"][test_name]
    if random.random() < test["traffic_split"]:
        variant = "a"
        test["exposures_a"] += 1
    else:
        variant = "b"
        test["exposures_b"] += 1
    
    save_tests(data)
    return variant, test[f"variant_{variant}"]

def record_conversion(test_name, variant):
    """Record a successful conversion (e.g., good feedback)"""
    data = load_tests()
    if test_name not in data["active_tests"]:
        return False
    
    if variant == "a":
        data["active_tests"][test_name]["conversions_a"] += 1
    else:
        data["active_tests"][test_name]["conversions_b"] += 1
    
    # Log to history
    data["history"].append({
        "test": test_name,
        "variant": variant,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    save_tests(data)
    return True

def get_test_results(test_name):
    """Get results of a test"""
    data = load_tests()
    if test_name not in data["active_tests"]:
        return None
    
    test = data["active_tests"][test_name]
    rate_a = test["conversions_a"] / test["exposures_a"] if test["exposures_a"] > 0 else 0
    rate_b = test["conversions_b"] / test["exposures_b"] if test["exposures_b"] > 0 else 0
    
    return {
        "test_name": test_name,
        "variant_a": test["variant_a"],
        "variant_b": test["variant_b"],
        "exposures_a": test["exposures_a"],
        "exposures_b": test["exposures_b"],
        "conversions_a": test["conversions_a"],
        "conversions_b": test["conversions_b"],
        "conversion_rate_a": round(rate_a, 4),
        "conversion_rate_b": round(rate_b, 4),
        "winner": "a" if rate_a > rate_b else "b" if rate_b > rate_a else "tie",
        "started": test["started"]
    }

def get_all_tests():
    """Get all active tests"""
    data = load_tests()
    results = []
    for test_name in data["active_tests"]:
        results.append(get_test_results(test_name))
    return results

def end_test(test_name):
    """End an A/B test and move to completed"""
    data = load_tests()
    if test_name not in data["active_tests"]:
        return None
    
    result = get_test_results(test_name)
    data["completed_tests"].append(result)
    del data["active_tests"][test_name]
    save_tests(data)
    return result
