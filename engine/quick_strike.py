"""
Quick Strike mode: 6 critics in parallel, 1 objection each, synthesis brief.
Target: under 60 seconds wall-clock time.
"""

import asyncio
import re
import time

from engine.api import call_claude
from engine.templates import QUICK_STRIKE_INPUT_TEMPLATE, QUICK_STRIKE_SYNTHESIS_TEMPLATE, QUICK_STRIKE_SUFFIX
import personas.customer as customer
import personas.hater as hater
import personas.builder as builder
import personas.vc as vc
import personas.growth as growth
import personas.indie as indie
import personas.synthesis as synthesis

CRITICS = [
    ("customer", customer.SYSTEM_PROMPT),
    ("hater",    hater.SYSTEM_PROMPT),
    ("builder",  builder.SYSTEM_PROMPT),
    ("vc",       vc.SYSTEM_PROMPT),
    ("growth",   growth.SYSTEM_PROMPT),
    ("indie",    indie.SYSTEM_PROMPT),
]


def _qs_system(base_prompt: str) -> str:
    return base_prompt + "\n\n" + QUICK_STRIKE_SUFFIX


def parse_severity_and_score(text: str) -> tuple[str, int]:
    """Extract the single severity tag and score from a Quick Strike objection."""
    sev_match = re.search(r'\[(FATAL|MAJOR|MINOR)\]', text)
    score_match = re.search(r'[Ss]core[:\s*]+(\d+)', text)
    severity = sev_match.group(1) if sev_match else "MAJOR"
    score = int(score_match.group(1)) if score_match else 5
    return severity, min(max(score, 1), 10)


async def _call_critic(persona: str, system_prompt: str, idea: str) -> tuple[str, str]:
    user_message = QUICK_STRIKE_INPUT_TEMPLATE.format(current_idea=idea)
    response = await call_claude(
        system_prompt=_qs_system(system_prompt),
        user_message=user_message,
        max_tokens=256,
    )
    return persona, response


async def run_quick_strike(idea: str, log_fn=print) -> dict:
    """
    Run Quick Strike mode. Returns a result dict with objections, synthesis,
    threat level, and elapsed time.
    """
    t_start = time.monotonic()

    log_fn("Quick Strike: firing 6 critics...")
    tasks = [_call_critic(p, s, idea) for p, s in CRITICS]
    results = await asyncio.gather(*tasks)

    objections: dict[str, str] = {}
    severities: dict[str, str] = {}
    scores: dict[str, int] = {}

    for persona, response in results:
        objections[persona] = response
        sev, score = parse_severity_and_score(response)
        severities[persona] = sev
        scores[persona] = score
        log_fn(f"  {persona:10s}  [{sev}:{score}]")

    # Synthesis
    log_fn("Synthesizing...")
    synthesis_message = QUICK_STRIKE_SYNTHESIS_TEMPLATE.format(
        current_idea=idea,
        customer_objection=objections.get("customer", ""),
        hater_objection=objections.get("hater", ""),
        builder_objection=objections.get("builder", ""),
        vc_objection=objections.get("vc", ""),
        growth_objection=objections.get("growth", ""),
        indie_objection=objections.get("indie", ""),
    )
    synthesis_response = await call_claude(
        system_prompt=synthesis.SYSTEM_PROMPT,
        user_message=synthesis_message,
        max_tokens=512,
    )

    elapsed = time.monotonic() - t_start

    # Extract threat level
    threat_match = re.search(r'\b(GREEN|YELLOW|RED)\b', synthesis_response)
    threat_level = threat_match.group(1) if threat_match else "YELLOW"

    return {
        "idea": idea,
        "objections": objections,
        "severities": severities,
        "scores": scores,
        "synthesis": synthesis_response,
        "threat_level": threat_level,
        "elapsed_seconds": round(elapsed, 1),
    }
