import re
import json
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import BotConfig, KNOWLEDGE_BASE_PATH

class KnowledgeChunk:
    def __init__(self, doc_id: str, title: str, url: str, category: str, content: str):
        self.doc_id = doc_id
        self.title = title
        self.url = url
        self.category = category
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.doc_id,
            "title": self.title,
            "url": self.url,
            "category": self.category,
            "content": self.content
        }

class Retriever:
    def __init__(self, config: BotConfig = BotConfig()):
        self.config = config
        self.chunks: List[KnowledgeChunk] = []
        self.vectorizer: TfidfVectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english"
        )
        self.tfidf_matrix = None
        self._load_and_index()

    def _load_and_index(self):
        if not KNOWLEDGE_BASE_PATH.exists():
            raise FileNotFoundError(f"Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")

        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            raw_docs = json.load(f)

        self.chunks = []
        corpus = []
        for doc in raw_docs:
            chunk = KnowledgeChunk(
                doc_id=doc.get("id", ""),
                title=doc.get("title", ""),
                url=doc.get("url", self.config.TARGET_URL),
                category=doc.get("category", "General"),
                content=doc.get("content", "")
            )
            self.chunks.append(chunk)
            # Combine title, category, and content for rich vector indexing
            indexed_text = f"{chunk.title} {chunk.category} {chunk.content}"
            corpus.append(indexed_text)

        if corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Retrieves the top-k most relevant chunks using hybrid cosine similarity
        and keyword-exact match weighting.
        """
        if not self.chunks or self.tfidf_matrix is None:
            return []

        # Vector cosine similarity
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        # Apply keyword boosting for specific product names and entities
        boosted_scores = np.copy(similarities)
        query_lower = query.lower()

        for idx, chunk in enumerate(self.chunks):
            # Keyword matching bonus
            chunk_text_lower = f"{chunk.title.lower()} {chunk.content.lower()}"
            keywords_to_check = [
                "armour365", "armour", "shield", "assist365", "inya",
                "prisma", "timbre", "vachana", "biometrics", "voice bot",
                "ganesh", "ananth", "bfsi", "telecom", "bengaluru",
                "quality assurance", "aura365", "wer", "speech-to-text",
                "text-to-speech", "soc 2", "iso 27001", "hipaa",
                "products", "product", "solutions", "offerings", "platform", "suite"
            ]
            for kw in keywords_to_check:
                if kw in query_lower and kw in chunk_text_lower:
                    boosted_scores[idx] += 0.25

            # If user asks about products, prioritize the master product suite and product categories
            if any(p in query_lower for p in ["product", "products", "offerings", "solutions"]):
                if chunk.doc_id == "gnani-all-products":
                    boosted_scores[idx] += 0.40
                elif chunk.category == "Products":
                    boosted_scores[idx] += 0.20

        # Normalize score upper bound to 1.0
        boosted_scores = np.clip(boosted_scores, 0.0, 1.0)

        # Rank indices
        top_indices = np.argsort(boosted_scores)[::-1][:top_k]
        results = []
        for i in top_indices:
            results.append((self.chunks[i], float(boosted_scores[i])))

        return results

    def get_max_similarity(self, query: str) -> float:
        results = self.retrieve(query, top_k=1)
        if results:
            return results[0][1]
        return 0.0

