import asyncio
import time
import feedparser
from datetime import datetime, timedelta
from app.services import cache


async def _fetch_google_news(ticker: str) -> list[dict]:
    """Shared helper: Google News RSS for ticker → [{title, period}], cached 2h.

    All three public fetch functions hit this feed; caching it avoids three
    separate feedparser.parse() calls for the same ticker in one analysis run.
    """
    cache_key = f"company:{ticker}:google_news_raw"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"https://news.google.com/rss/search?q={ticker}"

    def _fetch():
        items = []
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:10]:
                title = (entry.title or "").strip()
                if not title:
                    continue
                period = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    period = dt.strftime("%Y-%m-%d")
                items.append({"title": title, "period": period})
        except Exception:
            pass
        return items

    items = await asyncio.to_thread(_fetch)
    cache.set(cache_key, items, ttl_seconds=7200)
    return items


async def fetch_news_sentiment(company_name: str, ticker: str) -> float:
    cache_key = f"company:{ticker}:news"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    google_items = await _fetch_google_news(ticker)

    extra_feeds = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}",
        "https://feeds.reuters.com/reuters/businessNews",
    ]

    def _fetch_extra():
        headlines = []
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        for url in extra_feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:10]:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        if dt < thirty_days_ago:
                            continue
                    headlines.append(entry.title.lower())
            except Exception:
                continue
        return headlines

    extra_headlines = await asyncio.to_thread(_fetch_extra)
    headlines = [item["title"].lower() for item in google_items] + extra_headlines

    if not headlines:
        return 50.0

    positive_words = {"profit", "growth", "beat", "strong", "record", "raised", "upgraded"}
    negative_words = {"fraud", "loss", "miss", "decline", "investigation", "sec", "resigned",
                      "lawsuit", "warning", "downgrade", "restatement", "concern"}

    scores = []
    for h in headlines[:20]:
        score = 0
        words = set(h.replace(",", "").replace(".", "").split())
        for w in words:
            if w in positive_words:
                score += 1
            if w in negative_words:
                score -= 1
        scores.append(score)

    if not scores:
        return 50.0

    raw_avg = sum(scores) / len(scores)
    raw_avg = max(-1.0, min(1.0, raw_avg))
    final_score = ((raw_avg + 1) / 2) * 100

    cache.set(cache_key, final_score, ttl_seconds=7200)
    return final_score


async def fetch_news_statements(company_name: str, ticker: str, limit: int = 5) -> list[dict]:
    cache_key = f"company:{ticker}:news_statements"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    raw_items = (await _fetch_google_news(ticker))[:limit]

    statements = []
    for idx, item in enumerate(raw_items):
        period = item["period"] or f"item-{idx + 1:02d}"
        statements.append({"period": period, "text": item["title"], "source": "News"})

    cache.set(cache_key, statements, ttl_seconds=7200)
    return statements


async def fetch_news_text(company_name: str, ticker: str) -> str:
    raw_items = await _fetch_google_news(ticker)
    return "\n".join(item["title"] for item in raw_items)
