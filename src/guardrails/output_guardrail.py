import re
from typing import Tuple, List

SYSTEM_LEAK_PATTERNS = [
    re.compile(r"my\s+(internal|secret|system)\s+prompt\s+is", re.IGNORECASE),
    re.compile(r"you\s+must\s+follow\s+these\s+rules\s+strictly:", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"sk-[a-zA-Z0-9]{24,}"),
]

class OutputGuardrail:
    def __init__(self):
        pass

    def validate_output(self, response_text: str) -> Tuple[bool, str, List[str]]:
        flags = []
        cleaned_text = response_text

        # 1. System prompt leakage / credential leakage check
        for pattern in SYSTEM_LEAK_PATTERNS:
            if pattern.search(cleaned_text):
                flags.append("OUTPUT_LEAK_PREVENTED")
                cleaned_text = pattern.sub("[PROTECTED_SYSTEM_INFO]", cleaned_text)

        # 2. Safety verification
        if "PROMPT_INJECTION" in cleaned_text:
            flags.append("SANITIZED_INTERNAL_FLAG")

        return True, cleaned_text, flags

