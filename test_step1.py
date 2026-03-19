"""
Step 1 test: call The Customer with a sample idea.
Run with: python test_step1.py
"""

import asyncio
from engine.api import call_claude
from personas.customer import SYSTEM_PROMPT
from engine.api import MODEL

SAMPLE_IDEA = "An app that helps men track daily habits with AI coaching"

ROUND_1_TEMPLATE = """IDEA TO EVALUATE:

{current_idea}

---

This is Round 1. You are seeing this idea for the first time.
Provide your 2 most important objections with severity tags and
Skepticism Scores."""


async def main():
    print(f"Model: {MODEL}")
    print(f"Idea: {SAMPLE_IDEA}")
    print("-" * 60)

    user_message = ROUND_1_TEMPLATE.format(current_idea=SAMPLE_IDEA)
    response = await call_claude(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
    )

    print("THE CUSTOMER:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
