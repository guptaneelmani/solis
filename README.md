# SOLIS

A personal multi-agent AI assistant powered by Claude and Groq.
Three specialised agents, one orchestrator, one Telegram interface.

## Agents

| Agent | Model | Handles |
|---|---|---|
| **Code** | Claude Sonnet 4.6 | Writing, debugging, explaining, and reviewing code |
| **Productivity** | Groq Llama 3.3 70B | Emails, calendar, scheduling, deadlines, inbox management |
| **Research & Travel** | Claude Sonnet 4.6 | Research, fact-checking, travel planning, destination advice |

The **orchestrator** uses Claude Haiku 4.5 for fast, cheap request routing.

## Setup

```bash
git clone https://github.com/guptaneelmani/solis
cd solis/multi_agent
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...
export GROQ_API_KEY=gsk_...
```

## Run via CLI

```bash
python main.py
```

## Run via Telegram

1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token
2. Find your Telegram user ID via [@userinfobot](https://t.me/userinfobot)
3. Start the bot:

```bash
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_ALLOWED_IDS=123456789   # your Telegram user ID
python telegram_bot.py
```

`TELEGRAM_ALLOWED_IDS` accepts a comma-separated list — add family members when ready.

## Connecting real services

**Email / Calendar** — open `agents/email_calendar_agent.py` and replace `_build_emails()` and `_build_events()` with calls to your provider (Gmail API, Google Calendar, Microsoft Graph, IMAP, etc.).

**Research & Travel** — uses Anthropic's hosted web search out of the box. No extra setup needed.

## Project structure

```
multi_agent/
├── main.py                          # CLI entry point
├── telegram_bot.py                  # Telegram bot (polling)
├── orchestrator.py                  # Routes requests to the right agent
├── requirements.txt
└── agents/
    ├── code_agent.py
    ├── email_calendar_agent.py
    └── research_travel_agent.py
```
