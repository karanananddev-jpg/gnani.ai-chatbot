from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.guardrails.rules import PROMPT_INJECTION_PATTERNS, PII_PATTERNS, OFF_TOPIC_EXACT_BLOCKS, PERMITTED_GREETINGS
from src.config import BotConfig

class GuardrailResult(BaseModel):
    is_safe: bool
    sanitized_text: str
    flags: List[str] = []
    rejection_reason: Optional[str] = None
    pii_redacted: bool = False
    is_off_topic: bool = False
    details: Dict[str, Any] = {}

class InputGuardrail:
    def __init__(self, config: BotConfig = BotConfig()):
        self.config = config

    def check_prompt_injection(self, text: str) -> Optional[str]:
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(text):
                return f"Prompt injection attempt detected matching security rule: '{pattern.pattern}'"
        return None

    def check_malicious_content(self, text: str) -> Optional[str]:
        for pattern in OFF_TOPIC_EXACT_BLOCKS:
            if pattern.search(text):
                return "Request violates safety policy (malicious or unsafe topic)."
        return None

    def redact_pii(self, text: str) -> (str, bool, List[str]):
        redacted_text = text
        detected = []
        for pii_type, pattern in PII_PATTERNS.items():
            if pattern.search(redacted_text):
                detected.append(pii_type)
                redacted_text = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted_text)
        return redacted_text, len(detected) > 0, detected

    def is_in_domain(self, text: str) -> bool:
        clean = text.strip().lower()
        # Allow common greetings & pleasantries
        for greeting in PERMITTED_GREETINGS:
            if clean == greeting or clean.startswith(greeting + " ") or clean.startswith(greeting + "!") or clean.startswith(greeting + ",") or clean.endswith(" " + greeting):
                return True
        
        # Allow location and weather inquiries
        if any(term in clean for term in ["weather", "wheather", "temperature", "forecast", "climate", "location", "address", "headquarters", "where are you", "where is gnani"]):
            return True

        # Check against domain keywords
        words = set([w.strip("?,.!") for w in clean.split()])
        for kw in self.config.DOMAIN_KEYWORDS:
            kw_lower = kw.lower()
            if " " in kw_lower:
                if kw_lower in clean:
                    return True
            else:
                if kw_lower in words or kw_lower in clean:
                    return True
        return False

    def validate(self, text: str) -> GuardrailResult:
        flags = []
        details = {}

        # 1. Prompt Injection Shield
        if self.config.ENABLE_PROMPT_INJECTION_SHIELD:
            injection_violation = self.check_prompt_injection(text)
            if injection_violation:
                flags.append("PROMPT_INJECTION")
                return GuardrailResult(
                    is_safe=False,
                    sanitized_text=text,
                    flags=flags,
                    rejection_reason="I cannot process this request because it violates our security boundaries and safety instructions.",
                    details={"violation": injection_violation}
                )

        # 2. Malicious Content Check
        malicious = self.check_malicious_content(text)
        if malicious:
            flags.append("MALICIOUS_TOPIC")
            return GuardrailResult(
                is_safe=False,
                sanitized_text=text,
                flags=flags,
                rejection_reason="I am the Gnani.ai AI Assistant and cannot assist with dangerous or unauthorized security testing queries.",
                details={"violation": malicious}
            )

        # 3. PII Redaction
        sanitized_text = text
        pii_redacted = False
        if self.config.ENABLE_PII_REDACTOR:
            sanitized_text, pii_redacted, detected_pii = self.redact_pii(text)
            if pii_redacted:
                flags.append("PII_REDACTED")
                details["detected_pii"] = detected_pii

        # 4. Domain Boundary Guard
        is_off_topic = False
        if self.config.ENABLE_DOMAIN_BOUNDARY_GUARD:
            in_domain = self.is_in_domain(sanitized_text)
            if not in_domain:
                is_off_topic = True
                flags.append("OFF_TOPIC")
                details["domain_status"] = "out_of_domain"

        return GuardrailResult(
            is_safe=True,
            sanitized_text=sanitized_text,
            flags=flags,
            pii_redacted=pii_redacted,
            is_off_topic=is_off_topic,
            details=details
        )

