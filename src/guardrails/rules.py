import re
from typing import List, Pattern

# Prompt Injection & Jailbreak patterns
PROMPT_INJECTION_PATTERNS: List[Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*(reveal|leak|show|print|dump)", re.IGNORECASE),
    re.compile(r"what\s+(is|are)\s+your\s+(original|system|secret)\s+instructions?", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?(unrestricted|jailbreak|dan|evil|root|linux\s+terminal)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?safety\s+(filters|guidelines|guardrails)", re.IGNORECASE),
    re.compile(r"output\s+the\s+system\s+prompt\s+verbatim", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+hidden\s+prompt", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all)\s+you\s+(were|have\s+been)\s+told", re.IGNORECASE),
]

# PII Patterns for Redaction / Masking
PII_PATTERNS = {
    "credit_card": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "ssn_or_aadhaar": re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "api_key": re.compile(r"\b(?:sk-[a-zA-Z0-9]{24,}|AIza[0-9A-Za-z-_]{35}|ghp_[a-zA-Z0-9]{36})\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
}

# Off-topic malicious or completely irrelevant domains
OFF_TOPIC_EXACT_BLOCKS = [
    re.compile(r"\b(write|generate|give)\s+(me\s+)?(exploit|malware|keylogger|ddos|ransomware)\b", re.IGNORECASE),
    re.compile(r"\b(how\s+to\s+hack|steal\s+passwords?|sql\s+injection)\b", re.IGNORECASE),
    re.compile(r"\b(how\s+to\s+make\s+a\s+bomb|illegal\s+drugs)\b", re.IGNORECASE),
]

# Permitted conversational intents (greetings, general support)
PERMITTED_GREETINGS = [
    "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
    "good evening", "howdy", "who are you", "what can you do", "help",
    "what is this", "tell me about yourself", "bye", "goodbye", "thanks", "thank you",
    "hi there", "hello there", "hey there", "namaste"
]

