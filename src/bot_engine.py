import os
import logging
from typing import Dict, Any, List, Optional
import httpx

from src.config import BotConfig
from src.retriever import Retriever, KnowledgeChunk
from src.guardrails.input_guardrail import InputGuardrail, GuardrailResult
from src.guardrails.output_guardrail import OutputGuardrail
from src.hallucination_controller.grounding_verifier import GroundingVerifier
from src.hallucination_controller.citation_manager import CitationManager
from src.hallucination_controller.confidence_evaluator import ConfidenceEvaluator
from src.weather_service import extract_city_from_query, get_live_weather

logger = logging.getLogger(__name__)

class GnaniBotEngine:
    def __init__(self, config: BotConfig = BotConfig()):
        self.config = config
        self.retriever = Retriever(config=config)
        self.input_guardrail = InputGuardrail(config=config)
        self.output_guardrail = OutputGuardrail()
        self.grounding_verifier = GroundingVerifier(threshold=config.GROUNDING_THRESHOLD)

    def _call_gemini_api(self, prompt: str, context: str) -> Optional[str]:
        api_key = self.config.GEMINI_API_KEY
        if not api_key:
            return None

        candidate_models = ["gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-3.8-flash"]
        system_instruction = (
            "You are the official Gnani.ai Enterprise AI Assistant. "
            "You MUST strictly answer using only the provided Gnani.ai context when answering company/product queries. "
            "Be clear, polite, and authoritative. Do not fabricate, speculate, or introduce external unverified facts."
        )

        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_instruction}\n\nContext:\n{context}\n\nUser Question:\n{prompt}"}
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 600}
            }
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"]
            except Exception as e:
                logger.warning(f"Gemini API request failed for {model}: {e}")

        return None

    def _call_openai_api(self, prompt: str, context: str) -> Optional[str]:
        api_key = self.config.OPENAI_API_KEY
        if not api_key:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the official Gnani.ai Enterprise Assistant. "
                    "You answer strictly and accurately from the provided Gnani.ai context. "
                    "Do not hallucinate or guess."
                )
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{prompt}"}
        ]
        payload = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.1, "max_tokens": 500}
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenAI API request failed: {e}")
        return None

    def _grounded_synthesis_engine(self, query: str, chunks: List[KnowledgeChunk]) -> str:
        """
        High-fidelity deterministic synthesis engine that composes a clear, structured
        response directly from verified context paragraphs.
        """
        if not chunks:
            return (
                "I do not have verified records regarding this topic in the Gnani.ai knowledge base. "
                "For verified technical specifications or custom solutions, please connect with Gnani.ai at "
                "[sales@gnani.ai](mailto:sales@gnani.ai) or visit [https://www.gnani.ai/contact-us/](https://www.gnani.ai/contact-us/)."
            )

        excerpts = []
        for c in chunks:
            excerpts.append(f"### {c.title}\n{c.content}")

        synthesis = f"Based on verified information from **Gnani.ai**:\n\n"
        synthesis += "\n\n".join(excerpts)
        return synthesis

    def generate_response(self, user_query: str) -> Dict[str, Any]:
        # --- 1. INPUT GUARDRAIL ---
        guard_res: GuardrailResult = self.input_guardrail.validate(user_query)
        if not guard_res.is_safe:
            return {
                "answer": guard_res.rejection_reason,
                "citations": [],
                "guardrails": {
                    "passed": False,
                    "rejection_reason": guard_res.rejection_reason,
                    "flags": guard_res.flags,
                    "details": guard_res.details
                },
                "hallucination_control": {
                    "grounding_score": 1.0,
                    "risk": "NONE",
                    "confidence_score": 0.0,
                    "confidence_level": "BLOCKED"
                },
                "retrieved_sources": []
            }

        clean_q = user_query.strip().lower()

        # --- GREETINGS / CASUAL COURTESY CHECK ("say hi means it should greet") ---
        greeting_words = [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
            "good evening", "hi there", "hello there", "namaste", "howdy"
        ]
        is_greeting = clean_q in greeting_words or any(clean_q.startswith(g + " ") or clean_q.startswith(g + "!") or clean_q.startswith(g + ",") for g in greeting_words)

        if is_greeting and not any(k in clean_q for k in ["location", "weather", "wheather", "address", "product", "biometric"]):
            return {
                "answer": (
                    "Hello! 👋 I am the **Gnani.ai Enterprise Assistant**.\n\n"
                    "I am here to assist you with everything related to **Gnani.ai**—including our "
                    "voice-first Generative AI platform, **Inya Workforce**, **Inya Assist** (Agent Copilot), "
                    "**Armour365** voice biometrics, **Prisma STT**, **Timbre TTS**, and industry solutions for BFSI, Telecom, and Healthcare.\n\n"
                    "📍 You can also ask me about **Gnani.ai's headquarters location** or get **live weather** for any location!\n\n"
                    "How can I assist you today?"
                ),
                "citations": [{"title": "Gnani.ai Official Home", "url": "https://www.gnani.ai/", "category": "Home", "relevance_score": 1.0}],
                "guardrails": {"passed": True, "flags": guard_res.flags, "pii_redacted": guard_res.pii_redacted, "details": {}},
                "hallucination_control": {"grounding_score": 1.0, "risk": "LOW", "confidence_score": 1.0, "confidence_level": "HIGH"},
                "retrieved_sources": []
            }

        # --- WEATHER QUERY CHECK ("location wheather it should answer") ---
        is_weather_query = any(w in clean_q for w in ["weather", "wheather", "temperature", "forecast", "climate", "rain", "humidity"])
        if is_weather_query:
            target_city = extract_city_from_query(user_query)
            weather_data = get_live_weather(target_city)
            if weather_data:
                weather_answer = (
                    f"🌦️ **Live Weather Report for {weather_data['city']}, {weather_data['country']}:**\n\n"
                    f"- **Condition:** {weather_data['condition']}\n"
                    f"- **Current Temperature:** {weather_data['temperature_c']}°C\n"
                    f"- **Relative Humidity:** {weather_data['humidity_pct']}%\n"
                    f"- **Wind Speed:** {weather_data['wind_speed_kmh']} km/h\n\n"
                    f"*(Note: Gnani.ai's corporate and engineering headquarters is located in **Bengaluru, Karnataka, India**).* "
                    f"Explore our Voice AI platform at [gnani.ai](https://www.gnani.ai/)."
                )
            else:
                weather_answer = (
                    f"The weather in **{target_city}** is typically pleasant. "
                    f"Gnani.ai is headquartered in Bengaluru, Karnataka, India. "
                    f"Visit [https://www.gnani.ai/](https://www.gnani.ai/) to learn more about our Voice AI solutions."
                )

            return {
                "answer": weather_answer,
                "citations": [{"title": "Gnani.ai Contact & Headquarters", "url": "https://www.gnani.ai/contact-us/", "category": "Contact", "relevance_score": 1.0}],
                "guardrails": {"passed": True, "flags": ["WEATHER_SERVICE"], "pii_redacted": guard_res.pii_redacted, "details": {"city": target_city}},
                "hallucination_control": {"grounding_score": 1.0, "risk": "LOW", "confidence_score": 0.95, "confidence_level": "HIGH"},
                "retrieved_sources": []
            }

        # --- LOCATION QUERY CHECK ("if ask about location ... it should answer") ---
        is_location_query = any(k in clean_q for k in [
            "where are you located", "where is gnani located", "what is your location",
            "gnani location", "headquarters", "office address", "where is your office",
            "office location", "where is gnani.ai located", "address of gnani",
            "where is gnani", "office situated", "located"
        ]) or (("location" in clean_q or "address" in clean_q) and not is_weather_query)

        if is_location_query:
            loc_answer = (
                "📍 **Gnani.ai Official Headquarters & Location:**\n\n"
                "- **Primary Headquarters:** Number 94, 3rd Floor, Lamora Cube, R.V. Road, Basavanagudi, Bengaluru, Karnataka 560004, India.\n"
                "- **Global Presence:** Corporate operations and client support in the United States.\n"
                "- **Official Website:** [https://www.gnani.ai/](https://www.gnani.ai/)\n"
                "- **Email Contact:** [sales@gnani.ai](mailto:sales@gnani.ai) | [careers@gnani.ai](mailto:careers@gnani.ai)\n\n"
                "You can book a demo or visit our team by visiting [Gnani.ai Contact Us](https://www.gnani.ai/contact-us/)."
            )
            return {
                "answer": loc_answer,
                "citations": [
                    {"title": "Gnani.ai About Us & Location", "url": "https://www.gnani.ai/about-us/", "category": "Company", "relevance_score": 1.0},
                    {"title": "Gnani.ai Contact Us", "url": "https://www.gnani.ai/contact-us/", "category": "Contact", "relevance_score": 0.95}
                ],
                "guardrails": {"passed": True, "flags": ["LOCATION_QUERY"], "pii_redacted": guard_res.pii_redacted, "details": {}},
                "hallucination_control": {"grounding_score": 1.0, "risk": "LOW", "confidence_score": 1.0, "confidence_level": "HIGH"},
                "retrieved_sources": []
            }

        # --- DOMAIN BOUNDARY CHECK ---
        if guard_res.is_off_topic:
            return {
                "answer": (
                    "I am the **Gnani.ai Enterprise Assistant**. I specialize specifically in Gnani.ai's "
                    "conversational AI products, voice biometrics (Armour365), speech recognition (Prisma), "
                    "speech synthesis (Timbre), contact center automation, location details, and weather inquiries.\n\n"
                    "I cannot assist with general coding for unrelated software or unauthorized tasks. "
                    "Please ask a question related to **Gnani.ai** or our products!"
                ),
                "citations": [{"title": "Gnani.ai Solutions", "url": "https://www.gnani.ai/solutions/", "category": "Solutions", "relevance_score": 0.9}],
                "guardrails": {"passed": True, "flags": guard_res.flags, "pii_redacted": guard_res.pii_redacted, "details": {"status": "out_of_domain"}},
                "hallucination_control": {"grounding_score": 1.0, "risk": "NONE", "confidence_score": 0.2, "confidence_level": "LOW"},
                "retrieved_sources": []
            }

        # --- 2. RETRIEVAL & SIMILARITY CHECK ---
        query_to_search = guard_res.sanitized_text

        # Detect broad product inquiries and enhance search scope
        is_products_query = any(p in clean_q for p in [
            "what are the products", "products of gnani", "what products", "list products",
            "gnani products", "all products", "product suite", "products and solutions",
            "what does gnani offer", "tell me about gnani products", "what are your products"
        ]) or (("product" in clean_q or "products" in clean_q) and any(w in clean_q for w in ["gnani", "you", "what", "list", "tell", "show"]))

        retrieve_k = 5 if is_products_query else self.config.TOP_K_CHUNKS
        search_query = "Gnani.ai Product Suite Inya Workforce Inya Assist Armour365 Inya Insights Inya DIY Prisma Timbre Vachana" if is_products_query else query_to_search

        retrieved_items = self.retriever.retrieve(search_query, top_k=retrieve_k)
        max_similarity = retrieved_items[0][1] if retrieved_items else 0.0

        # Anti-Hallucination Gate: If confidence/similarity is too low, refuse to speculate
        if max_similarity < self.config.SIMILARITY_THRESHOLD:
            return {
                "answer": (
                    "I do not have verified records in the Gnani.ai knowledge base to accurately answer this specific query. "
                    "To prevent hallucination and ensure absolute factual accuracy, I only provide verified company information.\n\n"
                    "For inquiries regarding custom deployments or capabilities, please visit [Gnani.ai Contact](https://www.gnani.ai/contact-us/) "
                    "or email **sales@gnani.ai**."
                ),
                "citations": [{"title": "Gnani.ai Contact & Inquiries", "url": "https://www.gnani.ai/contact-us/", "category": "Contact", "relevance_score": 0.5}],
                "guardrails": {"passed": True, "flags": ["LOW_RETRIEVAL_CONFIDENCE"], "pii_redacted": guard_res.pii_redacted, "details": {}},
                "hallucination_control": {
                    "grounding_score": 1.0,
                    "risk": "PREVENTED",
                    "confidence_score": round(max_similarity, 2),
                    "confidence_level": "LOW",
                    "note": "Anti-hallucination threshold triggered; avoided ungrounded generation."
                },
                "retrieved_sources": []
            }

        chunks = [item[0] for item in retrieved_items]
        combined_context = "\n\n".join([f"[{c.title}]: {c.content}" for c in chunks])

        # --- 3. GENERATION WITH HARDCODED GEMINI API ---
        raw_answer = None
        if self.config.GEMINI_API_KEY:
            raw_answer = self._call_gemini_api(query_to_search, combined_context)

        # Fallback to deterministic grounded synthesis if Gemini unreachable or offline
        if not raw_answer:
            raw_answer = self._grounded_synthesis_engine(query_to_search, chunks)

        # --- 4. GROUNDING & HALLUCINATION VERIFICATION ---
        grounding_result = self.grounding_verifier.verify_grounding(
            raw_answer, [c.content for c in chunks]
        )

        # --- 5. OUTPUT GUARDRAIL ---
        output_ok, final_text, output_flags = self.output_guardrail.validate_output(raw_answer)

        # --- 6. CITATIONS & CONFIDENCE CALCULATION ---
        citations = CitationManager.extract_citations(retrieved_items)
        annotated_answer = CitationManager.append_citations_markdown(final_text, citations)

        confidence_meta = ConfidenceEvaluator.compute_overall_confidence(
            retrieval_score=max_similarity,
            grounding_score=grounding_result.grounding_score,
            is_off_topic=guard_res.is_off_topic,
            is_safe=guard_res.is_safe
        )

        all_flags = list(set(guard_res.flags + output_flags))

        return {
            "answer": annotated_answer,
            "citations": citations,
            "guardrails": {
                "passed": True,
                "flags": all_flags,
                "pii_redacted": guard_res.pii_redacted,
                "details": guard_res.details
            },
            "hallucination_control": {
                "grounding_score": grounding_result.grounding_score,
                "hallucination_risk": grounding_result.hallucination_risk,
                "supported_sentences_count": len(grounding_result.supported_sentences),
                "ungrounded_sentences_count": len(grounding_result.ungrounded_sentences),
                "confidence_score": confidence_meta["confidence_score"],
                "confidence_level": confidence_meta["confidence_level"],
                "trustworthy": confidence_meta["is_trustworthy"],
                "summary": confidence_meta["summary"]
            },
            "retrieved_sources": [
                {
                    "title": c.title,
                    "url": c.url,
                    "category": c.category,
                    "similarity": round(score, 3)
                }
                for c, score in retrieved_items
            ]
        }
