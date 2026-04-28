import anthropic

_SYSTEM = (
    "You are an expert software engineer. Write clean, well-structured, "
    "production-ready code with concise explanations. Support any language. "
    "When debugging, identify root causes clearly. When reviewing, be specific "
    "about improvements and why they matter."
)


class CodeAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def run(self, request: str) -> str:
        with self.client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=_SYSTEM,
            messages=[{"role": "user", "content": request}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            response = stream.get_final_message()

        print()
        return next((b.text for b in response.content if b.type == "text"), "")
