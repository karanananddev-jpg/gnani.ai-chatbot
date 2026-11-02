import re
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

class GroundingVerificationResult(BaseModel):
    grounding_score: float  # 0.0 to 1.0
    hallucination_risk: str  # "LOW", "MEDIUM", "HIGH"
    supported_sentences: List[str] = []
    ungrounded_sentences: List[str] = []
    verified_entities: List[str] = []
    unverified_entities: List[str] = []

class GroundingVerifier:
    def __init__(self, threshold: float = 0.55):
        self.threshold = threshold

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split on sentence terminals while avoiding splitting on common abbreviations
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
        return sentences

    def _extract_key_tokens(self, text: str) -> set:
        # Extract meaningful alphanumeric tokens (length > 3)
        tokens = re.findall(r"\b[A-Za-z0-9\-\.]{4,}\b", text.lower())
        stopwords = {
            "this", "that", "these", "those", "with", "from", "have", "been",
            "were", "which", "their", "there", "about", "would", "could",
            "should", "gnani", "please", "also", "into", "more", "other"
        }
        return {t for t in tokens if t not in stopwords}

    def verify_grounding(self, generated_text: str, context_chunks: List[str]) -> GroundingVerificationResult:
        """
        Cross-checks generated statements against source context.
        Computes token overlap and sentence support ratios.
        """
        combined_context = " ".join(context_chunks).lower()
        context_tokens = self._extract_key_tokens(combined_context)

        sentences = self._split_into_sentences(generated_text)
        if not sentences:
            return GroundingVerificationResult(
                grounding_score=1.0,
                hallucination_risk="LOW",
                supported_sentences=[],
                ungrounded_sentences=[]
            )

        supported = []
        ungrounded = []

        for sentence in sentences:
            # Check overlap of sentence tokens with context tokens
            s_tokens = self._extract_key_tokens(sentence)
            if not s_tokens:
                supported.append(sentence)
                continue

            matching_tokens = s_tokens.intersection(context_tokens)
            overlap_ratio = len(matching_tokens) / len(s_tokens)

            # A sentence is supported if at least 45% of its informative content words align with source text
            if overlap_ratio >= 0.40:
                supported.append(sentence)
            else:
                ungrounded.append(sentence)

        grounding_score = len(supported) / len(sentences) if sentences else 1.0

        if grounding_score >= 0.75:
            risk = "LOW"
        elif grounding_score >= 0.50:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        return GroundingVerificationResult(
            grounding_score=round(grounding_score, 2),
            hallucination_risk=risk,
            supported_sentences=supported,
            ungrounded_sentences=ungrounded
        )

