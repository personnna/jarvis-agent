from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
MODEL = "llama-3.3-70b-versatile"

INTENT_PROMPT = INTENT_PROMPT = """You are an intent classifier. You MUST respond with ONLY a JSON object, nothing else.

RULES:
- If message mentions "ticket", "bug", "issue", "jira" → intent = "create_jira_ticket"
- If message mentions "list", "show", "open tickets" → intent = "list_jira_tickets"
- If message mentions "show emails", "read emails", "unread", "inbox", "check email", "почту", "письма" → intent = "read_emails"
- If message mentions "send email", "write email", "draft email" → intent = "send_email"
- If message mentions "meeting", "summary", "standup" → intent = "meeting_summary"
- If message mentions "find", "search", "best practices", "how to", "research" → intent = "research"
- If message mentions "calendar", "events", "meetings", "schedule", "what's on", "календарь", "встречи", "расписание" → intent = "get_calendar"
- If message mentions "create event", "schedule meeting", "add to calendar", "создай встречу", "запланируй" → intent = "create_calendar_event"
- If message mentions "conflicts", "schedule ok", "do i have time", "check my schedule", "busy" → intent = "check_conflicts"
- If message mentions "can i go", "is it possible", "do i have time for", "feasible", "смогу ли" → intent = "check_feasibility"
- If message mentions "weather", "rain", "temperature", "forecast", "погода", "дождь" → intent = "get_weather". Extract city into entities as "city".
- If message mentions "remind", "reminder", "in X minutes/hours" → intent = "create_calendar_event"
For create_calendar_event extract: title, date (YYYY-MM-DD), time (HH:MM), duration (minutes), in_minutes (if "in X minutes" → extract X as integer)
- Everything else → intent = "general_chat"

Response format:
{"intent": "INTENT_HERE", "entities": {}, "confidence": 0.95}

For create_jira_ticket extract title into entities.
For research extract query into entities as "query".
For create_calendar_event extract: title, date (YYYY-MM-DD), time (HH:MM), duration (minutes)."""

SYSTEM_PROMPT = """You are JARVIS, a smart AI assistant.
STRICT RULES:
1) Always respond in EXACTLY the same language the user used. English→English, Russian→Russian, Kazakh→Kazakh. Never mix languages.
2) Never use 'Ma'am' or 'Sir'. Address user neutrally.
3) Be concise and helpful with a subtle Marvel JARVIS personality.
4) Remember context from conversation history."""

def get_system_prompt():
    return f"""You are JARVIS, a smart AI assistant.
Current date and time: {datetime.now().strftime('%A, %d %B %Y, %H:%M')}
STRICT RULES:
1) Always respond in EXACTLY the same language the user used.
2) Never use 'Ma'am' or 'Sir'. Address user neutrally.
3) Be concise and helpful with a subtle Marvel JARVIS personality.
4) Remember context from conversation history.
5) NEVER ask clarifying questions. Just do it. If information is missing — use reasonable defaults and act immediately.
6) When user asks to create a ticket — create it. When user asks to read emails — read them. No questions, just action."""


async def detect_intent(text: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": text}
            ],
            max_tokens=200,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = (raw.split)[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {
            "intent": "general_chat",
            "entities": {"text": text},
            "confidence": 0.5
        }

async def general_chat(text: str, context: str = "", history: list = []) -> str:
    try:
        messages = [{"role": "system", "content": get_system_prompt()}]

        if history:
            messages.extend(history[-6:])

        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})

        messages.append({"role": "user", "content": text})

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"JARVIS encountered an error: {str(e)}"


async def general_chat_stream(text: str, history: list = []):
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": text})

        stream = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            stream=True
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        yield f"JARVIS error: {str(e)}"
