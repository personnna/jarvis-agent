from services.gemini import general_chat
from agents.jira_agent import create_ticket, list_tickets
from agents.email_agent import read_emails
from agents.calendar_agent import get_upcoming_events, create_event
from agents.research_agent import research
from agents.meeting_agent import meeting_summary
import json
import asyncio

PLANNER_PROMPT = """You are JARVIS planning engine. Given a complex user request, break it into sequential steps. 

- For travel questions ("can i go to X"), use: get_weather for destination, general_chat for recommendation. Do NOT use get_calendar for travel questions.

Available tools:
- get_calendar: get upcoming events from calendar
- list_jira_tickets: list open Jira tickets
- read_emails: read unread emails
- research: search the web for information
- create_jira_ticket: create a Jira ticket (needs: title, description)
- create_calendar_event: create calendar event (needs: title, date, time)
- meeting_summary: summarize meeting transcript
- general_chat: answer with reasoning only (no external tools)

Rules:
1. If request needs only ONE tool → return single step
2. If request needs MULTIPLE tools → break into ordered steps
3. Each step must specify which tool and what parameters
4. Maximum 5 steps

Return ONLY a JSON array of steps:
[
  {"step": 1, "tool": "tool_name", "params": {}, "reason": "why this step"},
  {"step": 2, "tool": "tool_name", "params": {}, "reason": "why this step"}
]

Examples:
User: "prepare me for my team meeting"
[
  {"step": 1, "tool": "get_calendar", "params": {}, "reason": "find when the meeting is"},
  {"step": 2, "tool": "list_jira_tickets", "params": {}, "reason": "check open tickets to discuss"},
  {"step": 3, "tool": "read_emails", "params": {}, "reason": "check recent emails from team"},
  {"step": 4, "tool": "general_chat", "params": {"prompt": "create briefing from gathered data"}, "reason": "compile everything into briefing"}
]

User: "create a bug ticket for login issue"
[
  {"step": 1, "tool": "create_jira_ticket", "params": {"title": "Bug: login issue", "type": "Bug"}, "reason": "create the ticket directly"}
]"""

async def plan_and_execute(text: str, conversation_history: list = []) -> dict:
    steps_taken = []
    gathered_data = {}

    # шаг 1 — планируем
    print(f"[PLANNER] Planning for: {text}")
    plan_response = await general_chat(
        f"{PLANNER_PROMPT}\n\nUser: {text}",
        history=[]
    )

    # парсим план
    try:
        raw = plan_response.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        plan = json.loads(raw.strip())
    except Exception as e:
        print(f"[PLANNER] Failed to parse plan: {e}")
        # fallback — просто general chat
        response = await general_chat(text, history=conversation_history)
        return {"message": response, "intent": "general_chat", "steps": []}

    print(f"[PLANNER] Plan: {json.dumps(plan, indent=2)}")

    # шаг 2 — выполняем каждый шаг
    for step in plan:
        tool = step.get("tool")
        params = step.get("params", {})
        reason = step.get("reason", "")
        step_num = step.get("step", 0)

        print(f"[PLANNER] Step {step_num}: {tool} — {reason}")
        steps_taken.append(f"Step {step_num}: {tool}")

        try:
            if tool == "get_calendar":
                try:
                    result = await asyncio.wait_for(get_upcoming_events(params), timeout=10.0)
                except asyncio.TimeoutError:
                    result = "Calendar unavailable."
                gathered_data["calendar"] = result

            elif tool == "list_jira_tickets":
                result = await list_tickets()
                gathered_data["jira_tickets"] = result

            elif tool == "read_emails":
                result = await read_emails(params)
                gathered_data["emails"] = result

            elif tool == "research":
                result = await research(params)
                gathered_data["research"] = result
            
            elif tool == "get_weather":
                from agents.weather_agent import get_weather
                result = await get_weather(params)
                gathered_data["weather"] = result

            elif tool == "create_jira_ticket":
                result = await create_ticket(params)
                gathered_data["created_ticket"] = result
                # если это единственный шаг — сразу возвращаем
                if len(plan) == 1:
                    return {
                        "message": result,
                        "intent": "create_jira_ticket",
                        "steps": steps_taken
                    }

            elif tool == "create_calendar_event":
                result = await create_event(params)
                gathered_data["created_event"] = result
                if len(plan) == 1:
                    return {
                        "message": result,
                        "intent": "create_calendar_event",
                        "steps": steps_taken
                    }

            elif tool == "meeting_summary":
                result = await meeting_summary(params, text)
                gathered_data["meeting"] = result
                if len(plan) == 1:
                    return {
                        "message": result,
                        "intent": "meeting_summary",
                        "steps": steps_taken
                    }

            elif tool == "general_chat":
                prompt = params.get("prompt", text)
                # передаём все собранные данные как контекст
                context = "\n\n".join([f"{k}:\n{v}" for k, v in gathered_data.items()])
                result = await general_chat(
                    f"{prompt}\n\nUser request: {text}",
                    context=context,
                    history=conversation_history
                )
                gathered_data["final_response"] = result

        except Exception as e:
            print(f"[PLANNER] Step {step_num} failed: {e}")
            gathered_data[f"error_step_{step_num}"] = str(e)
            continue

    # шаг 3 — если есть собранные данные без финального ответа — генерируем
    if "final_response" not in gathered_data and gathered_data:
        context = "\n\n".join([f"{k}:\n{v}" for k, v in gathered_data.items()])
        final = await general_chat(
            f"Based on all gathered information, provide a comprehensive answer to: {text}",
            context=context,
            history=conversation_history
        )
        gathered_data["final_response"] = final

    final_message = gathered_data.get(
        "final_response",
        gathered_data.get(list(gathered_data.keys())[-1], "Done.") if gathered_data else "I couldn't complete this task."
    )

    return {
        "message": final_message,
        "intent": "multi_step",
        "steps": steps_taken,
        "data": gathered_data
    }