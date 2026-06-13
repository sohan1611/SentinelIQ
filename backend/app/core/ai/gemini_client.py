import json
import asyncio
import google.generativeai as genai
from app.config import settings
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

async def generate_content(prompt: str) -> str | None:
    try:
        def _call():
            response = model.generate_content(prompt)
            return response.text
        return await asyncio.to_thread(_call)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None

async def generate_json(prompt: str) -> dict | list | None:
    text = await generate_content(prompt)
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
