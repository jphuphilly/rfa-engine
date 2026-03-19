"""
Step 6 test: full 3-round debate loop on a sample idea.
Verifies: critics fire each round, Architect rewrites, exit conditions work,
idea evolves, verdict is produced.
Run with: python test_step6.py
"""

import asyncio
from engine.loop import run_debate

SAMPLE_IDEA = "An app that helps men track daily habits with AI coaching"


async def main():
    print("=" * 60)
    print("  RFA ENGINE — FULL DEBATE TEST")
    print("=" * 60)

    result = await run_debate(
        idea=SAMPLE_IDEA,
        mode="idea",
        max_rounds=3,
        amp_after=2,
    )

    print(f"\n{'=' * 60}")
    print(f"  VERDICT: {result.verdict} ({result.verdict_subtype})")
    print(f"  Exit reason: {result.exit_reason}")
    print(f"{'=' * 60}")

    print("\nFINAL IDEA:")
    print(result.final_idea[:800])
    if len(result.final_idea) > 800:
        print("  [truncated — full text in state file]")

    print("\nSURVIVING OBJECTIONS:")
    print(result.surviving_objections)

    state = result.state
    data = state.to_dict
    print(f"\nStats:")
    print(f"  Rounds completed:  {len(data['rounds'])}")
    print(f"  Total API calls:   {data['total_api_calls']}")
    print(f"  Amplification:     {data['amplification_triggered']}")
    print(f"  State file:        {state.file_path}")


if __name__ == "__main__":
    asyncio.run(main())
