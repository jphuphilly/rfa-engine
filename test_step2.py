"""
Step 2+3 test: all 6 critics in parallel against a sample idea.
Run with: python test_step2.py
"""

import asyncio
from engine.api import call_claude
from engine.templates import CRITIC_ROUND_1_TEMPLATE
import personas.customer as customer
import personas.hater as hater
import personas.builder as builder
import personas.vc as vc
import personas.growth as growth
import personas.indie as indie

SAMPLE_IDEA = "An app that helps men track daily habits with AI coaching"

CRITICS = [
    ("THE CUSTOMER", customer.SYSTEM_PROMPT),
    ("THE HATER",    hater.SYSTEM_PROMPT),
    ("THE BUILDER",  builder.SYSTEM_PROMPT),
    ("THE VC",       vc.SYSTEM_PROMPT),
    ("THE GROWTH OPERATOR", growth.SYSTEM_PROMPT),
    ("THE INDIE",    indie.SYSTEM_PROMPT),
]


async def run_critic(name: str, system_prompt: str, idea: str) -> tuple[str, str]:
    user_message = CRITIC_ROUND_1_TEMPLATE.format(current_idea=idea)
    response = await call_claude(system_prompt=system_prompt, user_message=user_message)
    return name, response


async def main():
    print(f"Idea: {SAMPLE_IDEA}")
    print(f"Running {len(CRITICS)} critics in parallel...")
    print("=" * 60)

    tasks = [run_critic(name, prompt, SAMPLE_IDEA) for name, prompt in CRITICS]
    results = await asyncio.gather(*tasks)

    for name, response in results:
        print(f"\n{'=' * 60}")
        print(f"  {name}")
        print(f"{'=' * 60}")
        print(response)

    print(f"\n{'=' * 60}")
    print(f"  COMPLETE — {len(results)} critics, {len(results) * 2} objections")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
