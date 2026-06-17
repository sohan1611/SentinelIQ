import asyncio
import yfinance as yf
from fastapi import HTTPException
from app.services import cache

# curl_cffi impersonates Chrome at the TLS layer (JA3/JA4 fingerprint), which is
# what Yahoo Finance's Cloudflare protection checks. A plain requests.Session with
# browser headers is not enough — the TLS fingerprint still identifies python-requests.
try:
    from curl_cffi import requests as _cffi_requests
    _YF_SESSION = _cffi_requests.Session(impersonate="chrome120")
except ImportError:
    import requests as _requests
    _YF_SESSION = _requests.Session()
    _YF_SESSION.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    })


def _ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol, session=_YF_SESSION)


async def fetch_company_info(ticker: str) -> dict:
    cache_key = f"company:{ticker}:info"
    cached = cache.get(cache_key)
    if cached:
        return cached

    def _fetch():
        t = _ticker(ticker)
        info = t.info
        if not info or 'longName' not in info:
            raise HTTPException(status_code=404, detail="No financial data available for this ticker.")
        return {
            "longName": info.get("longName"),
            "sector": info.get("sector"),
            "exchange": info.get("exchange"),
            "marketCap": info.get("marketCap")
        }

    data = await asyncio.to_thread(_fetch)
    cache.set(cache_key, data, ttl_seconds=86400)
    return data


async def fetch_financials(ticker: str) -> list[dict]:
    cache_key = f"company:{ticker}:financials"
    cached = cache.get(cache_key)
    if cached:
        return cached

    def _fetch():
        import pandas as pd
        t = _ticker(ticker)
        try:
            inc = t.financials
            bs = t.balance_sheet
            cf = t.cashflow

            if inc.empty and bs.empty and cf.empty:
                raise HTTPException(status_code=404, detail="No financial data available for this ticker.")

            periods = set()
            for df in [inc, bs, cf]:
                periods.update(df.columns)

            periods = sorted(list(periods), reverse=True)
            results = []

            for p in periods:
                period_str = str(p.year)

                def get_val(df, row_names):
                    for r in row_names:
                        if r in df.index:
                            val = df.loc[r, p]
                            if not pd.isna(val):
                                return float(val)
                    return None

                rev = get_val(inc, ["Total Revenue", "Operating Revenue"])
                net_inc = get_val(inc, ["Net Income", "Net Income Common Stockholders"])
                ocf = get_val(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"])
                fcf = get_val(cf, ["Free Cash Flow"])
                debt = get_val(bs, ["Total Debt"])
                assets = get_val(bs, ["Total Assets"])
                recv = get_val(bs, ["Accounts Receivable", "Net Receivables"])

                gm = None
                if rev and get_val(inc, ["Gross Profit"]):
                    gm = get_val(inc, ["Gross Profit"]) / rev

                results.append({
                    "period": period_str,
                    "period_type": "annual",
                    "revenue": rev,
                    "net_income": net_inc,
                    "operating_cf": ocf,
                    "free_cf": fcf,
                    "total_debt": debt,
                    "total_assets": assets,
                    "accounts_recv": recv,
                    "gross_margin": gm
                })

            return results
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=404, detail="No financial data available for this ticker.")

    data = await asyncio.to_thread(_fetch)
    cache.set(cache_key, data, ttl_seconds=43200)
    return data
