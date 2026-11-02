from src.hallucination_controller.grounding_verifier import GroundingVerifier
from src.bot_engine import GnaniBotEngine
from src.config import BotConfig

def test_grounding_verifier_high_grounding():
    verifier = GroundingVerifier()
    context = [
        "Inya Shield Armour365 is Gnani.ai's voice biometrics platform that authenticates customers securely.",
        "It extracts over 300 physiological and behavioral voice acoustic parameters within 3 to 5 seconds."
    ]
    grounded_answer = "Armour365 is a voice biometrics platform that authenticates customers securely using 300 voice acoustic parameters."
    res = verifier.verify_grounding(grounded_answer, context)
    assert res.grounding_score >= 0.70
    assert res.hallucination_risk == "LOW"

def test_grounding_verifier_detects_hallucination():
    verifier = GroundingVerifier()
    context = [
        "Gnani.ai is an enterprise conversational AI company based in Bengaluru."
    ]
    hallucinated_answer = "Gnani.ai was founded in Tokyo and recently acquired by a space exploration agency for quantum computing satellites."
    res = verifier.verify_grounding(hallucinated_answer, context)
    assert res.grounding_score < 0.50
    assert res.hallucination_risk == "HIGH"

def test_anti_hallucination_gate_on_unsupported_queries():
    engine = GnaniBotEngine(BotConfig())
    # Query something completely fabricated not in Gnani's documentation
    unknown_query = "What is the stock price prediction and quarterly dividend payout of Gnani.ai crypto coin?"
    response = engine.generate_response(unknown_query)
    # The engine should refuse to hallucinate
    assert "knowledge base" in response["answer"].lower() or "not have verified" in response["answer"].lower()
    assert response["hallucination_control"]["risk"] in ["PREVENTED", "NONE", "LOW"]

if __name__ == "__main__":
    test_grounding_verifier_high_grounding()
    test_grounding_verifier_detects_hallucination()
    test_anti_hallucination_gate_on_unsupported_queries()
    print("All Hallucination tests passed successfully!")

