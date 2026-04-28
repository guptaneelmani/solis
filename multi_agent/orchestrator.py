import json
from typing import Literal

from groq import Groq
from pydantic import BaseModel

from agents.code_agent import CodeAgent
from agents.email_calendar_agent import EmailCalendarAgent
from agents.research_travel_agent import ResearchTravelAgent


class _Route(BaseModel):
    agent: Literal["code", "productivity", "research"]


_ROUTING_SYSTEM = """You are a task router. Classify the user request into exactly one category and respond with JSON only.

Categories:
- code: writing, debugging, explaining, or reviewing code
- productivity: emails, calendar, scheduling, meetings, deadlines, inbox management
- research: finding information, explaining topics, fact-checking, travel planning, destinations

Respond with exactly: {"agent": "<category>"}"""

_MODEL = "llama-3.3-70b-versatile"


class Orchestrator:
    def __init__(self):
        self.client = Groq()
        self.agents: dict[str, CodeAgent | EmailCalendarAgent | ResearchTravelAgent] = {
            "code": CodeAgent(),
            "productivity": EmailCalendarAgent(),
            "research": ResearchTravelAgent(),
        }

    def route(self, user_input: str) -> str:
        response = self.client.chat.completions.create(
            model=_MODEL,
            max_tokens=64,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _ROUTING_SYSTEM},
                {"role": "user", "content": user_input},
            ],
        )
        data = json.loads(response.choices[0].message.content)
        agent_name = _Route(**data).agent
        print(f"[→ {agent_name} agent]\n")
        return self.agents[agent_name].run(user_input)
