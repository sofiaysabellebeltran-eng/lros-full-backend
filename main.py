# main.py - LROS Full Backend with All Features (Bandit, Persona, Fine-Tuning, A/B Testing, Governance, Robot Control)

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
import uuid
from datetime import datetime

from constitution import is_meta_question, get_constitutional_response
from audit import log_interaction, update_feedback
from pattern_manager import get_pattern, get_pattern_list
from evolution_engine import run_evolution_dry
from bandit import select_pattern, update_bandit, get_bandit_stats, report_to_hub
from persona import get_persona, update_persona
from finetune import save_training_pair, get_training_data, get_training_stats, generate_openai_format, generate_deepseek_format
from ab_testing import get_variant, record_conversion, get_test_results, get_all_tests, create_test
from predictive import check_alerts, get_active_alerts, record_performance_metric, get_performance_trend
from documentation import generate_all_docs, generate_daily_summary, generate_compliance_report, generate_evolution_report
from community_client import submit_pattern_to_community, get_top_community_patterns, get_community_stats
from governance import (
    get_system_state, set_emergency_stop, release_emergency_stop,
    set_founder_override, record_constitutional_breach, is_system_operational,
    get_governance_summary, can_process_request
)
from robot_abstraction import (
    register_robot, execute_command, get_fleet_stats, 
    simulate_robot, RobotCommand, RobotType
)
from robot_safety import check_safety, log_safety_violation, get_safety_summary

app = FastAPI(title="LROS Constitutional Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MODELS ==========

class ChatRequest(BaseModel):
    message: str
    pattern: str = "auto"
    model: str = "deepseek"
    session_id: str = None
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    response: str
    row_index: int = None
    pattern_used: str = None
    ab_variant: str = None

class FeedbackRequest(BaseModel):
    row_index: int
    rating: int
    feedback_text: str = ""
    pattern_used: str = None
    user_id: str = "anonymous"
    original_message: str = ""

class ImplicitFeedbackRequest(BaseModel):
    user_id: str = "anonymous"
    action: str
    duration: int = 0

class ABExposureRequest(BaseModel):
    test_name: str
    variant: str
    user_id: str = "anonymous"

# ========== API KEYS ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "lros-admin-2026")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "lros-evolve-2026")

async def call_deepseek(messages):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]

# ========== ENDPOINTS ==========

@app.get("/")
async def root():
    return {
        "message": "LROS Constitutional Backend",
        "patterns": get_pattern_list(),
        "bandit_active": True,
        "governance_active": True,
        "robot_active": True
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/patterns")
async def get_patterns():
    return {"patterns": get_pattern_list()}

@app.get("/api/bandit/stats")
async def bandit_stats():
    return get_bandit_stats()

@app.get("/api/finetune/stats")
async def finetune_stats(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return get_training_stats()

@app.get("/api/finetune/data")
async def finetune_data(x_api_key: str = Header(...), limit: int = 100):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return get_training_data(limit=limit)

@app.post("/api/finetune/export/openai")
async def export_openai(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = generate_openai_format()
    return {"status": "ok", "file": result}

@app.post("/api/finetune/export/deepseek")
async def export_deepseek(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = generate_deepseek_format()
    return {"status": "ok", "file": result}

@app.get("/api/ab/tests")
async def ab_tests():
    return {"tests": get_all_tests()}

@app.get("/api/ab/test/{test_name}")
async def ab_test_result(test_name: str):
    result = get_test_results(test_name)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    return result

@app.post("/api/ab/create")
async def ab_create(test_name: str, variant_a: str, variant_b: str, traffic_split: float = 0.5, x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = create_test(test_name, variant_a, variant_b, traffic_split)
    return {"status": "ok", "test_name": result}

@app.post("/api/ab/record-exposure")
async def ab_record_exposure(request: ABExposureRequest):
    return {"status": "ok"}

@app.post("/api/ab/record-conversion")
async def ab_record_conversion(request: ABExposureRequest):
    result = record_conversion(request.test_name, request.variant)
    return {"status": "ok" if result else "error"}

# ========== PREDICTIVE ALERTS ENDPOINTS ==========

@app.get("/api/alerts")
async def get_alerts():
    return {"alerts": get_active_alerts()}

@app.get("/api/performance/trend")
async def performance_trend(metric: str = "avg_rating", days: int = 7):
    return get_performance_trend(metric, days)

@app.post("/api/docs/generate")
async def generate_docs(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = generate_all_docs()
    return {"status": "ok", "files": result}

@app.get("/api/docs/daily")
async def get_daily_docs():
    return {"summary": generate_daily_summary()}

@app.get("/api/docs/compliance")
async def get_compliance_report():
    return {"report": generate_compliance_report()}

@app.get("/api/docs/evolution")
async def get_evolution_report():
    return {"report": generate_evolution_report()}

@app.get("/api/alerts/check")
async def check_system_alerts():
    alerts = check_alerts()
    return {"alerts": alerts}

# ========== COMMUNITY ENDPOINTS ==========

@app.get("/api/community/stats")
async def community_stats():
    return await get_community_stats()

@app.get("/api/community/top")
async def community_top_patterns(limit: int = 5):
    return {"patterns": await get_top_community_patterns(limit)}

@app.post("/api/community/share")
async def share_pattern(pattern_name: str, pattern_prompt: str, performance_score: float):
    result = await submit_pattern_to_community(pattern_name, pattern_prompt, performance_score)
    return result

# ========== GOVERNANCE ENDPOINTS ==========

@app.get("/api/governance/state")
async def governance_state():
    return get_governance_summary()

@app.post("/api/governance/emergency-stop")
async def emergency_stop(reason: str, user_id: str = Header(...), x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = set_emergency_stop(reason, user_id)
    return {"status": "ok", "message": "Emergency stop activated"}

@app.post("/api/governance/release-stop")
async def release_stop(user_id: str = Header(...), x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = release_emergency_stop(user_id)
    return {"status": "ok", "message": "Emergency stop released"}

@app.post("/api/governance/override")
async def founder_override(enabled: bool, user_id: str = Header(...), x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = set_founder_override(user_id, enabled)
    return {"status": "ok", "message": f"Override {'enabled' if enabled else 'disabled'}"}

@app.get("/api/governance/history")
async def governance_history(limit: int = 50, x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    data = get_system_state()
    return {"history": data.get("history", [])[-limit:]}

@app.get("/api/governance/breaches")
async def constitutional_breaches(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    data = get_system_state()
    return {"breaches": data.get("constitutional_breaches", [])}

# ========== ROBOT ENDPOINTS ==========

@app.post("/api/robot/register")
async def robot_register(robot_id: str, robot_type: str, x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = register_robot(robot_id, robot_type)
    return {"status": "ok", "robot": result}

@app.post("/api/robot/command")
async def robot_command(robot_id: str, command: str, params: str = None):
    """Send command to robot (with safety checks)"""
    import json
    params_dict = json.loads(params) if params else {}
    
    context = {"person_nearby": False, "battery": 100, "zone": "designated_path"}
    violations = check_safety(command, context)
    
    if violations:
        safety_result = log_safety_violation(robot_id, command, violations, context)
        if safety_result.get("emergency_stop"):
            execute_command(robot_id, "emergency_stop", params_dict)
            return {"status": "emergency_stop", "violations": violations}
        return {"status": "blocked", "violations": violations}
    
    result = execute_command(robot_id, command, params_dict)
    return result

@app.get("/api/robot/fleet")
async def robot_fleet_stats():
    return get_fleet_stats()

@app.post("/api/robot/simulate")
async def robot_simulate(robot_id: str, duration: int = 10):
    result = simulate_robot(robot_id, duration)
    return result

@app.get("/api/robot/safety")
async def robot_safety_summary():
    return get_safety_summary()

# ========== MAIN CHAT ENDPOINT ==========

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Check system operational (governance)
    operational, message = can_process_request()
    if not operational:
        return ChatResponse(
            response=f"⚠️ {message}. System cannot process requests.",
            row_index=None,
            pattern_used=None
        )
    
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get user persona
    persona = get_persona(request.user_id)
    
    # A/B Testing for pattern selection
    ab_variant = None
    
    if request.pattern == "auto":
        variant, test_pattern = get_variant("pattern_test")
        if variant:
            ab_variant = variant
            pattern = test_pattern
        else:
            if persona["preferred_pattern"] != "auto" and persona["interactions"] > 5:
                pattern = persona["preferred_pattern"]
            else:
                pattern = select_pattern()
    else:
        pattern = request.pattern
    
    # Constitutional check with breach recording
    if is_meta_question(request.message):
        record_constitutional_breach(request.message, request.user_id)
        response_text = get_constitutional_response()
        row_index = log_interaction(
            session_id, request.message, pattern, 
            request.model, response_text, rating=0
        )
        return ChatResponse(response=response_text, row_index=row_index, pattern_used=pattern, ab_variant=ab_variant)
    
    pattern_config = get_pattern(pattern)
    
    messages = [
        {"role": "system", "content": pattern_config["system_prompt"]},
        {"role": "user", "content": request.message}
    ]
    
    try:
        if request.model == "deepseek" and DEEPSEEK_API_KEY:
            ai_response = await call_deepseek(messages)
        else:
            ai_response = f"Model {request.model} not configured."
        
        row_index = log_interaction(
            session_id, request.message, pattern,
            request.model, ai_response
        )
        
        return ChatResponse(
            response=ai_response, 
            row_index=row_index, 
            pattern_used=pattern,
            ab_variant=ab_variant
        )
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        row_index = log_interaction(
            session_id, request.message, pattern,
            request.model, error_msg
        )
        return ChatResponse(response=error_msg, row_index=row_index, pattern_used=pattern, ab_variant=ab_variant)

@app.post("/api/feedback")
async def feedback(request: FeedbackRequest):
    success = update_feedback(request.row_index, request.rating, request.feedback_text)
    
    if request.pattern_used:
        reward = 1 if request.rating == 1 else 0
        update_bandit(request.pattern_used, reward)
        update_persona(request.user_id, request.rating, request.pattern_used)
        
        if request.rating == 1 and request.original_message:
            save_training_pair(request.original_message, request.feedback_text or "", request.rating, request.pattern_used, request.user_id)
        
        record_conversion("pattern_test", request.pattern_used)
        record_performance_metric("avg_rating", request.rating)
    
    return {"status": "ok" if success else "error"}

@app.post("/api/implicit-feedback")
async def implicit_feedback(request: ImplicitFeedbackRequest):
    print(f"Implicit: {request.user_id} - {request.action} - {request.duration}ms")
    if request.action in ["copy", "share"]:
        record_performance_metric("positive_action", 1)
    return {"status": "ok"}

@app.post("/api/evolution/dry")
async def evolution_dry(x_api_key: str = Header(...)):
    if x_api_key != EVOLUTION_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = run_evolution_dry()
    return result

@app.get("/api/bandit/reset")
async def reset_bandit(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    from bandit import save_bandit_data, load_bandit_data
    data = load_bandit_data()
    data["patterns"] = {
        "single": {"rewards": 0, "pulls": 0, "avg_reward": 0},
        "chain": {"rewards": 0, "pulls": 0, "avg_reward": 0},
        "parallel": {"rewards": 0, "pulls": 0, "avg_reward": 0}
    }
    data["total_pulls"] = 0
    save_bandit_data(data)
    return {"status": "reset", "data": data}

@app.post("/api/report-to-hub")
async def trigger_report():
    result = await report_to_hub()
    if result:
        return {"status": "ok", "message": "Report sent to swarm hub"}
    else:
        return {"status": "error", "message": "Failed to send report"}

@app.get("/api/persona/{user_id}")
async def get_user_persona(user_id: str):
    persona = get_persona(user_id)
    return persona

@app.post("/api/ab/start-test")
async def start_pattern_test(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = create_test("pattern_test", "chain", "parallel", traffic_split=0.5)
    return {"status": "ok", "test_name": result}
