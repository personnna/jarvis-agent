from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from services.gemini import general_chat
import base64
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

executor = ThreadPoolExecutor(max_workers=2)

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def _sync_read_emails():
    service = get_gmail_service()
    results = service.users().messages().list(
        userId="me",
        maxResults=5,
        q="is:unread"
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        return None, []
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append(
            f"From: {headers.get('From', 'Unknown')}\n"
            f"Subject: {headers.get('Subject', 'No subject')}"
        )
    return len(messages), emails

async def read_emails(entities: dict) -> str:
    try:
        loop = asyncio.get_event_loop()
        count, emails = await asyncio.wait_for(
            loop.run_in_executor(executor, _sync_read_emails),
            timeout=20.0
        )
        if count is None:
            return "No unread emails."
        context = "\n---\n".join(emails)
        summary = await general_chat(
            f"Summarize these {count} unread emails briefly. List each one as a bullet point with sender and subject. Be concise:\n{context}"
        )
        return f"{count} unread emails:\n\n{summary}"
    except asyncio.TimeoutError:
        return "Gmail is taking too long. Try again."
    except Exception as e:
        return f"JARVIS couldn't read emails: {str(e)}"

async def draft_email(entities: dict) -> str:
    try:
        service = get_gmail_service()
        to = entities.get("recipient", "")
        subject = entities.get("subject", "")
        body_hint = entities.get("body", entities.get("text", ""))
        if not to:
            return "Please specify recipient."
        draft_text = await general_chat(
            f"Write a professional email body.\nTo: {to}\nSubject: {subject}\nContext: {body_hint}\nWrite only the email body."
        )
        email_message = f"To: {to}\nSubject: {subject}\n\n{draft_text}"
        encoded = base64.urlsafe_b64encode(email_message.encode()).decode()
        service.users().drafts().create(
            userId="me",
            body={"message": {"raw": encoded}}
        ).execute()
        return f"Draft created. Subject: '{subject}' to {to}\n\nPreview:\n{draft_text[:300]}..."
    except Exception as e:
        return f"JARVIS couldn't draft email: {str(e)}"
