"""
Email + Calendar agent — Gmail + Google Calendar.

First-time setup:
  1. Go to console.cloud.google.com → create a project
  2. Enable Gmail API and Google Calendar API
  3. APIs & Services → Credentials → Create OAuth client ID (Desktop app)
  4. Download the JSON → save as  multi_agent/credentials.json
  5. Run the bot — a browser window opens for one-time authorisation
     Token saved to multi_agent/token.json and reused automatically after that.
"""

import base64
import json
from datetime import datetime, timedelta, date
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq

# ---------------------------------------------------------------------------
# OAuth setup
# ---------------------------------------------------------------------------

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

_DIR = Path(__file__).parent
_CREDS_FILE = _DIR / "credentials.json"
_TOKEN_FILE = _DIR / "token.json"


def _get_credentials() -> Credentials:
    creds = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDS_FILE), _SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())
    return creds


def _gmail():
    return build("gmail", "v1", credentials=_get_credentials(), cache_discovery=False)


def _gcal():
    return build("calendar", "v3", credentials=_get_credentials(), cache_discovery=False)


# ---------------------------------------------------------------------------
# Gmail helpers
# ---------------------------------------------------------------------------

def _parse_headers(headers: list[dict]) -> dict:
    return {h["name"]: h["value"] for h in headers}


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data")
    if mime == "text/plain" and data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


# ---------------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------------

def _events_in_range(days_ahead: int) -> list[dict]:
    now = datetime.utcnow().isoformat() + "Z"
    cutoff = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
    result = (
        _gcal()
        .events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=cutoff,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = []
    for e in result.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        end = e["end"].get("dateTime", e["end"].get("date", ""))
        events.append({
            "id": e["id"],
            "title": e.get("summary", "No title"),
            "date": start[:10],
            "start": start,
            "end": end,
            "attendees": [a["email"] for a in e.get("attendees", [])],
            "notes": e.get("description", ""),
        })
    return events


def _free_slots_on(target_date: date, duration_minutes: int) -> list[dict]:
    day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0).isoformat() + "Z"
    day_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59).isoformat() + "Z"
    result = (
        _gcal()
        .events()
        .list(
            calendarId="primary",
            timeMin=day_start,
            timeMax=day_end,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    busy = []
    for e in result.get("items", []):
        s = e["start"].get("dateTime")
        en = e["end"].get("dateTime")
        if s and en:
            busy.append((
                datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None),
                datetime.fromisoformat(en.replace("Z", "+00:00")).replace(tzinfo=None),
            ))

    work_start = datetime(target_date.year, target_date.month, target_date.day, 9, 0)
    work_end = datetime(target_date.year, target_date.month, target_date.day, 18, 0)
    step = timedelta(minutes=30)
    duration = timedelta(minutes=duration_minutes)
    slots = []
    cursor = work_start
    while cursor + duration <= work_end:
        slot_end = cursor + duration
        if not any(s < slot_end and en > cursor for s, en in busy):
            slots.append({"start": cursor.isoformat(), "end": slot_end.isoformat()})
        cursor += step
    return slots


# ---------------------------------------------------------------------------
# Email tools
# ---------------------------------------------------------------------------

def get_emails(max_emails: int = 20, read_status: str = "all") -> str:
    query_map = {"unread": "is:unread", "read": "is:read", "all": ""}
    q = query_map.get(read_status, "")
    count = min(max(max_emails, 1), 50)

    kwargs: dict = dict(userId="me", labelIds=["INBOX"], maxResults=count)
    if q:
        kwargs["q"] = q

    results = _gmail().users().messages().list(**kwargs).execute()
    messages = results.get("messages", [])

    emails = []
    svc = _gmail()
    for msg in messages:
        m = svc.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        h = _parse_headers(m["payload"]["headers"])
        emails.append({
            "id": m["id"],
            "thread_id": m["threadId"],
            "from": h.get("From", ""),
            "subject": h.get("Subject", ""),
            "date": h.get("Date", ""),
            "read": "UNREAD" not in m.get("labelIds", []),
            "preview": m.get("snippet", ""),
        })

    return json.dumps(emails, indent=2)


def get_email_details(email_id: str) -> str:
    m = _gmail().users().messages().get(userId="me", id=email_id, format="full").execute()
    body = _extract_body(m["payload"])
    return json.dumps({"id": email_id, "body": body, "attachments": []}, indent=2)


def get_thread(thread_id: str) -> str:
    thread = _gmail().users().threads().get(userId="me", id=thread_id).execute()
    messages = []
    for m in thread.get("messages", []):
        h = _parse_headers(m["payload"]["headers"])
        messages.append({
            "id": m["id"],
            "thread_id": m["threadId"],
            "from": h.get("From", ""),
            "subject": h.get("Subject", ""),
            "date": h.get("Date", ""),
            "read": "UNREAD" not in m.get("labelIds", []),
            "preview": m.get("snippet", ""),
        })
    return json.dumps(messages, indent=2)


# ---------------------------------------------------------------------------
# Calendar tools
# ---------------------------------------------------------------------------

def get_upcoming_events(days_ahead: int = 7) -> str:
    events = _events_in_range(min(max(days_ahead, 1), 30))
    return json.dumps(events, indent=2)


def find_free_slots(date_str: str, duration_minutes: int = 60) -> str:
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return json.dumps({"error": f"Invalid date format: {date_str}. Use YYYY-MM-DD."})
    slots = _free_slots_on(target, max(duration_minutes, 15))
    return json.dumps({"date": date_str, "free_slots": slots}, indent=2)


# ---------------------------------------------------------------------------
# Groq tool schemas + dispatcher
# ---------------------------------------------------------------------------

_GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_emails",
            "description": "Retrieve emails from the Gmail inbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_emails": {
                        "type": "integer",
                        "description": "Maximum number of emails to retrieve (1–50, default 20).",
                    },
                    "read_status": {
                        "type": "string",
                        "enum": ["all", "unread", "read"],
                        "description": "Filter by read status — 'all' (default), 'unread', or 'read'.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_details",
            "description": "Get the full body of a specific email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The Gmail message ID (from get_emails or get_thread).",
                    },
                },
                "required": ["email_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_thread",
            "description": "Get all emails in a Gmail thread in chronological order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "The Gmail thread ID (from get_emails results).",
                    },
                },
                "required": ["thread_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get Google Calendar events for the next N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to look ahead (1–30, default 7).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_free_slots",
            "description": "Find available time slots on a given date within working hours (9am–6pm).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "Date to check in YYYY-MM-DD format.",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Required slot length in minutes (default 60).",
                    },
                },
                "required": ["date_str"],
            },
        },
    },
]

_TOOL_MAP = {
    "get_emails": get_emails,
    "get_email_details": get_email_details,
    "get_thread": get_thread,
    "get_upcoming_events": get_upcoming_events,
    "find_free_slots": find_free_slots,
}


def _call_tool(name: str, args: dict) -> str:
    fn = _TOOL_MAP.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    return fn(**args)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are a productivity assistant with access to the user's real Gmail inbox "
    "and Google Calendar.\n\n"
    "When asked about emails: surface urgent items, flag stale threads needing "
    "closure, and note any commitments the user has made but not yet fulfilled.\n\n"
    "When asked about the calendar: summarise upcoming events, highlight deadlines, "
    "and flag conflicts or preparation needed.\n\n"
    "When relevant, cross-reference both — e.g. a contract deadline in the calendar "
    "that maps to an unsigned email, or a meeting tomorrow where an open thread "
    "should be resolved first.\n\n"
    "Use get_thread to reconstruct context on older conversations before drawing "
    "conclusions. Present findings grouped by priority. Be concise."
)

_MODEL = "llama-3.3-70b-versatile"


class EmailCalendarAgent:
    def __init__(self):
        self.client = Groq()

    def run(self, request: str) -> str:
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": request},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                tools=_GROQ_TOOLS,
                tool_choice="auto",
                max_tokens=4096,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                result = message.content or ""
                print(result)
                return result

            messages.append(message)

            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                tool_result = _call_tool(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                })
