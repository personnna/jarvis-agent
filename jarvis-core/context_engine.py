from database import get_history, get_context, save_context
from services.gemini import general_chat
import json

async def enrich_context(text: str, intent: str, entities: dict, session_id: str = "default") -> dict:
    history = await get_history(session_id, limit=20)
    user_profile = await get_context("user_profile") or "{}"
    patterns = await get_context("patterns") or "{}"

    try:
        profile = json.loads(user_profile)
        pattern_data = json.loads(patterns)
    except Exception:
        profile = {}
        pattern_data = {}

    enrichment_prompt = f"""You are JARVIS context engine. Analyze this request and provide enrichment.

User request: {text}
Intent: {intent}
Entities: {json.dumps(entities)}

User profile: {json.dumps(profile)}
Recent patterns: {json.dumps(pattern_data)}
Recent history (last 5):
{chr(10).join([f"{m['role']}: {m['content'][:100]}" for m in history[-5:]])}

Return ONLY a JSON object:
{{
    "why": "what the user is trying to achieve (1 sentence)",
    "context_hints": ["relevant context from history or profile"],
    "warnings": ["potential issues to flag"],
    "suggestions": ["proactive suggestions beyond the request"],
    "priority": "high/medium/low based on context"
}}"""

    try:
        response = await general_chat(enrichment_prompt, history=[])
        raw = response.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[CONTEXT] Enrichment failed: {e}")
        return {
            "why": "direct request",
            "context_hints": [],
            "warnings": [],
            "suggestions": [],
            "priority": "medium"
        }

async def update_user_profile(text: str, intent: str, session_id: str = "default"):
    current = await get_context("user_profile") or "{}"
    try:
        profile = json.loads(current)
    except Exception:
        profile = {}

    update_prompt = f"""Extract user profile information from this message and current profile.
Message: {text}
Intent: {intent}
Current profile: {json.dumps(profile)}

Update the profile with any NEW information found (name, role, preferences, tools used, timezone, language).
Return ONLY updated JSON profile. If nothing new, return current profile unchanged."""

    try:
        response = await general_chat(update_prompt, history=[])
        raw = response.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        updated = json.loads(raw.strip())
        await save_context("user_profile", json.dumps(updated))
    except Exception as e:
        print(f"[CONTEXT] Profile update failed: {e}")

async def update_patterns(intent: str, success: bool):
    current = await get_context("patterns") or "{}"
    try:
        patterns = json.loads(current)
    except Exception:
        patterns = {}

    if intent not in patterns:
        patterns[intent] = {"count": 0, "success": 0}

    patterns[intent]["count"] += 1
    if success:
        patterns[intent]["success"] += 1

    await save_context("patterns", json.dumps(patterns))
