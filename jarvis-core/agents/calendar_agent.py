from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)

async def get_upcoming_events(entities: dict) -> str:
    try:
        service = get_calendar_service()
        now = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=end,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = result.get("items", [])
        if not events:
            return "No upcoming events in the next 7 days."
        output = "Upcoming events:\n"
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                formatted = dt.strftime("%A %d %b, %H:%M")
            except Exception:
                formatted = start
            output += f"• {formatted} — {event.get('summary', 'No title')}\n"
        return output
    except Exception as e:
        return f"JARVIS couldn't fetch calendar: {str(e)}"

async def create_event(entities: dict) -> str:
    try:
        service = get_calendar_service()
        title = entities.get("title", "New meeting")
        date_str = entities.get("date", "")
        time_str = entities.get("time", "")
        duration = int(entities.get("duration", 30) or 30)
        in_minutes = int(entities.get("in_minutes", 0) or 0)

        now = datetime.now()

        if in_minutes:
            start_dt = now + timedelta(minutes=in_minutes)
        elif date_str in ["tomorrow", "завтра"]:
            start_dt = datetime.now().replace(hour=10, minute=0) + timedelta(days=1)
        elif time_str:
            start_dt = datetime.fromisoformat(f"{now.strftime('%Y-%m-%d')}T{time_str}:00")
        else:
            start_dt = now + timedelta(hours=1)

        end_dt = start_dt + timedelta(minutes=duration)
        event = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Rome"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Rome"}
        }
        service.events().insert(calendarId="primary", body=event).execute()
        return f"Reminder set: '{title}' at {start_dt.strftime('%H:%M')} ✅"
    except Exception as e:
        return f"JARVIS couldn't create event: {str(e)}"