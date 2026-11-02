from typing import List, Dict, Any
from src.retriever import KnowledgeChunk

class CitationManager:
    @staticmethod
    def extract_citations(chunks_with_scores: List[tuple]) -> List[Dict[str, Any]]:
        """
        Deduplicates and formats citations from retrieved chunks.
        """
        seen_urls = set()
        citations = []

        for item in chunks_with_scores:
            chunk: KnowledgeChunk = item[0] if isinstance(item, (tuple, list)) else item
            score: float = item[1] if isinstance(item, (tuple, list)) and len(item) > 1 else 1.0

            if chunk.url not in seen_urls:
                seen_urls.add(chunk.url)
                citations.append({
                    "id": chunk.doc_id,
                    "title": chunk.title,
                    "url": chunk.url,
                    "category": chunk.category,
                    "relevance_score": round(score, 3)
                })

        return citations

    @staticmethod
    def append_citations_markdown(text: str, citations: List[Dict[str, Any]]) -> str:
        """
        Appends clean markdown citations to the end of a response.
        """
        if not citations:
            return text

        citation_lines = ["\n\n**Verified Sources & Links:**"]
        for c in citations:
            citation_lines.append(f"- [{c['title']}]({c['url']}) *(Relevance: {int(c['relevance_score'] * 100)}%)*")

        return text + "\n".join(citation_lines)

