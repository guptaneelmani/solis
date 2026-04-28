"""
Email monitoring agent.

Mock email tools are provided out of the box so the agent works immediately.
To connect a real inbox, replace the bodies of _fetch_mock() and _fetch_details_mock()
with calls to your email provider (Gmail API, IMAP via imaplib, Microsoft Graph, etc.).
"""

import json
from datetime import datetime, timedelta
from typing import Literal

import anthropic
from anthropic import beta_tool

# ---------------------------------------------------------------------------
# Mock data — swap in real API calls here
# ---------------------------------------------------------------------------

_ALL_EMAILS = None  # built lazily so timedelta stays relative to runtime


def _build_emails() -> list[dict]:
    now = datetime.now()
    return [
        # --- recent, unread ---
        {
            "id": "e001",
            "thread_id": "t001",
            "from": "ceo@company.com",
            "subject": "URGENT: Board deck needs your slide by EOD",
            "date": (now - timedelta(hours=1)).isoformat(),
            "read": False,
            "preview": "Hi, I need your department slide for the board presentation. Please send by 5pm today.",
        },
        {
            "id": "e003",
            "thread_id": "t003",
            "from": "hr@company.com",
            "subject": "Action required: Complete annual compliance training",
            "date": (now - timedelta(days=5)).isoformat(),
            "read": False,
            "preview": "This is your third reminder. The deadline is this Friday.",
        },
        {
            "id": "e004",
            "thread_id": "t004",
            "from": "noreply@github.com",
            "subject": "PR review requested: fix/auth-token-expiry",
            "date": (now - timedelta(hours=4)).isoformat(),
            "read": False,
            "preview": "alice requested your review on pull request #142.",
        },
        # --- recent, read ---
        {
            "id": "e002",
            "thread_id": "t002",
            "from": "client@bigcorp.com",
            "subject": "Re: Proposal — still waiting for revised quote",
            "date": (now - timedelta(days=3)).isoformat(),
            "read": True,
            "preview": "Following up again on the revised pricing proposal we discussed last week...",
        },
        {
            "id": "e005",
            "thread_id": "t005",
            "from": "newsletter@techdigest.io",
            "subject": "This week in AI — April digest",
            "date": (now - timedelta(days=1)).isoformat(),
            "read": True,
            "preview": "Top stories: new model benchmarks, open-source releases, and regulatory updates...",
        },
        # --- older threads that may need closure ---
        {
            "id": "e006",
            "thread_id": "t006",
            "from": "vendor@supplierco.com",
            "subject": "Re: Contract renewal — awaiting your signature",
            "date": (now - timedelta(days=18)).isoformat(),
            "read": True,
            "preview": "We sent the updated contract two weeks ago. Could you confirm receipt and sign?",
        },
        {
            "id": "e007",
            "thread_id": "t007",
            "from": "alice@company.com",
            "subject": "Re: Q1 retrospective action items",
            "date": (now - timedelta(days=30)).isoformat(),
            "read": True,
            "preview": "Here are the 5 action items we agreed on. I'll follow up in a month on progress.",
        },
        {
            "id": "e008",
            "thread_id": "t008",
            "from": "recruiter@talentfirm.com",
            "subject": "Re: Senior engineer candidate — feedback requested",
            "date": (now - timedelta(days=14)).isoformat(),
            "read": True,
            "preview": "The candidate is still available. Are you ready to proceed to the offer stage?",
        },
        {
            "id": "e009",
            "thread_id": "t002",  # same thread as e002
            "from": "you@company.com",
            "subject": "Re: Proposal — still waiting for revised quote",
            "date": (now - timedelta(days=10)).isoformat(),
            "read": True,
            "preview": "Hi, I'll have the revised numbers to you by end of next week.",
        },
        {
            "id": "e010",
            "thread_id": "t009",
            "from": "bob@partnerorg.com",
            "subject": "Partnership proposal — next steps?",
            "date": (now - timedelta(days=45)).isoformat(),
            "read": True,
            "preview": "It's been a while since our last call. Would love to reconnect and discuss moving forward.",
        },
    ]


def _get_all_emails() -> list[dict]:
    global _ALL_EMAILS
    if _ALL_EMAILS is None:
        _ALL_EMAILS = _build_emails()
    return _ALL_EMAILS


def _fetch_mock(max_emails: int, read_status: str) -> list[dict]:
    emails = _get_all_emails()
    if read_status == "unread":
        emails = [e for e in emails if not e["read"]]
    elif read_status == "read":
        emails = [e for e in emails if e["read"]]
    return emails[:max_emails]


def _fetch_thread_mock(thread_id: str) -> list[dict]:
    return [e for e in _get_all_emails() if e["thread_id"] == thread_id]


def _fetch_details_mock(email_id: str) -> dict:
    bodies = {
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
    return {
        "id": email_id,
        "body": bodies.get(email_id, "Email body not found."),
        "attachments": [],
    }


# ---------------------------------------------------------------------------
# Tools (replace mock implementations above to connect a real inbox)
# ---------------------------------------------------------------------------

@beta_tool
def get_emails(max_emails: int = 20, read_status: str = "all") -> str:
    """Retrieve emails from the inbox.

    Args:
        max_emails: Maximum number of emails to retrieve (1–50, default 20).
        read_status: Filter by read status — "all" (default), "unread", or "read".
    """
    valid = {"all", "unread", "read"}
    if read_status not in valid:
        read_status = "all"
    emails = _fetch_mock(min(max(max_emails, 1), 50), read_status)
    return json.dumps(emails, indent=2)


@beta_tool
def get_email_details(email_id: str) -> str:
    """Get the full body of a specific email.

    Args:
        email_id: The unique ID of the email (from get_emails or get_thread).
    """
    return json.dumps(_fetch_details_mock(email_id), indent=2)


@beta_tool
def get_thread(thread_id: str) -> str:
    """Get all emails in a thread in chronological order.

    Args:
        thread_id: The thread ID (from get_emails results).
    """
    thread = sorted(_fetch_thread_mock(thread_id), key=lambda e: e["date"])
    if not thread:
        return json.dumps({"error": f"No thread found with id {thread_id}"})
    return json.dumps(thread, indent=2)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are an email assistant with full access to the inbox — read and unread, "
    "recent and old. Your job is to:\n"
    "1. Surface urgent or time-sensitive emails that need immediate action.\n"
    "2. Identify stale threads where a response or decision is overdue and the "
    "user needs to provide closure (reply, sign, approve, decline, etc.).\n"
    "3. Flag emails where the user made a commitment they have not yet fulfilled.\n"
    "Use get_thread to reconstruct context on older conversations before drawing "
    "conclusions. Present findings grouped by priority. Be concise."
)


class EmailAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def run(self, request: str) -> str:
        runner = self.client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=_SYSTEM,
            tools=[get_emails, get_email_details, get_thread],
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
