from agents.calendar_agent import get_calendar_service
from services.gemini import general_chat
from datetime import datetime, timedelta
import json

async def check_conflicts(entities: dict) -> str:
    try:
        service = get_calendar_service()
        now = datetime.utcnow()
        end = (now + timedelta(days=7)).isoformat() + "Z"
        now_str = now.isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now_str,
            timeMax=end,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if len(events) < 2:
            return "No conflicts found — your schedule looks clear!"

        conflicts = []
        for i in range(len(events) - 1):
            e1 = events[i]
            e2 = events[i + 1]

            start1 = e1["start"].get("dateTime")
            end1 = e1["end"].get("dateTime")
            start2 = e2["start"].get("dateTime")

            if not start1 or not end1 or not start2:
                continue

            try:
                dt_end1 = datetime.fromisoformat(end1.replace("Z", "+00:00"))
                dt_start2 = datetime.fromisoformat(start2.replace("Z", "+00:00"))
                dt_start1 = datetime.fromisoformat(start1.replace("Z", "+00:00"))

                gap_minutes = int((dt_start2 - dt_end1).total_seconds() / 60)
                title1 = e1.get("summary", "Event 1")
                title2 = e2.get("summary", "Event 2")

                if gap_minutes < 0:
                    conflicts.append({
                        "type": "overlap",
                        "event1": title1,
                        "event2": title2,
                        "overlap_minutes": abs(gap_minutes)
                    })
                elif gap_minutes < 15:
                    conflicts.append({
                        "type": "tight",
                        "event1": title1,
                        "event2": title2,
                        "gap_minutes": gap_minutes,
                        "time1": dt_start1.strftime("%a %d %b %H:%M"),
                        "time2": dt_start2.strftime("%a %d %b %H:%M")
                    })
            except Exception:
                continue

        if not conflicts:
            return "Your schedule looks good — no conflicts detected! ✅"

        conflict_text = json.dumps(conflicts, ensure_ascii=False)
        summary = await general_chat(
            f"""Analyze these calendar conflicts and explain them naturally like JARVIS would.
Be specific about timing. Give practical advice.
Conflicts: {conflict_text}"""
        )
        return f"⚠️ Schedule Analysis:\n\n{summary}"

    except Exception as e:
        return f"JARVIS couldn't check conflicts: {str(e)}"

async def check_event_feasibility(entities: dict) -> str:
    try:
        title = entities.get("title", "this event")
        duration = int(entities.get("duration", 60) or 60)
        date_str = entities.get("date", datetime.now().strftime("%Y-%m-%d"))
        time_str = entities.get("time", "10:00")
        travel_minutes = int(entities.get("travel_minutes", 0) or 0)

        service = get_calendar_service()
        try:
            proposed_start = datetime.fromisoformat(f"{date_str}T{time_str}:00")
        except Exception:
            proposed_start = datetime.now() + timedelta(hours=1)

        proposed_end = proposed_start + timedelta(minutes=duration)

        window_start = (proposed_start - timedelta(hours=2)).isoformat() + "Z"
        window_end = (proposed_end + timedelta(hours=2)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=window_start,
            timeMax=window_end,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        nearby = events_result.get("items", [])

        analysis_prompt = f"""You are JARVIS analyzing if an event is feasible.

Proposed event: '{title}'
Start: {proposed_start.strftime('%A %d %b at %H:%M')}
Duration: {duration} minutes
Travel time needed: {travel_minutes} minutes

Nearby events: {json.dumps([{
    'title': e.get('summary', 'Event'),
    'start': e['start'].get('dateTime', ''),
    'end': e['end'].get('dateTime', '')
} for e in nearby], ensure_ascii=False)}

Analyze if this is feasible. Check for:
1. Time conflicts
2. Not enough travel time
3. Back-to-back events with no break
4. Give a clear YES/NO recommendation with specific timing advice.

Be concise and direct like JARVIS."""

        result = await general_chat(analysis_prompt)
        return result

    except Exception as e:
        return f"JARVIS couldn't analyze feasibility: {str(e)}"
