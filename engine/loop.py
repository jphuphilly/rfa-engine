"""
Debate loop orchestration for the RFA Engine.
Runs critics → Architect → critics until an exit condition is met.
"""

import asyncio
import re
from dataclasses import dataclass

from engine.api import call_claude
from engine.state import RunState
from engine.templates import (
    CRITIC_ROUND_1_TEMPLATE,
    CRITIC_ROUND_N_TEMPLATE,
    ARCHITECT_TEMPLATE,
    ASSUMPTION_TEST_TEMPLATE,
)
import personas.customer as customer
import personas.hater as hater
import personas.builder as builder
import personas.vc as vc
import personas.growth as growth
import personas.indie as indie
import personas.architect as architect
import personas.assumption_test as assumption_test

# ------------------------------------------------------------------
# Panel definition
# ------------------------------------------------------------------

CRITICS = [
    ("customer", customer.SYSTEM_PROMPT),
    ("hater",    hater.SYSTEM_PROMPT),
    ("builder",  builder.SYSTEM_PROMPT),
    ("vc",       vc.SYSTEM_PROMPT),
    ("growth",   growth.SYSTEM_PROMPT),
    ("indie",    indie.SYSTEM_PROMPT),
]

CRITIC_LABELS = {
    "customer": "THE CUSTOMER",
    "hater":    "THE HATER",
    "builder":  "THE BUILDER",
    "vc":       "THE VC",
    "growth":   "THE GROWTH OPERATOR",
    "indie":    "THE INDIE",
}


# ------------------------------------------------------------------
# Result type
# ------------------------------------------------------------------

@dataclass
class DebateResult:
    verdict: str           # BUILD / PIVOT / KILL
    verdict_subtype: str   # e.g. "Segment", "Moatless", etc.
    exit_reason: str       # human-readable explanation
    final_idea: str
    surviving_objections: str
    assumption_test: str
    state: RunState


# ------------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------------

def parse_severities_and_scores(text: str) -> tuple[list[str], list[int]]:
    severities = re.findall(r'\[(FATAL|MAJOR|MINOR)\]', text)
    scores = re.findall(r'[Ss]core[:\s*]+(\d+)', text)
    scores = [int(s) for s in scores if 1 <= int(s) <= 10]
    return severities[:2], scores[:2]


def extract_section(text: str, start_marker: str, end_marker: str | None = None) -> str:
    """Extract text between two markers (case-insensitive)."""
    pattern = re.escape(start_marker)
    start = re.search(pattern, text, re.IGNORECASE)
    if not start:
        return ""
    if end_marker:
        end = re.search(re.escape(end_marker), text[start.end():], re.IGNORECASE)
        if end:
            return text[start.end(): start.end() + end.start()].strip()
    return text[start.end():].strip()


def extract_revised_idea(architect_text: str) -> str:
    """Pull the content under OUTPUT 5: THE REVISED IDEA."""
    result = extract_section(
        architect_text,
        "OUTPUT 5",
        "OUTPUT 6",
    )
    if result:
        return result
    # Fallback: try section header directly
    result = extract_section(architect_text, "REVISED IDEA", "NEXT BUILD PROMPT")
    return result or architect_text


def extract_architect_changes(architect_text: str) -> str:
    """Pull OUTPUT 1: WHAT I CHANGED AND WHY."""
    result = extract_section(architect_text, "OUTPUT 1", "OUTPUT 2")
    if result:
        return result
    return extract_section(architect_text, "WHAT I CHANGED", "WHAT I REFUSED")


def build_surviving_objections(state: RunState) -> str:
    """Format surviving objections from the final round for the report."""
    lines = []
    severities = state.get_all_severities()
    scores = state.get_all_scores()
    round_data = state.get_round(state.round_number)
    critiques = round_data.get("critiques", {})

    for persona, sevs in severities.items():
        persona_scores = scores.get(persona, [])
        for i, (sev, score) in enumerate(zip(sevs, persona_scores)):
            if sev in ("FATAL", "MAJOR"):
                # Extract the i-th objection text (rough heuristic)
                full_critique = critiques.get(persona, "")
                objection_blocks = re.split(r'\*?\*?Objection \d+\*?\*?', full_critique, flags=re.IGNORECASE)
                text = objection_blocks[i + 1].strip()[:300] if len(objection_blocks) > i + 1 else ""
                lines.append(f"• [{sev}] {CRITIC_LABELS.get(persona, persona)} (Score {score}/10): {text[:200]}...")

    return "\n".join(lines) if lines else "None — all objections resolved."


# ------------------------------------------------------------------
# Single-round helpers
# ------------------------------------------------------------------

async def _call_critic(
    persona: str,
    system_prompt: str,
    user_message: str,
) -> tuple[str, str]:
    response = await call_claude(system_prompt=system_prompt, user_message=user_message)
    return persona, response


async def run_critic_round(
    state: RunState,
    round_number: int,
    log_fn=print,
) -> dict[str, str]:
    """Run all 6 critics in parallel. Returns {persona: critique_text}."""
    current_idea = state.current_idea

    if round_number == 1:
        user_messages = {
            p: CRITIC_ROUND_1_TEMPLATE.format(current_idea=current_idea)
            for p, _ in CRITICS
        }
    else:
        prev_round = state.get_round(round_number - 1)
        architect_changes = extract_architect_changes(prev_round.get("architect", ""))
        user_messages = {}
        for persona, _ in CRITICS:
            prev_critique = prev_round["critiques"].get(persona, "")
            prev_sevs = prev_round["severities"].get(persona, [])
            prev_scores = prev_round["scores"].get(persona, [])
            prev_objections_fmt = prev_critique[:600] if prev_critique else "None recorded."
            prev_scores_fmt = ", ".join(str(s) for s in prev_scores) if prev_scores else "N/A"
            user_messages[persona] = CRITIC_ROUND_N_TEMPLATE.format(
                round_number=round_number,
                current_idea=current_idea,
                architect_changes=architect_changes,
                previous_objections=prev_objections_fmt,
                previous_scores=prev_scores_fmt,
            )

    async def _staggered_critic(persona: str, system_prompt: str, idx: int) -> tuple[str, str]:
        if idx > 0:
            await asyncio.sleep(idx * 0.3)
        return await _call_critic(persona, system_prompt, user_messages[persona])

    tasks = [
        _staggered_critic(p, s, i)
        for i, (p, s) in enumerate(CRITICS)
    ]
    results = await asyncio.gather(*tasks)

    critiques: dict[str, str] = {}
    for persona, critique in results:
        severities, scores = parse_severities_and_scores(critique)
        state.set_critique(persona, critique, scores, severities)
        critiques[persona] = critique
        tag_str = " ".join(f"[{s}:{sc}]" for s, sc in zip(severities, scores))
        log_fn(f"  {persona:10s}  {tag_str}")

    return critiques


async def run_architect_round(
    state: RunState,
    critiques: dict[str, str],
    round_number: int,
    amplification: bool = False,
) -> str:
    current_idea = state.current_idea
    architect_message = ARCHITECT_TEMPLATE.format(
        current_idea=current_idea,
        round_number=round_number,
        customer_critique=critiques.get("customer", ""),
        hater_critique=critiques.get("hater", ""),
        builder_critique=critiques.get("builder", ""),
        vc_critique=critiques.get("vc", ""),
        growth_critique=critiques.get("growth", ""),
        indie_critique=critiques.get("indie", ""),
    )
    system = (
        architect.AMPLIFICATION_SYSTEM_PROMPT
        if amplification
        else architect.SYSTEM_PROMPT
    )
    response = await call_claude(
        system_prompt=system,
        user_message=architect_message,
        max_tokens=4096,
    )
    revised_idea = extract_revised_idea(response)
    state.set_architect(response, revised_idea)
    return response


async def run_assumption_test(state: RunState, verdict: str, surviving_objections: str) -> str:
    """Run the Critical Assumption Test after the debate concludes."""
    message = ASSUMPTION_TEST_TEMPLATE.format(
        total_rounds=state.round_number,
        final_idea=state.current_idea,
        verdict=verdict,
        surviving_objections=surviving_objections,
    )
    response = await call_claude(
        system_prompt=assumption_test.SYSTEM_PROMPT,
        user_message=message,
        max_tokens=1024,
    )
    state.set_assumption_test(response)
    return response


# ------------------------------------------------------------------
# Exit condition checks
# ------------------------------------------------------------------

def _fatal_set(state: RunState, round_number: int) -> frozenset[str]:
    """Return a frozenset of (persona, index) for each FATAL in a given round."""
    fatals = set()
    round_data = state.get_round(round_number)
    for persona, sevs in round_data.get("severities", {}).items():
        for i, s in enumerate(sevs):
            if s == "FATAL":
                fatals.add(f"{persona}:{i}")
    return frozenset(fatals)


def check_exit_conditions(
    state: RunState,
    round_number: int,
    max_rounds: int,
    amp_after: int,
) -> tuple[bool, str, str, str]:
    """
    Returns (should_exit, verdict, verdict_subtype, exit_reason).
    Call AFTER the critic round scores are recorded (before Architect).
    """
    fatals = state.count_fatals()
    majors = state.count_majors()
    minors = state.count_minors()
    total = fatals + majors + minors

    # 1. All resolved
    if fatals == 0 and majors == 0:
        return True, "BUILD", "Clean", "All objections resolved."

    # 2. Dynamic stop: ≥70% MINOR, no new FATAL this round
    if total > 0 and (minors / total) >= 0.70 and fatals == 0:
        verdict = "BUILD" if majors <= 1 else "PIVOT"
        subtype = "Narrow" if verdict == "BUILD" else "Segment"
        return True, verdict, subtype, f"Dynamic stop: {minors}/{total} objections are MINOR, no FATALs."

    # 3. No progress: same FATAL survived 2 consecutive rounds
    if round_number >= 2:
        prev_fatals = _fatal_set(state, round_number - 1)
        curr_fatals = _fatal_set(state, round_number)
        stuck = prev_fatals & curr_fatals  # FATALs present in both rounds
        if stuck:
            return True, "KILL", "No-progress", (
                f"FATAL objection(s) unresolved across 2 consecutive rounds: {stuck}"
            )

    # 4. Max rounds hit
    if round_number >= max_rounds:
        if fatals > 0:
            verdict, subtype = "KILL", "Unresolved-FATAL"
        elif majors >= 2:
            verdict, subtype = "PIVOT", "Segment"
        elif majors == 1:
            verdict, subtype = "PIVOT", "Form-factor"
        else:
            verdict, subtype = "BUILD", "Experiment-heavy"
        return True, verdict, subtype, f"Max rounds ({max_rounds}) reached."

    # 5. Check amplification trigger (not an exit — caller uses this)
    # Handled by caller via should_amplify()

    return False, "", "", ""


def should_amplify(state: RunState, round_number: int, amp_after: int) -> bool:
    """True when amplification mode should kick in next round."""
    return (
        round_number >= amp_after
        and state.count_fatals() == 0
        and not state.to_dict.get("amplification_triggered", False)
    )


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------

async def run_debate(
    idea: str,
    mode: str = "idea",
    max_rounds: int = 3,
    amp_after: int = 2,
    log_fn=print,
) -> DebateResult:
    """
    Run the full RFA debate loop.

    Parameters
    ----------
    idea       : The raw idea text.
    mode       : 'idea' | 'feature' | 'positioning'
    max_rounds : Maximum debate rounds (default 3).
    amp_after  : Trigger amplification after this many rounds with 0 FATALs.
    log_fn     : Callable for progress output (default print).
    """
    state = RunState(idea=idea, mode=mode, max_rounds=max_rounds)
    log_fn(f"\nRun ID: {state.run_id}")
    log_fn(f"Mode: {mode}  |  Max rounds: {max_rounds}  |  Amp after: {amp_after}")

    amplification = False

    for round_number in range(1, max_rounds + 1):
        log_fn(f"\n{'─' * 50}")
        log_fn(f"ROUND {round_number}")
        log_fn(f"{'─' * 50}")

        state.start_round(round_number)

        # --- Critics ---
        log_fn("Critics:")
        critiques = await run_critic_round(state, round_number, log_fn=log_fn)
        log_fn(
            f"  → FATALs: {state.count_fatals()}  "
            f"MAJORs: {state.count_majors()}  "
            f"MINORs: {state.count_minors()}"
        )

        # --- Exit check (before Architect) ---
        should_exit, verdict, subtype, exit_reason = check_exit_conditions(
            state, round_number, max_rounds, amp_after
        )

        # --- Amplification check ---
        if not should_exit and should_amplify(state, round_number, amp_after):
            amplification = True
            state.set_amplification_triggered()
            log_fn("  → Amplification mode triggered.")

        if should_exit:
            log_fn(f"\nExit: {exit_reason}")
            log_fn(f"Verdict: {verdict} ({subtype})")
            surviving = build_surviving_objections(state)
            state.set_verdict(f"{verdict} ({subtype})", surviving)
            log_fn("\nRunning Critical Assumption Test...")
            assumption = await run_assumption_test(state, f"{verdict} ({subtype})", surviving)
            log_fn("  → Done.")
            return DebateResult(
                verdict=verdict,
                verdict_subtype=subtype,
                exit_reason=exit_reason,
                final_idea=state.current_idea,
                surviving_objections=surviving,
                assumption_test=assumption,
                state=state,
            )

        # --- Architect (not the last round, or amplification) ---
        log_fn(f"\nArchitect {'(AMPLIFICATION)' if amplification else ''}:")
        await run_architect_round(state, critiques, round_number, amplification)
        log_fn(f"  → Revised idea written.")

    # Should not reach here (max_rounds exit handles it), but safety net:
    surviving = build_surviving_objections(state)
    state.set_verdict("KILL (max-rounds-fallback)", surviving)
    assumption = await run_assumption_test(state, "KILL (max-rounds-fallback)", surviving)
    return DebateResult(
        verdict="KILL",
        verdict_subtype="max-rounds-fallback",
        exit_reason="Fell through loop — check exit logic.",
        final_idea=state.current_idea,
        surviving_objections=surviving,
        assumption_test=assumption,
        state=state,
    )
