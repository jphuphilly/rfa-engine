"""
Step 5 test: The Architect — run 6 critics in parallel, feed all
12 objections to the Architect, verify 6-output structure.
Run with: python test_step5.py
"""

import asyncio
import re
from engine.api import call_claude
from engine.templates import CRITIC_ROUND_1_TEMPLATE, ARCHITECT_TEMPLATE
from engine.state import RunState
import personas.customer as customer
import personas.hater as hater
import personas.builder as builder
import personas.vc as vc
import personas.growth as growth
import personas.indie as indie
import personas.architect as architect

SAMPLE_IDEA = "An app that helps men track daily habits with AI coaching"

CRITICS = [
    ("customer", customer.SYSTEM_PROMPT),
    ("hater",    hater.SYSTEM_PROMPT),
    ("builder",  builder.SYSTEM_PROMPT),
    ("vc",       vc.SYSTEM_PROMPT),
    ("growth",   growth.SYSTEM_PROMPT),
    ("indie",    indie.SYSTEM_PROMPT),
]

ARCHITECT_OUTPUT_MARKERS = [
    "WHAT I CHANGED",
    "WHAT I REFUSED",
    "TRADEOFFS",
    "OBJECTION STATUS",
    "REVISED IDEA",
    "NEXT BUILD PROMPT",
]


def parse_severities_and_scores(text: str) -> tuple[list[str], list[int]]:
    severities = re.findall(r'\[(FATAL|MAJOR|MINOR)\]', text)
    scores = re.findall(r'[Ss]core[:\s*]+(\d+)', text)
    scores = [int(s) for s in scores if 1 <= int(s) <= 10]
    return severities[:2], scores[:2]


def extract_revised_idea(architect_text: str) -> str:
    """Pull out the content under OUTPUT 5: THE REVISED IDEA."""
    markers = [
        r"(?:OUTPUT 5|REVISED IDEA)[:\s\-]+",
        r"(?:OUTPUT 6|NEXT BUILD PROMPT)[:\s\-]+",
    ]
    start = re.search(markers[0], architect_text, re.IGNORECASE)
    end = re.search(markers[1], architect_text, re.IGNORECASE)
    if start and end:
        return architect_text[start.end():end.start()].strip()
    if start:
        return architect_text[start.end():].strip()
    return architect_text


async def run_critic(persona: str, system_prompt: str, idea: str) -> tuple[str, str]:
    user_message = CRITIC_ROUND_1_TEMPLATE.format(current_idea=idea)
    response = await call_claude(system_prompt=system_prompt, user_message=user_message)
    return persona, response


async def main():
    state = RunState(idea=SAMPLE_IDEA, mode="idea", max_rounds=3)
    print(f"Run ID: {state.run_id}")
    print("=" * 60)

    # --- Round 1: critics in parallel ---
    print("Round 1: running 6 critics in parallel...")
    state.start_round(1)

    tasks = [run_critic(p, s, SAMPLE_IDEA) for p, s in CRITICS]
    results = await asyncio.gather(*tasks)

    critiques: dict[str, str] = {}
    for persona, critique in results:
        severities, scores = parse_severities_and_scores(critique)
        state.set_critique(persona, critique, scores, severities)
        critiques[persona] = critique
        tag_str = " ".join(f"[{s}:{sc}]" for s, sc in zip(severities, scores))
        print(f"  {persona:10s}  {tag_str}")

    print(f"\n  FATALs: {state.count_fatals()}  MAJORs: {state.count_majors()}  MINORs: {state.count_minors()}")

    # --- Architect ---
    print("\nRunning The Architect...")
    architect_message = ARCHITECT_TEMPLATE.format(
        current_idea=SAMPLE_IDEA,
        round_number=1,
        customer_critique=critiques["customer"],
        hater_critique=critiques["hater"],
        builder_critique=critiques["builder"],
        vc_critique=critiques["vc"],
        growth_critique=critiques["growth"],
        indie_critique=critiques["indie"],
    )

    architect_response = await call_claude(
        system_prompt=architect.SYSTEM_PROMPT,
        user_message=architect_message,
        max_tokens=4096,
    )

    revised_idea = extract_revised_idea(architect_response)
    state.set_architect(architect_response, revised_idea)

    # --- Verify 6 outputs present ---
    print("\nArchitect output verification:")
    for marker in ARCHITECT_OUTPUT_MARKERS:
        found = marker.upper() in architect_response.upper()
        status = "OK" if found else "MISSING"
        print(f"  [{status}] {marker}")

    print(f"\n{'=' * 60}")
    print("ARCHITECT OUTPUT:")
    print("=" * 60)
    print(architect_response)

    print(f"\n{'=' * 60}")
    print("REVISED IDEA (extracted):")
    print("=" * 60)
    print(revised_idea)

    print(f"\nState saved to: {state.file_path}")
    print(f"Total API calls: {state.to_dict['total_api_calls']}")


if __name__ == "__main__":
    asyncio.run(main())
