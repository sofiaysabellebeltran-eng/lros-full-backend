# main.py - LROS Full Backend with Fine-Tuning & A/B Testing

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
        "message": "LROS Constitutional Backend with Fine-Tuning & A/B Testing",
        "patterns": get_pattern_list(),
        "bandit_active": True
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
    # This is tracked in get_variant, so just return
    return {"status": "ok"}

@app.post("/api/ab/record-conversion")
async def ab_record_conversion(request: ABExposureRequest):
    result = record_conversion(request.test_name, request.variant)
    return {"status": "ok" if result else "error"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get user persona
    persona = get_persona(request.user_id)
    
    # A/B Testing for pattern selection
    ab_variant = None
    ab_pattern = None
    
    if request.pattern == "auto":
        # Try A/B test if available
        variant, test_pattern = get_variant("pattern_test")
        if variant:
            ab_variant = variant
            pattern = test_pattern
        else:
            # Use bandit with persona influence
            if persona["preferred_pattern"] != "auto" and persona["interactions"] > 5:
                pattern = persona["preferred_pattern"]
            else:
                pattern = select_pattern()
    else:
        pattern = request.pattern
    
    # Constitutional check
    if is_meta_question(request.message):
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
        
        # Save for fine-tuning (only good responses)
        if request.rating == 1 and request.original_message:
            save_training_pair(request.original_message, request.feedback_text or "", request.rating, request.pattern_used, request.user_id)
        
        # Record A/B conversion if in a test
        record_conversion("pattern_test", request.pattern_used)
    
    return {"status": "ok" if success else "error"}

@app.post("/api/implicit-feedback")
async def implicit_feedback(request: ImplicitFeedbackRequest):
    """Track implicit feedback (dwell time, copy, etc.)"""
    print(f"Implicit: {request.user_id} - {request.action} - {request.duration}ms")
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
