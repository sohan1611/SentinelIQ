import asyncio
import logging
import time
import feedparser
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.services import cache

logger = logging.getLogger(__name__)

NEWS_FETCH_TIMEOUT_SECONDS = 15.0

# VADER gives negation-, intensifier-, and punctuation-aware sentiment, unlike
# the previous flat keyword bag which scored "profit warning" as neutral and
# "no fraud" as negative (it just counted +1/-1 per matching word, blind to
# word order and negation). VADER is rule-based and fully deterministic --
# preserving ADR-004's "determinism for judgment" -- and ships its own
# lexicon, so scoring stays offline and $0.
_analyzer = SentimentIntensityAnalyzer()

# Finance-domain valence overrides (VADER scale, roughly -4..+4). VADER is
# tuned on general/social English, where "beat"/"miss" carry the wrong sign for
# earnings and terms like "restatement"/"downgrade" are unknown (scored 0).
# These corrections make the news signal reflect financial meaning; VADER still
# layers its own negation handling on top, so e.g. "no restatement" is handled.
_FINANCE_LEXICON = {
    # positive in a financial context
    "beat": 1.9, "beats": 1.9, "outperform": 1.9, "outperforms": 1.9,
    "upgrade": 1.7, "upgraded": 1.7, "buyback": 1.2, "accretive": 1.5,
    "profit": 1.4, "surge": 1.6, "surges": 1.6, "rally": 1.3,
    # negative in a financial context
    "miss": -1.6, "misses": -1.6, "missed": -1.6,
    "downgrade": -1.9, "downgraded": -1.9,
    "restatement": -2.6, "restate": -2.4, "restated": -2.4,
    "probe": -1.9, "subpoena": -2.4, "investigation": -2.0,
    "lawsuit": -1.9, "litigation": -1.6,
    "resign": -1.3, "resigned": -1.3, "resignation": -1.3,
    "delisting": -2.5, "delisted": -2.5, "bankruptcy": -3.0,
    "default": -1.9, "impairment": -1.6, "writedown": -1.8,
    "misconduct": -2.6, "warning": -1.5,
    "plunge": -2.0, "plunges": -2.0, "slump": -1.7, "halted": -1.8,
}
_analyzer.lexicon.update(_FINANCE_LEXICON)


def _score_headlines(headlines: list[str]) -> float:
    """Map a list of headlines to a 0-100 news-sentiment score.

    Each headline's VADER ``compound`` score (in [-1, 1], negation- and
    intensifier-aware) is averaged, then linearly mapped to [0, 100] where 50
    is neutral. Pure/offline/deterministic (no I/O), so it is unit-testable
    without touching the network. At most the first 20 headlines are used, and
    empty/blank input returns 50.0 (neutral) -- matching the prior fallback.
    """
    usable = [h for h in headlines[:20] if h and h.strip()]
    if not usable:
        return 50.0
    compounds = [_analyzer.polarity_scores(h)["compound"] for h in usable]
    avg = sum(compounds) / len(compounds)
    avg = max(-1.0, min(1.0, avg))
    return ((avg + 1.0) / 2.0) * 100.0


async def _fetch_google_news(company_name: str, ticker: str) -> list[dict]:
    """Shared helper: Google News RSS for company_name+ticker → [{title, period}], cached 2h.

    All three public fetch functions hit this feed; caching it avoids three
    separate feedparser.parse() calls for the same ticker in one analysis run.

    Querying on company_name OR ticker (not the bare ticker alone) avoids
    pulling unrelated stories for short/word-like tickers (e.g. F, ALL, ON,
    KEY) that otherwise match many unconnected headlines -- a governance flag
    "grounded" in an unrelated headline would get attributed to the wrong
    company (Phase 39 / C-1 hardening).
    """
    cache_key = f"company:{ticker}:google_news_raw"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    query = quote(f'"{company_name}" OR {ticker}')
    url = f"https://news.google.com/rss/search?q={query}"

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

    try:
        items = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=NEWS_FETCH_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.warning(f"Google News fetch timed out for {ticker}")
        items = []
    cache.set(cache_key, items, ttl_seconds=7200)
    return items


async def fetch_news_sentiment(company_name: str, ticker: str) -> float:
    cache_key = f"company:{ticker}:news"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    google_items = await _fetch_google_news(company_name, ticker)

    extra_feeds = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}",
        "https://feeds.reuters.com/reuters/businessNews",
    ]

    def _fetch_extra():
        headlines = []
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
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

    try:
        extra_headlines = await asyncio.wait_for(
            asyncio.to_thread(_fetch_extra), timeout=NEWS_FETCH_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        extra_headlines = []
    headlines = [item["title"].lower() for item in google_items] + extra_headlines

    if not headlines:
        return 50.0

    final_score = _score_headlines(headlines)

    cache.set(cache_key, final_score, ttl_seconds=7200)
    return final_score


async def fetch_news_statements(company_name: str, ticker: str, limit: int = 5) -> list[dict]:
    cache_key = f"company:{ticker}:news_statements"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    raw_items = (await _fetch_google_news(company_name, ticker))[:limit]

    statements = []
    for idx, item in enumerate(raw_items):
        period = item["period"] or f"item-{idx + 1:02d}"
        statements.append({"period": period, "text": item["title"], "source": "News"})

    cache.set(cache_key, statements, ttl_seconds=7200)
    return statements


async def fetch_news_text(company_name: str, ticker: str) -> str:
    raw_items = await _fetch_google_news(company_name, ticker)
    return "\n".join(item["title"] for item in raw_items)
