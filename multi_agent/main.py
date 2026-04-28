#!/usr/bin/env python3
"""SOLIS CLI — loads .env automatically, then starts the multi-agent loop."""

from dotenv import load_dotenv
load_dotenv()

from orchestrator import Orchestrator


def main() -> None:
    print("SOLIS")
    print("Agents: code · productivity · research & travel")
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
