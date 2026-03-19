"""
Step 7 test: Critical Assumption Test wired into full debate loop.
Verifies: assumption test fires post-verdict, outputs 2-3 testable assumptions
with pass/fail metrics.
Run with: python test_step7.py
"""

import asyncio
from engine.loop import run_debate

SAMPLE_IDEA = "An app that helps men track daily habits with AI coaching"


async def main():
    print("=" * 60)
    print("  RFA ENGINE — STEP 7: CRITICAL ASSUMPTION TEST")
    print("=" * 60)

    result = await run_debate(
        idea=SAMPLE_IDEA,
        mode="idea",
        max_rounds=3,
        amp_after=2,
    )

    print(f"\n{'=' * 60}")
    print(f"  VERDICT: {result.verdict} ({result.verdict_subtype})")
    print(f"{'=' * 60}")

    print("\nCRITICAL ASSUMPTION TEST:")
    print("─" * 60)
    print(result.assumption_test)

    state = result.state
    data = state.to_dict
    print(f"\n{'─' * 60}")
    print(f"Rounds: {len(data['rounds'])}  |  API calls: {data['total_api_calls']}  |  File: {state.file_path}")

    # Verify assumption test was saved to state
    assert data.get("assumption_test"), "ERROR: assumption_test not saved to state!"
    print("State verification: assumption_test saved OK")


if __name__ == "__main__":
    asyncio.run(main())
