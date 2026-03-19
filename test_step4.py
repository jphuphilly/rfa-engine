"""
Step 4 test: state tracking — run one parallel critic round,
save everything to JSON, verify structure.
Run with: python test_step4.py
"""

import asyncio
import json
from engine.api import call_claude
from engine.templates import CRITIC_ROUND_1_TEMPLATE
from engine.state import RunState
import personas.customer as customer
import personas.hater as hater
import personas.builder as builder
import personas.vc as vc
import personas.growth as growth
import personas.indie as indie

SAMPLE_IDEA = "An app that helps men track daily habits with AI coaching"

CRITICS = [
    ("customer", customer.SYSTEM_PROMPT),
    ("hater",    hater.SYSTEM_PROMPT),
    ("builder",  builder.SYSTEM_PROMPT),
    ("vc",       vc.SYSTEM_PROMPT),
    ("growth",   growth.SYSTEM_PROMPT),
    ("indie",    indie.SYSTEM_PROMPT),
]


def parse_severities_and_scores(text: str) -> tuple[list[str], list[int]]:
    """
    Quick regex-free parser to extract severity tags and scores from critique text.
    Looks for [FATAL], [MAJOR], [MINOR] and 'Score: N' or 'Score: N/10'.
    """
    import re
    severities = re.findall(r'\[(FATAL|MAJOR|MINOR)\]', text)
    scores = re.findall(r'[Ss]core[:\s*]+(\d+)', text)
    scores = [int(s) for s in scores if 1 <= int(s) <= 10]
    return severities[:2], scores[:2]


async def run_critic(persona: str, system_prompt: str, idea: str) -> tuple[str, str]:
    user_message = CRITIC_ROUND_1_TEMPLATE.format(current_idea=idea)
    response = await call_claude(system_prompt=system_prompt, user_message=user_message)
    return persona, response


async def main():
    state = RunState(idea=SAMPLE_IDEA, mode="idea", max_rounds=3)
    print(f"Run ID: {state.run_id}")
    print(f"State file: {state.file_path}")
    print(f"Running Round 1 ({len(CRITICS)} critics in parallel)...")

    state.start_round(1)

    tasks = [run_critic(p, s, SAMPLE_IDEA) for p, s in CRITICS]
    results = await asyncio.gather(*tasks)

    for persona, critique in results:
        severities, scores = parse_severities_and_scores(critique)
        state.set_critique(persona, critique, scores, severities)
        tag_str = " ".join(f"[{s}:{sc}]" for s, sc in zip(severities, scores))
        print(f"  {persona:10s}  {tag_str}")

    print(f"\nFATALs: {state.count_fatals()}  MAJORs: {state.count_majors()}  MINORs: {state.count_minors()}")

    # Verify JSON structure
    with open(state.file_path) as f:
        data = json.load(f)

    print(f"\nJSON structure check:")
    print(f"  run_id:          {data['run_id']}")
    print(f"  input.idea:      {data['input']['idea'][:50]}...")
    print(f"  rounds:          {len(data['rounds'])} round(s)")
    print(f"  round[0] keys:   {list(data['rounds'][0].keys())}")
    print(f"  total_api_calls: {data['total_api_calls']}")
    print(f"  critics stored:  {list(data['rounds'][0]['critiques'].keys())}")
    print(f"\nFull state saved to: {state.file_path}")


if __name__ == "__main__":
    asyncio.run(main())
