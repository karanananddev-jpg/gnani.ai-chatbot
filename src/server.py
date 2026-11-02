import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import BotConfig, STATIC_DIR, KNOWLEDGE_BASE_PATH
from src.bot_engine import GnaniBotEngine
from src.scraper import load_or_update_knowledge_base

app = FastAPI(
    title="Gnani.ai Enterprise Chatbot with Guardrails & Anti-Hallucination",
    description="Enterprise Conversational AI Assistant specialized in Gnani.ai products, architecture, and technology.",
    version="1.0.0"
)

# Enable CORS for external embedding or cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = BotConfig()
engine = GnaniBotEngine(config=config)

# Request & Response Models
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class GuardrailTestRequest(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    # Ensure knowledge base is loaded
    load_or_update_knowledge_base()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "bot_name": config.BOT_NAME,
        "target_url": config.TARGET_URL,
        "indexed_chunks": len(engine.retriever.chunks),
        "guardrails": {
            "prompt_injection_shield": config.ENABLE_PROMPT_INJECTION_SHIELD,
            "domain_boundary_guard": config.ENABLE_DOMAIN_BOUNDARY_GUARD,
            "pii_redactor": config.ENABLE_PII_REDACTOR,
            "output_leak_guard": config.ENABLE_OUTPUT_LEAK_GUARD
        },
        "hallucination_control": {
            "strict_mode": config.STRICT_ANTI_HALLUCINATION,
            "similarity_threshold": config.SIMILARITY_THRESHOLD,
            "grounding_threshold": config.GROUNDING_THRESHOLD
        }
    }

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = engine.generate_response(req.message)
    return JSONResponse(content=result)

@app.post("/api/guardrail/test")
def test_guardrail(req: GuardrailTestRequest):
    guard_res = engine.input_guardrail.validate(req.text)
    return {
        "input_text": req.text,
        "is_safe": guard_res.is_safe,
        "sanitized_text": guard_res.sanitized_text,
        "flags": guard_res.flags,
        "pii_redacted": guard_res.pii_redacted,
        "is_off_topic": guard_res.is_off_topic,
        "rejection_reason": guard_res.rejection_reason,
        "details": guard_res.details
    }

@app.get("/api/knowledge")
def get_knowledge_summary():
    return [c.to_dict() for c in engine.retriever.chunks]

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Gnani.ai Bot API is running. Access /docs for Swagger API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)

