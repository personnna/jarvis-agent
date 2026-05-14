from services.gemini import general_chat
from agents.jira_agent import create_ticket
import json

async def meeting_summary(entities: dict, transcript: str = "") -> str:
    try:
        text = transcript or entities.get("text", "")
        if not text:
            return "Please provide meeting transcript or notes."

        # шаг 1 — summary
        summary_prompt = f"""You are JARVIS. Analyze this meeting transcript and return ONLY a JSON object:
{{
    "summary": "2-3 sentence meeting summary",
    "decisions": ["decision 1", "decision 2"],
    "action_items": [
        {{"title": "task title", "assignee": "person name or 'team'", "priority": "High/Medium/Low"}},
    ]
}}

Transcript:
{text}

Return ONLY JSON, no markdown."""

        response = await general_chat(summary_prompt)

        # парсим JSON
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        # шаг 2 — создаём тикеты в Jira для каждого action item
        created_tickets = []
        for item in data.get("action_items", []):
            ticket_entities = {
                "title": item["title"],
                "description": f"From meeting.\nAssignee: {item.get('assignee', 'TBD')}\nPriority: {item.get('priority', 'Medium')}",
                "type": "Task"
            }
            result = await create_ticket(ticket_entities)
            created_tickets.append(result)

        # шаг 3 — формируем красивый ответ
        output = f"Meeting Summary\n{'='*40}\n"
        output += f"\n{data.get('summary', '')}\n"

        if data.get("decisions"):
            output += f"\nDecisions:\n"
            for d in data["decisions"]:
                output += f"• {d}\n"

        if created_tickets:
            output += f"\nJira tickets created:\n"
            for t in created_tickets:
                output += f"• {t}\n"

        return output

    except json.JSONDecodeError:
        # если LLM не вернул JSON — просто summary
        summary = await general_chat(
            f"Summarize this meeting in 3 bullet points and list action items:\n{entities.get('text', '')}"
        )
        return summary
    except Exception as e:
        return f"JARVIS couldn't process meeting: {str(e)}"
