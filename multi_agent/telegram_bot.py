"""
SOLIS Telegram bot — polling mode.

Required env vars:
  TELEGRAM_BOT_TOKEN      — from @BotFather
  ANTHROPIC_API_KEY       — for orchestrator / Claude agents
  GROQ_API_KEY            — for email+calendar agent

Optional env vars:
  TELEGRAM_ALLOWED_IDS    — comma-separated Telegram user IDs allowed to use the bot
                            (leave unset to allow anyone; find your ID via @userinfobot)

Run:
  cd multi_agent
  python telegram_bot.py
"""

import os
import sys
import threading

import telebot

sys.path.insert(0, os.path.dirname(__file__))
from orchestrator import Orchestrator

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

_raw_ids = os.environ.get("TELEGRAM_ALLOWED_IDS", "").strip()
ALLOWED_IDS: set[int] = (
    {int(uid) for uid in _raw_ids.split(",") if uid.strip()}
    if _raw_ids else set()
)

# ---------------------------------------------------------------------------
# Bot + orchestrator
# ---------------------------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
orchestrator = Orchestrator()


def _keep_typing(chat_id: int, stop: threading.Event) -> None:
    """Send typing action every 4 s while the agent is working."""
    while not stop.is_set():
        bot.send_chat_action(chat_id, "typing")
        stop.wait(4)


def _send_long(chat_id: int, text: str, reply_to: int | None = None) -> None:
    """Send text, splitting into chunks if it exceeds Telegram's 4096-char limit."""
    limit = 4096
    chunks = [text[i : i + limit] for i in range(0, max(len(text), 1), limit)]
    for idx, chunk in enumerate(chunks):
        if idx == 0 and reply_to:
            bot.send_message(chat_id, chunk, reply_to_message_id=reply_to)
        else:
            bot.send_message(chat_id, chunk)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["start", "help"])
def handle_start(message):
    if ALLOWED_IDS and message.from_user.id not in ALLOWED_IDS:
        bot.reply_to(message, "You are not authorised to use this bot.")
        return
    bot.reply_to(
        message,
        "Hi! I'm SOLIS. Ask me anything — code help, emails, research, or travel.",
    )


@bot.message_handler(func=lambda _: True, content_types=["text"])
def handle_message(message):
    if ALLOWED_IDS and message.from_user.id not in ALLOWED_IDS:
        bot.reply_to(message, "You are not authorised to use this bot.")
        return

    stop = threading.Event()
    typing = threading.Thread(target=_keep_typing, args=(message.chat.id, stop), daemon=True)
    typing.start()

    try:
        response = orchestrator.route(message.text)
    except Exception as exc:
        response = f"Something went wrong: {exc}"
    finally:
        stop.set()
        typing.join()

    _send_long(message.chat.id, response or "Done.", reply_to=message.message_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("SOLIS is online. Ctrl+C to stop.")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
