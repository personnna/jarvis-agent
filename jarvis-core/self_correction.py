import asyncio
import json
from services.gemini import general_chat

async def with_retry(func, args=(), kwargs={}, max_retries=3, fallback=None):
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await func(*args, **kwargs)
            # проверяем только строки, dict пропускаем
            if isinstance(result, str) and "error" in result.lower()[:50]:
                raise ValueError(f"Bad result: {result[:100]}")
            return result
        except Exception as e:
            last_error = e
            print(f"[SELF-CORRECTION] Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
                print(f"[SELF-CORRECTION] Retrying...")
    if fallback:
        return fallback
    return f"I encountered an issue after {max_retries} attempts: {last_error}"

    
async def safe_json_parse(text: str, retry_prompt: str = None) -> dict:
    for attempt in range(3):
        try:
            raw = text.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            print(f"[SELF-CORRECTION] JSON parse failed attempt {attempt+1}: {e}")
            if retry_prompt and attempt < 2:
                print("[SELF-CORRECTION] Asking LLM to fix JSON...")
                text = await general_chat(
                    f"Fix this invalid JSON and return ONLY valid JSON, nothing else:\n{text}\nError: {e}"
                )
    return {}

async def self_correcting_intent(detect_func, text: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            result = await detect_func(text)
            if "intent" in result and result["intent"]:
                return result
            raise ValueError(f"Missing intent in result: {result}")
        except Exception as e:
            print(f"[SELF-CORRECTION] Intent detection failed attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
    return {"intent": "general_chat", "entities": {}, "confidence": 0.0}
