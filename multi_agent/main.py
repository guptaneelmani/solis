#!/usr/bin/env python3
"""
Multi-agent system entry point.

Set ANTHROPIC_API_KEY in your environment before running:
    export ANTHROPIC_API_KEY=sk-ant-...
    python main.py
"""

from orchestrator import Orchestrator


def main() -> None:
    print("Multi-Agent System")
    print("Agents: code · email · research · travel")
    print("Type 'quit' to exit.\n")

    orchestrator = Orchestrator()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        print()
        orchestrator.route(user_input)
        print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    main()
