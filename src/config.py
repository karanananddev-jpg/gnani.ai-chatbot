import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_BASE_PATH = DATA_DIR / "gnani_knowledge_base.json"
STATIC_DIR = BASE_DIR / "static"

class BotConfig:
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Target URL & Branding
    TARGET_URL: str = "https://www.gnani.ai/"
    BOT_NAME: str = "Gnani AI Assistant"
    
    # Hardcoded Gemini API Key provided by user
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "gemini")
    
    # Retrieval & Hallucination Thresholds
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.20"))
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "3"))
    GROUNDING_THRESHOLD: float = float(os.getenv("GROUNDING_THRESHOLD", "0.55"))
    STRICT_ANTI_HALLUCINATION: bool = True
    
    # Guardrail Controls
    ENABLE_PROMPT_INJECTION_SHIELD: bool = True
    ENABLE_DOMAIN_BOUNDARY_GUARD: bool = True
    ENABLE_PII_REDACTOR: bool = True
    ENABLE_OUTPUT_LEAK_GUARD: bool = True
    
    # Domain Keywords (Gnani AI platform, conversational AI, company location, and weather queries)
    DOMAIN_KEYWORDS = [
        "gnani", "gnani.ai", "voice", "speech", "asr", "stt", "tts", "voice bot", "chatbot",
        "conversational ai", "contact center", "call center", "agent assist", "assist365",
        "armour365", "inya", "aura365", "biometrics", "voiceprint", "prisma", "timbre",
        "vachana", "indic", "slm", "llm", "ivr", "ganesh gopalan", "ananth nagaraj",
        "telecom", "bfsi", "banking", "liveness", "anti-spoofing", "bengaluru", "bangalore",
        "workforce", "diy", "omnichannel", "cx", "customer experience", "sentiment",
        # Location & Weather keywords
        "location", "headquarters", "address", "office", "where are you located", "where is gnani",
        "weather", "wheather", "temperature", "forecast", "climate", "rain", "humidity"
    ]
