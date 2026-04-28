from typing import Literal

import anthropic
from pydantic import BaseModel

from agents.code_agent import CodeAgent
from agents.email_calendar_agent import EmailCalendarAgent
from agents.research_travel_agent import ResearchTravelAgent


class _Route(BaseModel):
    agent: Literal["code", "productivity", "research"]


_ROUTING_SYSTEM = """You are a task router. Classify the user request into exactly one category:
- code: writing, debugging, explaining, or reviewing code
- productivity: emails, calendar, scheduling, meetings, deadlines, inbox management
- research: finding information, explaining topics, fact-checking, travel planning, destinations"""


class Orchestrator:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.agents: dict[str, CodeAgent | EmailCalendarAgent | ResearchTravelAgent] = {
            "code": CodeAgent(),
            "productivity": EmailCalendarAgent(),
            "research": ResearchTravelAgent(),
        }

    def route(self, user_input: str) -> str:
        response = self.client.messages.parse(
            model="claude-opus-4-7",
            max_tokens=64,
            output_config={"effort": "low"},
            system=_ROUTING_SYSTEM,
            messages=[{"role": "user", "content": user_input}],
            output_format=_Route,
        )
        agent_name = response.parsed_output.agent
        print(f"[→ {agent_name} agent]\n")
        return self.agents[agent_name].run(user_input)
