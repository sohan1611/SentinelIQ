import asyncio
import time
import feedparser
from datetime import datetime, timedelta
from app.services import cache

async def fetch_news_sentiment(company_name: str, ticker: str) -> float:
    cache_key = f"company:{ticker}:news"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    feeds = [
        f"https://news.google.com/rss/search?q={ticker}",
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}",
        "https://feeds.reuters.com/reuters/businessNews"
    ]

    def _fetch():
        headlines = []
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        for url in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:10]: # limit to 10 per feed to avoid huge lists
                    # Very rough date parsing, feedparser does provide time structs
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        if dt < thirty_days_ago:
                            continue
                    
                    headlines.append(entry.title.lower())
            except Exception:
                continue
                
        return headlines

    import time
    headlines = await asyncio.to_thread(_fetch)
    
    if not headlines:
        return 50.0 # Neutral fallback if no news found or all fail
        
    positive_words = {"profit", "growth", "beat", "strong", "record", "raised", "upgraded"}
    negative_words = {"fraud", "loss", "miss", "decline", "investigation", "sec", "resigned", "lawsuit", "warning", "downgrade", "restatement", "concern"}
    
    scores = []
    for h in headlines[:20]: # limit to 20 recent
        score = 0
        words = set(h.replace(',', '').replace('.', '').split())
        for w in words:
            if w in positive_words:
                score += 1
            if w in negative_words:
                score -= 1
        scores.append(score)
    
    if not scores:
        return 50.0
        
    raw_avg = sum(scores) / len(scores)
    # clamp raw_avg to [-1, 1]
    raw_avg = max(-1.0, min(1.0, raw_avg))
    
    # map to 0-100
    final_score = ((raw_avg + 1) / 2) * 100
    
    cache.set(cache_key, final_score, ttl_seconds=7200) # 2 hours
    return final_score

async def fetch_news_statements(company_name: str, ticker: str, limit: int = 5) -> list[dict]:
    # Returns recent headlines as {"period", "text", "source"} dicts — same shape
    # ConsistencyEngine.analyze already expects, used as real narrative input.
    cache_key = f"company:{ticker}:news_statements"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    feeds = [f"https://news.google.com/rss/search?q={ticker}"]

    def _fetch():
        items = []
        for url in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:limit]:
                    title = entry.title.strip()
                    if not title:
                        continue
                    period = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        period = dt.strftime("%Y-%m-%d")
                    items.append({"title": title, "period": period})
            except Exception:
                continue
        return items

    raw_items = await asyncio.to_thread(_fetch)

    statements = []
    for idx, item in enumerate(raw_items):
        period = item["period"] or f"item-{idx + 1:02d}"
        statements.append({"period": period, "text": item["title"], "source": "News"})

    cache.set(cache_key, statements, ttl_seconds=7200)  # 2h, matches news TTL
    return statements


async def fetch_news_text(company_name: str, ticker: str) -> str:
    # Used for governance & narrative prompts to have raw text
    feeds = [
        f"https://news.google.com/rss/search?q={ticker}"
    ]
    def _fetch():
        headlines = []
        for url in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:10]:
                    headlines.append(entry.title)
            except Exception:
                continue
        return "\n".join(headlines)

    return await asyncio.to_thread(_fetch)
