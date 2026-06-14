import json
import asyncio
import random
import logging
from typing import TypedDict

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

DEFAULT_MODEL_ID = "gemini-1.5-flash"
model = genai.GenerativeModel(DEFAULT_MODEL_ID)

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2.0


class GenerationResult(TypedDict):
    text: str | None
    prompt: str
    model_id: str
    raw_response: str | None


def _build_config(temperature: float | None) -> dict | None:
    if temperature is None:
        return None
    return {"temperature": temperature}


async def _call_with_backoff(fn):
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return await asyncio.to_thread(fn)
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
    def _call():
        config = _build_config(temperature)
        if config:
            return model.generate_content(prompt, generation_config=config).text
        return model.generate_content(prompt).text

    try:
        return await _call_with_backoff(_call)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


async def generate_content_with_provenance(prompt: str, temperature: float = 0.0) -> GenerationResult:
    text = await generate_content(prompt, temperature=temperature)
    return {
        "text": text,
        "prompt": prompt,
        "model_id": DEFAULT_MODEL_ID,
        "raw_response": text,
    }


def _parse_json(text: str | None) -> dict | list | None:
    if not text:
        return None
    try:
        # Strip markdown json blocks if present
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
    text = await generate_content(prompt, temperature=temperature)
    provenance: GenerationResult = {
        "text": text,
        "prompt": prompt,
        "model_id": DEFAULT_MODEL_ID,
        "raw_response": text,
    }
    return _parse_json(text), provenance
