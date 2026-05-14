from jira import JIRA
from self_correction import with_retry
from dotenv import load_dotenv
import os
import httpx
import base64

load_dotenv()

def get_jira_client():
    return JIRA(
        server=os.getenv("JIRA_BASE_URL"),
        basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
    )

async def create_ticket(entities: dict) -> str:
    async def _create():
        jira = get_jira_client()
        title = entities.get("title", "New ticket from JARVIS")
        description = entities.get("description", "Created by JARVIS")
        issue_type = entities.get("type", "Task")
        issue = jira.create_issue(
            project=os.getenv("JIRA_PROJECT_KEY"),
            summary=title,
            description=description,
            issuetype={"name": issue_type}
        )
        return f"Done! Ticket {issue.key} created: '{title}'"

    return await with_retry(_create, fallback="Couldn't create ticket after retries.")

async def list_tickets() -> str:
    try:
        email = os.getenv("JIRA_EMAIL")
        token = os.getenv("JIRA_API_TOKEN")
        base_url = os.getenv("JIRA_BASE_URL")
        project = os.getenv("JIRA_PROJECT_KEY")

        credentials = base64.b64encode(f"{email}:{token}".encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/rest/api/3/search/jql",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json"
                },
                json={
                    "jql": f"project={project} AND status != Done ORDER BY created DESC",
                    "maxResults": 5,
                    "fields": ["summary", "status", "issuetype"]
                }
            )
            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                return "No open tickets found."

            result = "Open tickets:\n"
            for issue in issues:
                key = issue["key"]
                summary = issue["fields"]["summary"]
                status = issue["fields"]["status"]["name"]
                result += f"• {key}: {summary} [{status}]\n"
            return result
    except Exception as e:
        return f"JARVIS couldn't fetch tickets: {str(e)}"

async def update_ticket(entities: dict) -> str:
    try:
        email = os.getenv("JIRA_EMAIL")
        token = os.getenv("JIRA_API_TOKEN")
        base_url = os.getenv("JIRA_BASE_URL")
        ticket_key = entities.get("ticket_key")

        if not ticket_key:
            return "Please specify a ticket key, e.g. JAR-1"

        credentials = base64.b64encode(f"{email}:{token}".encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/rest/api/3/issue/{ticket_key}",
                headers={"Authorization": f"Basic {credentials}"}
            )
            if response.status_code == 200:
                return f"Ticket {ticket_key} found and ready to update."
            return f"Ticket {ticket_key} not found."
    except Exception as e:
        return f"JARVIS couldn't update ticket: {str(e)}"
