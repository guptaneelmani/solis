import anthropic

_SYSTEM = (
    "You are a research and travel specialist. Use web search to find accurate, "
    "up-to-date information.\n\n"
    "For research queries: synthesise findings into a clear, well-structured answer. "
    "Cite sources inline. If a topic is contested, present multiple perspectives.\n\n"
    "For travel queries: cover current flight options, accommodation, visa requirements, "
    "local tips, estimated costs, best time to visit, and any relevant advisories. "
    "Structure responses as: overview → key logistics → budget estimate → practical tips."
)

_TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]


class ResearchTravelAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def run(self, query: str) -> str:
        messages = [{"role": "user", "content": query}]

        for _ in range(5):  # guard against infinite pause_turn loops
            with self.client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                thinking={"type": "adaptive"},
                output_config={"effort": "medium"},
                system=_SYSTEM,
                tools=_TOOLS,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                response = stream.get_final_message()

            if response.stop_reason != "pause_turn":
                break

            # Server hit its tool-loop limit; re-send to continue
            messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response.content},
            ]

        print()
        return next((b.text for b in response.content if b.type == "text"), "")
