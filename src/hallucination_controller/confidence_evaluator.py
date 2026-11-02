from typing import Dict, Any

class ConfidenceEvaluator:
    @staticmethod
    def compute_overall_confidence(
        retrieval_score: float,
        grounding_score: float,
        is_off_topic: bool,
        is_safe: bool
    ) -> Dict[str, Any]:
        """
        Combines retrieval relevance, lexical/factual grounding, and safety checks
        into a unified confidence score and reliability status.
        """
        if not is_safe:
            return {
                "confidence_score": 0.0,
                "confidence_level": "REJECTED",
                "is_trustworthy": False,
                "summary": "Request blocked by safety guardrails."
            }

        if is_off_topic:
            return {
                "confidence_score": 0.15,
                "confidence_level": "LOW",
                "is_trustworthy": False,
                "summary": "Query is outside the Gnani.ai knowledge boundary."
            }

        # Weighted calculation: 50% retrieval score + 50% grounding score
        weighted_score = (0.50 * retrieval_score) + (0.50 * grounding_score)
        weighted_score = min(max(weighted_score, 0.0), 1.0)

        if weighted_score >= 0.70:
            level = "HIGH"
            trustworthy = True
            summary = "Answer is strictly grounded in verified Gnani.ai documentation."
        elif weighted_score >= 0.45:
            level = "MODERATE"
            trustworthy = True
            summary = "Answer is partially supported by available context."
        else:
            level = "LOW"
            trustworthy = False
            summary = "Low context overlap detected; hallucination prevention recommended."

        return {
            "confidence_score": round(weighted_score, 2),
            "confidence_level": level,
            "is_trustworthy": trustworthy,
            "summary": summary
        }

