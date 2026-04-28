import json
import os

from groq import Groq
from tavily import TavilyClient

_SYSTEM = (
    "You are a research and travel specialist. Use the web_search tool to find accurate, "
    "up-to-date information.\n\n"
    "For research queries: synthesise findings into a clear, well-structured answer. "
    "Cite sources inline. If a topic is contested, present multiple perspectives.\n\n"
    "For travel queries: cover current flight options, accommodation, visa requirements, "
    "local tips, estimated costs, best time to visit, and any relevant advisories. "
    "Structure responses as: overview → key logistics → budget estimate → practical tips."
)

_MODEL = "llama-3.3-70b-versatile"

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information on any topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                },
                "required": ["query"],
            },
        },
    }
]


def _web_search(query: str) -> str:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    result = client.search(query=query, max_results=5)
    formatted = []
    for r in result.get("results", []):
        formatted.append(f"**{r['title']}**\n{r['url']}\n{r['content']}\n")
    return "\n---\n".join(formatted) if formatted else "No results found."


class ResearchTravelAgent:
    def __init__(self):
        self.client = Groq()

    def run(self, query: str) -> str:
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": query},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                tools=_TOOLS,
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
                tool_result = _web_search(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                })
