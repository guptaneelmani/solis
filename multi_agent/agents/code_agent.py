from groq import Groq

_SYSTEM = (
    "You are an expert software engineer. Write clean, well-structured, "
    "production-ready code with concise explanations. Support any language. "
    "When debugging, identify root causes clearly. When reviewing, be specific "
    "about improvements and why they matter."
)

_MODEL = "llama-3.3-70b-versatile"


class CodeAgent:
    def __init__(self):
        self.client = Groq()

    def run(self, request: str) -> str:
        response = self.client.chat.completions.create(
            model=_MODEL,
            max_tokens=8192,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": request},
            ],
        )
        result = response.choices[0].message.content or ""
        print(result)
        return result
