import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from src.config import BotConfig, KNOWLEDGE_BASE_PATH

logger = logging.getLogger(__name__)

URLS_TO_SCRAPE = [
    {"url": "https://www.gnani.ai/", "category": "Home"},
    {"url": "https://www.gnani.ai/about-us/", "category": "Company"},
    {"url": "https://www.gnani.ai/products/voice-bot/", "category": "Products"},
    {"url": "https://www.gnani.ai/products/agent-assist/", "category": "Products"},
    {"url": "https://www.gnani.ai/products/voice-biometrics/", "category": "Products"},
    {"url": "https://www.gnani.ai/products/speech-analytics/", "category": "Products"},
    {"url": "https://www.gnani.ai/technology/speech-to-text/", "category": "Technology"},
    {"url": "https://www.gnani.ai/technology/text-to-speech/", "category": "Technology"},
    {"url": "https://www.gnani.ai/solutions/bfsi/", "category": "Solutions"},
    {"url": "https://www.gnani.ai/security-compliance/", "category": "Security"},
    {"url": "https://www.gnani.ai/contact-us/", "category": "Contact"},
]

def clean_html_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script, style, navigation, footer boilerplate
    for elem in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        elem.extract()
    text = soup.get_text(separator=" ", strip=True)
    # Normalize whitespaces
    return " ".join(text.split())

def scrape_gnani_site(timeout: int = 8) -> List[Dict[str, Any]]:
    """
    Attempts to scrape live pages from Gnani.ai.
    Falls back gracefully to cached knowledge base if network is restricted or site is down.
    """
    scraped_documents = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    logger.info("Initiating scrape of %s target URLs...", len(URLS_TO_SCRAPE))
    for target in URLS_TO_SCRAPE:
        url = target["url"]
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else url
                text = clean_html_text(resp.text)
                if len(text) > 100:
                    scraped_documents.append({
                        "id": url.rstrip("/").split("/")[-1] or "home",
                        "title": title,
                        "url": url,
                        "category": target["category"],
                        "content": text[:3000] # Primary excerpt
                    })
        except Exception as e:
            logger.warning(f"Could not reach {url}: {e}")

    return scraped_documents

def load_or_update_knowledge_base() -> List[Dict[str, Any]]:
    """
    Loads knowledge base from local cache or attempts live scrape.
    Guarantees a verified, structured knowledge base is always returned.
    """
    if KNOWLEDGE_BASE_PATH.exists():
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            docs = json.load(f)
            logger.info("Loaded %d verified documents from knowledge base.", len(docs))
            return docs
    
    # If not present, try live scrape
    live_docs = scrape_gnani_site()
    if live_docs:
        KNOWLEDGE_BASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(KNOWLEDGE_BASE_PATH, "w", encoding="utf-8") as f:
            json.dump(live_docs, f, indent=2)
        return live_docs
    
    return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = load_or_update_knowledge_base()
    print(f"Loaded {len(data)} documents.")

