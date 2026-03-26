# main.py - LROS Full Backend

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
import uuid

from constitution import is_meta_question, get_constitutional_response
from audit import log_interaction, update_feedback
from pattern_manager import get_pattern, get_pattern_list
from evolution_engine import run_evolution_dry

app = FastAPI(title="LROS Constitutional Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    pattern: str = "single"
    model: str = "deepseek"
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    row_index: int = None

class FeedbackRequest(BaseModel):
    row_index: int
    rating: int
    feedback_text: str = ""

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

@app.get("/")
async def root():
    return {"message": "LROS Constitutional Backend", "patterns": get_pattern_list()}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/patterns")
async def get_patterns():
    return {"patterns": get_pattern_list()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    if is_meta_question(request.message):
        response_text = get_constitutional_response()
        row_index = log_interaction(session_id, request.message, request.pattern, request.model, response_text, rating=0)
        return ChatResponse(response=response_text, row_index=row_index)
    
    pattern_config = get_pattern(request.pattern)
    
    messages = [
        {"role": "system", "content": pattern_config["system_prompt"]},
        {"role": "user", "content": request.message}
    ]
    
    try:
        if request.model == "deepseek" and DEEPSEEK_API_KEY:
            ai_response = await call_deepseek(messages)
        else:
            ai_response = f"Model {request.model} not configured."
        
        row_index = log_interaction(session_id, request.message, request.pattern, request.model, ai_response)
        return ChatResponse(response=ai_response, row_index=row_index)
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        row_index = log_interaction(session_id, request.message, request.pattern, request.model, error_msg)
        return ChatResponse(response=error_msg, row_index=row_index)

@app.post("/api/feedback")
async def feedback(request: FeedbackRequest):
    success = update_feedback(request.row_index, request.rating, request.feedback_text)
    return {"status": "ok" if success else "error"}

@app.post("/api/evolution/dry")
async def evolution_dry(x_api_key: str = Header(...)):
    if x_api_key != EVOLUTION_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    result = run_evolution_dry()
    return result