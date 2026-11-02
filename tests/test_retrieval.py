from src.retriever import Retriever
from src.config import BotConfig

def test_retriever_biometrics():
    retriever = Retriever(BotConfig())
    results = retriever.retrieve("Tell me about Armour365 voice biometrics authentication", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "armour" in top_chunk.title.lower() or "shield" in top_chunk.title.lower() or "biometrics" in top_chunk.content.lower()
    assert score > 0.3

def test_retriever_speech_to_text():
    retriever = Retriever(BotConfig())
    results = retriever.retrieve("How does Prisma speech recognition STT work in Indic languages?", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "prisma" in top_chunk.content.lower() or "speech" in top_chunk.content.lower()
    assert score > 0.3

def test_retriever_leadership():
    retriever = Retriever(BotConfig())
    results = retriever.retrieve("Who is the CEO and founder Ganesh Gopalan?", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "ganesh gopalan" in top_chunk.content.lower() or "leadership" in top_chunk.title.lower()

if __name__ == "__main__":
    test_retriever_biometrics()
    test_retriever_speech_to_text()
    test_retriever_leadership()
    print("All Retrieval tests passed successfully!")

