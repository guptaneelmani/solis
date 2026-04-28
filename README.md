# SOLIS

A multi-agent system powered by Claude. Three specialised agents, one orchestrator.

## Agents

| Agent | Handles |
|---|---|
| **Code** | Writing, debugging, explaining, and reviewing code |
| **Productivity** | Emails, calendar, scheduling, deadlines, and inbox management |
| **Research & Travel** | Research, fact-checking, travel planning, and destination advice |

## Setup

```bash
cd multi_agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python main.py
```

## Connecting real services

**Email / Calendar** — open `agents/email_calendar_agent.py` and replace the `_build_emails()` and `_build_events()` functions with calls to your provider (Gmail API, Google Calendar, Microsoft Graph, IMAP, etc.).

**Research & Travel** — uses Anthropic's hosted web search out of the box. No additional setup needed.

## Project structure

```
multi_agent/
├── main.py                          # CLI entry point
├── orchestrator.py                  # Routes requests to the right agent
├── requirements.txt
└── agents/
    ├── code_agent.py
    ├── email_calendar_agent.py
    └── research_travel_agent.py
```
