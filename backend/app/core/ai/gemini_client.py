import json
import asyncio
import random
import logging
from typing import TypedDict

from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ID = "gemini-2.0-flash"
client = genai.Client(api_key=settings.GEMINI_API_KEY)

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2.0


class GenerationResult(TypedDict):
    text: str | None
    prompt: str
    model_id: str
    raw_response: dict | None


def _extract_provenance_fields(response) -> dict:
    """Extract audit fields from a raw Gemini response object.

    Captures finish_reason, safety_ratings, and token counts — the fields
    an audit needs when a score looks wrong (M-1).  Defensive: any attribute
    miss or enum type mismatch returns an empty dict rather than raising.
    """
    try:
        candidates = getattr(response, "candidates", None) or []
        candidate = candidates[0] if candidates else None

        finish_reason = None
        safety_ratings = []
        if candidate is not None:
            fr = getattr(candidate, "finish_reason", None)
            finish_reason = fr.name if hasattr(fr, "name") else (str(fr) if fr is not None else None)
            for r in getattr(candidate, "safety_ratings", []) or []:
                cat = getattr(r, "category", None)
                prob = getattr(r, "probability", None)
                safety_ratings.append({
                    "category": cat.name if hasattr(cat, "name") else str(cat),
                    "probability": prob.name if hasattr(prob, "name") else str(prob),
                })

        usage = getattr(response, "usage_metadata", None)
        return {
            "finish_reason": finish_reason,
            "safety_ratings": safety_ratings,
            "prompt_token_count": getattr(usage, "prompt_token_count", None) if usage else None,
            "candidates_token_count": getattr(usage, "candidates_token_count", None) if usage else None,
        }
    except Exception:
        return {}


def _build_config(temperature: float | None) -> types.GenerateContentConfig | None:
    if temperature is None:
        return None
    return types.GenerateContentConfig(temperature=temperature)


async def _call_with_backoff(coro_fn):
    """coro_fn: async callable that takes no args and returns the response."""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_fn()
        except Exception as e:
            last_exc = e
            is_429 = (
                "429" in str(e)
                or "ResourceExhausted" in type(e).__name__
                or "quota" in str(e).lower()
            )
            if not is_429 or attempt == MAX_RETRIES - 1:
                raise
            delay = BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 0.5)
            logger.warning(
                f"Gemini rate-limited, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
            )
            await asyncio.sleep(delay)
    raise last_exc


async def generate_content(prompt: str, temperature: float | None = None) -> str | None:
    config = _build_config(temperature)

    async def _call():
        kwargs = {"model": DEFAULT_MODEL_ID, "contents": prompt}
        if config is not None:
            kwargs["config"] = config
        return await client.aio.models.generate_content(**kwargs)

    try:
        response = await _call_with_backoff(_call)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


async def generate_content_with_provenance(prompt: str, temperature: float = 0.0) -> GenerationResult:
    config = _build_config(temperature)

    async def _call():
        return await client.aio.models.generate_content(
            model=DEFAULT_MODEL_ID, contents=prompt, config=config
        )

    try:
        response = await _call_with_backoff(_call)
        text = response.text
        raw_response = _extract_provenance_fields(response)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        text = None
        raw_response = None

    return {
        "text": text,
        "prompt": prompt,
        "model_id": DEFAULT_MODEL_ID,
        "raw_response": raw_response,
    }


def _parse_json(text: str | None) -> dict | list | None:
    if not text:
        return None
    try:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Gemini JSON decode error: {e}\nRaw text: {text}")
        return None


async def generate_json(prompt: str, temperature: float = 0.0) -> dict | list | None:
    text = await generate_content(prompt, temperature=temperature)
    return _parse_json(text)


async def generate_json_with_provenance(
    prompt: str, temperature: float = 0.0
) -> tuple[dict | list | None, GenerationResult]:
    provenance = await generate_content_with_provenance(prompt, temperature=temperature)
    return _parse_json(provenance["text"]), provenance
