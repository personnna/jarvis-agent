import asyncio
from datetime import datetime, timedelta
from agents.calendar_agent import get_calendar_service
from agents.email_agent import get_gmail_service
from services.gemini import general_chat
import json

# глобальный список подключённых WebSocket клиентов
connected_clients = set()

def register_client(websocket):
    global connected_clients
    connected_clients.add(websocket)
    print(f"[PROACTIVE] Client registered. Total: {len(connected_clients)}")

def unregister_client(websocket):
    global connected_clients
    connected_clients.discard(websocket)
    print(f"[PROACTIVE] Client unregistered. Total: {len(connected_clients)}")

async def notify_all(message: str, intent: str = "proactive"):
    global connected_clients
    if not connected_clients:
        return
    data = json.dumps({
        "type": "proactive",
        "intent": intent,
        "message": f"🔔 {message}"
    })
    dead = set()
    for client in connected_clients:
        try:
            await client.send_text(data)
        except Exception:
            dead.add(client)
    connected_clients -= dead

async def check_upcoming_meetings():
    try:
        service = get_calendar_service()
        now = datetime.utcnow()
        soon = (now + timedelta(minutes=20)).isoformat() + "Z"
        now_str = now.isoformat() + "Z"

        events = service.events().list(
            calendarId="primary",
            timeMin=now_str,
            timeMax=soon,
            maxResults=3,
            singleEvents=True,
            orderBy="startTime"
        ).execute().get("items", [])

        for event in events:
            start = event["start"].get("dateTime", "")
            if not start:
                continue
            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            minutes_left = int((dt.replace(tzinfo=None) - now).total_seconds() / 60)

            if 10 <= minutes_left <= 20:
                title = event.get("summary", "Meeting")
                await notify_all(
                    f"You have '{title}' in {minutes_left} minutes.",
                    intent="calendar_alert"
                )
    except Exception as e:
        print(f"[PROACTIVE] Calendar check error: {e}")

async def check_urgent_emails():
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me",
            maxResults=3,
            q="is:unread is:important"
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return

        for msg in messages[:1]:
            detail = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            sender = headers.get("From", "Unknown").split("<")[0].strip()
            subject = headers.get("Subject", "No subject")

            await notify_all(
                f"Urgent email from {sender}: '{subject}'",
                intent="email_alert"
            )
    except Exception as e:
        print(f"[PROACTIVE] Email check error: {e}")

async def proactive_loop():
    print("[PROACTIVE] Starting background monitor...")
    check_count = 0
    while True:
        await asyncio.sleep(60)  # каждую минуту
        check_count += 1

        if not connected_clients:
            continue

        # каждую минуту — проверяем встречи
        await check_upcoming_meetings()

        # каждые 5 минут — проверяем срочные письма
        if check_count % 5 == 0:
            await check_urgent_emails()

        print(f"[PROACTIVE] Check #{check_count} done. Clients: {len(connected_clients)}")
