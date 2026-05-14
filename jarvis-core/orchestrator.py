from services.gemini import detect_intent, general_chat
from agents.jira_agent import create_ticket, list_tickets, update_ticket
from agents.research_agent import research
from agents.meeting_agent import meeting_summary
from agents.email_agent import read_emails, draft_email
from agents.calendar_agent import get_upcoming_events, create_event
from planner import plan_and_execute
from demo_data import DEMO_EMAILS, DEMO_TICKETS, DEMO_MEETING, DEMO_RESEARCH, DEMO_CALENDAR
from collections import deque
import os
from database import save_message, get_history, log_agent, save_context, get_context
import time
import uuid
from context_engine import enrich_context, update_user_profile, update_patterns
import asyncio

conversation_history = deque(maxlen=10)
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

COMPLEX_KEYWORDS = [
    "prepare", "briefing", "overview", "get ready", "catch me up",
    "podgotov", "what do i have", "weekly report", "daily summary"
]

def needs_planning(text):
    return any(k in text.lower() for k in COMPLEX_KEYWORDS)

from self_correction import with_retry, self_correcting_intent

async def process_message(text: str, session_id: str = "default") -> dict:
    start_time = time.time()
    await save_message(session_id, "user", text)
    conversation_history.append({"role": "user", "content": text})
    db_history = await get_history(session_id, limit=10)

    if DEMO_MODE:
        intent_data = await self_correcting_intent(detect_intent, text)
        intent = intent_data.get("intent", "general_chat")
        entities = intent_data.get("entities", {})
        message = await handle_demo(intent, entities, text)
        await save_message(session_id, "assistant", message, intent)
        conversation_history.append({"role": "assistant", "content": message})
        return {"type": "response", "intent": intent, "message": message}

    if needs_planning(text):
        print(f"[ORCHESTRATOR] Complex request — using planner")
        result = await with_retry(
            plan_and_execute,
            args=(text, db_history),
            fallback={"message": "I had trouble planning this.", "intent": "general_chat", "steps": []}
        )
        message = result["message"]
        intent = result.get("intent", "multi_step")
        steps = result.get("steps", [])
        duration = int((time.time() - start_time) * 1000)
        await save_message(session_id, "assistant", message, intent)
        await log_agent(session_id, intent, text, message, steps, duration, True)
        await update_patterns(intent, True)
        conversation_history.append({"role": "assistant", "content": message})
        return {"type": "response", "intent": intent, "message": message, "steps": steps}

    intent_data = await self_correcting_intent(detect_intent, text)
    intent = intent_data.get("intent", "general_chat")
    entities = intent_data.get("entities", {})
    print(f"[JARVIS] Intent: {intent} | Entities: {entities}")

    # обогащаем контекстом
    context = await enrich_context(text, intent, entities, session_id)
    print(f"[CONTEXT] Why: {context.get('why')} | Priority: {context.get('priority')}")
    if context.get("warnings"):
        print(f"[CONTEXT] Warnings: {context['warnings']}")

    # обновляем профиль пользователя в фоне
    asyncio.create_task(update_user_profile(text, intent, session_id))

    message = await with_retry(
        handle_live,
        args=(intent, entities, text, db_history, context),
        fallback="I encountered an issue. Please try again."
    )

    duration = int((time.time() - start_time) * 1000)
    await save_message(session_id, "assistant", message, intent)
    await log_agent(session_id, intent, text, message, [], duration, True)
    await update_patterns(intent, True)
    conversation_history.append({"role": "assistant", "content": message})
    return {"type": "response", "intent": intent, "message": message, "context": context}

async def handle_demo(intent, entities, text):
    if intent == "create_jira_ticket":
        title = entities.get("title", "New task")
        return f"Done! Ticket JAR-{len(conversation_history)} created: '{title}' ✅"
    elif intent == "list_jira_tickets":
        return DEMO_TICKETS
    elif intent == "read_emails":
        return DEMO_EMAILS
    elif intent == "meeting_summary":
        return DEMO_MEETING
    elif intent == "research":
        return DEMO_RESEARCH
    elif intent in ["get_calendar", "create_calendar_event"]:
        return DEMO_CALENDAR
    else:
        return await general_chat(text, history=list(conversation_history)[:-1])

async def handle_live(intent, entities, text, history=[], context=None):
    enriched_response = ""

    if intent == "create_jira_ticket":
        result = await create_ticket(entities)
        if context and context.get("warnings"):
            warnings = "\n".join([f"⚠️ {w}" for w in context["warnings"]])
            result = f"{result}\n\n{warnings}"
        if context and context.get("suggestions"):
            suggestions = "\n".join([f"💡 {s}" for s in context["suggestions"][:2]])
            result = f"{result}\n\n{suggestions}"
        return result
    elif intent == "list_jira_tickets":
        return await list_tickets()
    elif intent == "update_jira_ticket":
        return await update_ticket(entities)
    elif intent == "research":
        return await research(entities)
    elif intent == "meeting_summary":
        return await meeting_summary(entities, text)
    elif intent == "read_emails":
        return await read_emails(entities)
    elif intent == "send_email":
        return await draft_email(entities)
    elif intent == "get_calendar":
        return await get_upcoming_events(entities)
    elif intent == "create_calendar_event":
        return await create_event(entities)
    else:
        return await general_chat(text, history=history)