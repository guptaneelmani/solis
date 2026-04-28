"""
Email + Calendar agent.

Mock data is provided so the agent works immediately.
To connect real services, replace the _fetch_* and _build_* functions with
calls to your provider (Gmail API, Google Calendar API, Microsoft Graph, IMAP, etc.).
"""

import json
from datetime import datetime, timedelta, date

import anthropic
from anthropic import beta_tool

# ---------------------------------------------------------------------------
# Mock email data
# ---------------------------------------------------------------------------

_ALL_EMAILS = None


def _build_emails() -> list[dict]:
    now = datetime.now()
    return [
        # recent, unread
        {
            "id": "e001", "thread_id": "t001",
            "from": "ceo@company.com",
            "subject": "URGENT: Board deck needs your slide by EOD",
            "date": (now - timedelta(hours=1)).isoformat(),
            "read": False,
            "preview": "Hi, I need your department slide for the board presentation. Please send by 5pm today.",
        },
        {
            "id": "e003", "thread_id": "t003",
            "from": "hr@company.com",
            "subject": "Action required: Complete annual compliance training",
            "date": (now - timedelta(days=5)).isoformat(),
            "read": False,
            "preview": "This is your third reminder. The deadline is this Friday.",
        },
        {
            "id": "e004", "thread_id": "t004",
            "from": "noreply@github.com",
            "subject": "PR review requested: fix/auth-token-expiry",
            "date": (now - timedelta(hours=4)).isoformat(),
            "read": False,
            "preview": "alice requested your review on pull request #142.",
        },
        # recent, read
        {
            "id": "e002", "thread_id": "t002",
            "from": "client@bigcorp.com",
            "subject": "Re: Proposal — still waiting for revised quote",
            "date": (now - timedelta(days=3)).isoformat(),
            "read": True,
            "preview": "Following up again on the revised pricing proposal we discussed last week...",
        },
        {
            "id": "e005", "thread_id": "t005",
            "from": "newsletter@techdigest.io",
            "subject": "This week in AI — April digest",
            "date": (now - timedelta(days=1)).isoformat(),
            "read": True,
            "preview": "Top stories: new model benchmarks, open-source releases, and regulatory updates...",
        },
        # older threads needing closure
        {
            "id": "e006", "thread_id": "t006",
            "from": "vendor@supplierco.com",
            "subject": "Re: Contract renewal — awaiting your signature",
            "date": (now - timedelta(days=18)).isoformat(),
            "read": True,
            "preview": "We sent the updated contract two weeks ago. Could you confirm receipt and sign?",
        },
        {
            "id": "e007", "thread_id": "t007",
            "from": "alice@company.com",
            "subject": "Re: Q1 retrospective action items",
            "date": (now - timedelta(days=30)).isoformat(),
            "read": True,
            "preview": "Here are the 5 action items we agreed on. I'll follow up in a month on progress.",
        },
        {
            "id": "e008", "thread_id": "t008",
            "from": "recruiter@talentfirm.com",
            "subject": "Re: Senior engineer candidate — feedback requested",
            "date": (now - timedelta(days=14)).isoformat(),
            "read": True,
            "preview": "The candidate is still available. Are you ready to proceed to the offer stage?",
        },
        {
            "id": "e009", "thread_id": "t002",
            "from": "you@company.com",
            "subject": "Re: Proposal — still waiting for revised quote",
            "date": (now - timedelta(days=10)).isoformat(),
            "read": True,
            "preview": "Hi, I'll have the revised numbers to you by end of next week.",
        },
        {
            "id": "e010", "thread_id": "t009",
            "from": "bob@partnerorg.com",
            "subject": "Partnership proposal — next steps?",
            "date": (now - timedelta(days=45)).isoformat(),
            "read": True,
            "preview": "It's been a while since our last call. Would love to reconnect and discuss moving forward.",
        },
    ]


_EMAIL_BODIES = {
    "e001": "Hi team, I need everyone's department slide for the Q2 board presentation. Format: 3 bullets max, include key metric. Please send to me directly by 5pm today. This is critical.",
    "e002": "Hi, I've sent two follow-up emails about the revised quote. Our procurement team needs this to proceed. Please respond ASAP or we'll have to look at other vendors.",
    "e003": "This is your third reminder. The compliance training deadline is this Friday. Non-completion will be escalated to your manager. Link: https://training.internal/compliance",
    "e004": "PR #142 fixes the auth token expiry bug causing user logouts. Alice needs your review before merging. CI is green.",
    "e005": "Newsletter content here...",
    "e006": "We sent the updated contract on the 10th. Please check your inbox for the DocuSign link. The renewal window closes at end of month.",
    "e007": "Action items from Q1 retro: (1) migrate CI pipeline, (2) document onboarding, (3) resolve vendor contract, (4) hire two engineers, (5) finish API v2. Let me know if anything has changed.",
    "e008": "The candidate interviewed really well with your team. She's currently considering two other offers. If you want to move forward, we need feedback this week.",
    "e009": "Hi, I'll have the revised numbers to you by end of next week. Apologies for the delay — we're finalising Q2 costs.",
    "e010": "Hi, it's been about six weeks since we spoke at the summit. I wanted to check in on whether a partnership still makes sense. Happy to jump on a call.",
}


def _get_all_emails() -> list[dict]:
    global _ALL_EMAILS
    if _ALL_EMAILS is None:
        _ALL_EMAILS = _build_emails()
    return _ALL_EMAILS


# ---------------------------------------------------------------------------
# Mock calendar data
# ---------------------------------------------------------------------------

_ALL_EVENTS = None


def _build_events() -> list[dict]:
    today = date.today()
    return [
        {
            "id": "c001",
            "title": "Q2 Board Presentation",
            "date": today.isoformat(),
            "start": f"{today}T15:00:00",
            "end": f"{today}T17:00:00",
            "attendees": ["ceo@company.com", "board@company.com"],
            "notes": "Department slides must be submitted before this meeting.",
        },
        {
            "id": "c002",
            "title": "Compliance training deadline",
            "date": (today + timedelta(days=2)).isoformat(),
            "start": f"{today + timedelta(days=2)}T23:59:00",
            "end": f"{today + timedelta(days=2)}T23:59:00",
            "attendees": [],
            "type": "deadline",
            "notes": "Annual compliance training must be completed by end of day.",
        },
        {
            "id": "c003",
            "title": "1:1 with Alice",
            "date": (today + timedelta(days=1)).isoformat(),
            "start": f"{today + timedelta(days=1)}T10:00:00",
            "end": f"{today + timedelta(days=1)}T10:30:00",
            "attendees": ["alice@company.com"],
            "notes": "Weekly sync. Q1 retro action items would be a good topic.",
        },
        {
            "id": "c004",
            "title": "Engineering All-Hands",
            "date": (today + timedelta(days=2)).isoformat(),
            "start": f"{today + timedelta(days=2)}T14:00:00",
            "end": f"{today + timedelta(days=2)}T15:30:00",
            "attendees": ["engineering@company.com"],
            "notes": "Quarterly all-hands. Agenda includes API v2 and hiring update.",
        },
        {
            "id": "c005",
            "title": "Contract renewal deadline: SupplierCo",
            "date": (today + timedelta(days=3)).isoformat(),
            "start": f"{today + timedelta(days=3)}T23:59:00",
            "end": f"{today + timedelta(days=3)}T23:59:00",
            "attendees": [],
            "type": "deadline",
            "notes": "DocuSign link in email from vendor@supplierco.com. Must sign before window closes.",
        },
        {
            "id": "c006",
            "title": "Interview: Senior Engineer (final round)",
            "date": (today + timedelta(days=5)).isoformat(),
            "start": f"{today + timedelta(days=5)}T11:00:00",
            "end": f"{today + timedelta(days=5)}T12:00:00",
            "attendees": ["recruiter@talentfirm.com"],
            "notes": "Confirm offer decision before this. Recruiter is waiting for feedback.",
        },
        {
            "id": "c007",
            "title": "Sprint Planning",
            "date": (today + timedelta(days=7)).isoformat(),
            "start": f"{today + timedelta(days=7)}T09:00:00",
            "end": f"{today + timedelta(days=7)}T11:00:00",
            "attendees": ["engineering@company.com"],
            "notes": "Next sprint kick-off. CI pipeline migration should be on the agenda.",
        },
    ]


def _get_all_events() -> list[dict]:
    global _ALL_EVENTS
    if _ALL_EVENTS is None:
        _ALL_EVENTS = _build_events()
    return _ALL_EVENTS


def _events_in_range(days_ahead: int) -> list[dict]:
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    return [
        e for e in _get_all_events()
        if today <= date.fromisoformat(e["date"]) <= cutoff
    ]


def _free_slots_on(target_date: date, duration_minutes: int) -> list[dict]:
    """Return available slots on target_date given existing events."""
    busy = [
        (datetime.fromisoformat(e["start"]), datetime.fromisoformat(e["end"]))
        for e in _get_all_events()
        if e["date"] == target_date.isoformat() and "T" in e.get("start", "")
    ]
    work_start = datetime(target_date.year, target_date.month, target_date.day, 9, 0)
    work_end = datetime(target_date.year, target_date.month, target_date.day, 18, 0)
    step = timedelta(minutes=30)
    duration = timedelta(minutes=duration_minutes)
    slots = []
    cursor = work_start
    while cursor + duration <= work_end:
        slot_end = cursor + duration
        if not any(s < slot_end and e > cursor for s, e in busy):
            slots.append({"start": cursor.isoformat(), "end": slot_end.isoformat()})
        cursor += step
    return slots


# ---------------------------------------------------------------------------
# Email tools
# ---------------------------------------------------------------------------

@beta_tool
def get_emails(max_emails: int = 20, read_status: str = "all") -> str:
    """Retrieve emails from the inbox.

    Args:
        max_emails: Maximum number of emails to retrieve (1–50, default 20).
        read_status: Filter emails — "all" (default), "unread", or "read".
    """
    emails = _get_all_emails()
    if read_status == "unread":
        emails = [e for e in emails if not e["read"]]
    elif read_status == "read":
        emails = [e for e in emails if e["read"]]
    return json.dumps(emails[:min(max(max_emails, 1), 50)], indent=2)


@beta_tool
def get_email_details(email_id: str) -> str:
    """Get the full body of a specific email.

    Args:
        email_id: The unique ID of the email (from get_emails or get_thread).
    """
    body = _EMAIL_BODIES.get(email_id, "Email body not found.")
    return json.dumps({"id": email_id, "body": body, "attachments": []}, indent=2)


@beta_tool
def get_thread(thread_id: str) -> str:
    """Get all emails in a thread in chronological order.

    Args:
        thread_id: The thread ID (from get_emails results).
    """
    thread = sorted(
        [e for e in _get_all_emails() if e["thread_id"] == thread_id],
        key=lambda e: e["date"],
    )
    if not thread:
        return json.dumps({"error": f"No thread found with id {thread_id}"})
    return json.dumps(thread, indent=2)


# ---------------------------------------------------------------------------
# Calendar tools
# ---------------------------------------------------------------------------

@beta_tool
def get_upcoming_events(days_ahead: int = 7) -> str:
    """Get calendar events for the next N days.

    Args:
        days_ahead: Number of days to look ahead (1–30, default 7).
    """
    events = _events_in_range(min(max(days_ahead, 1), 30))
    return json.dumps(events, indent=2)


@beta_tool
def find_free_slots(date_str: str, duration_minutes: int = 60) -> str:
    """Find available time slots on a given date within working hours (9am–6pm).

    Args:
        date_str: Date to check in YYYY-MM-DD format.
        duration_minutes: Required slot length in minutes (default 60).
    """
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return json.dumps({"error": f"Invalid date format: {date_str}. Use YYYY-MM-DD."})
    slots = _free_slots_on(target, max(duration_minutes, 15))
    return json.dumps({"date": date_str, "free_slots": slots}, indent=2)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are a productivity assistant with access to both the inbox and calendar. "
    "You can see all emails (read and unread, recent and old) and upcoming events.\n\n"
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


class EmailCalendarAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def run(self, request: str) -> str:
        runner = self.client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=_SYSTEM,
            tools=[
                get_emails, get_email_details, get_thread,
                get_upcoming_events, find_free_slots,
            ],
            messages=[{"role": "user", "content": request}],
        )

        final_text = ""
        for message in runner:
            for block in message.content:
                if block.type == "text" and block.text:
                    print(block.text, end="", flush=True)
                    final_text = block.text

        print()
        return final_text
