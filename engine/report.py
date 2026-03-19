"""
Terminal output formatting for the RFA Engine.
Short mode (default): verdict + surviving risks + next build prompt + cost.
Verbose mode (--verbose): full debate panels per round.
Quick Strike mode: threat level + top 3 risks + quick build prompt.
"""

import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.rule import Rule

from engine.api import get_token_usage
from engine.loop import DebateResult
from engine.state import RunState

console = Console()

VERDICT_COLORS = {
    "BUILD": "bold green",
    "PIVOT": "bold yellow",
    "KILL":  "bold red",
}

SEVERITY_COLORS = {
    "FATAL": "bold red",
    "MAJOR": "yellow",
    "MINOR": "dim white",
}

THREAT_COLORS = {
    "GREEN":  "bold green",
    "YELLOW": "bold yellow",
    "RED":    "bold red",
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_next_build_prompt(state: RunState) -> str:
    """Pull the NEXT BUILD PROMPT from the most recent Architect output."""
    for round_num in range(state.round_number, 0, -1):
        round_data = state.get_round(round_num)
        architect_text = round_data.get("architect") or ""
        if not architect_text:
            continue
        match = re.search(r'OUTPUT 6[:\s\-]+', architect_text, re.IGNORECASE)
        if match:
            return architect_text[match.end():].strip()[:1200]
        match = re.search(r'NEXT BUILD PROMPT[:\s\-]+', architect_text, re.IGNORECASE)
        if match:
            return architect_text[match.end():].strip()[:1200]
    return "See state file for full debate."


def _extract_assumptions_brief(assumption_text: str) -> list[str]:
    """Extract top 2 assumption headlines for short report."""
    lines = []
    for match in re.finditer(
        r'ASSUMPTION \d+[:\s\-]+(.{20,120})', assumption_text, re.IGNORECASE
    ):
        line = match.group(1).strip().rstrip("*").strip()
        lines.append(line)
        if len(lines) >= 2:
            break
    if not lines:
        # Fallback: grab first 2 lines that start with "This assumes"
        for line in assumption_text.splitlines():
            line = line.strip()
            if line.lower().startswith("this assumes") and len(line) > 20:
                lines.append(line[:120])
                if len(lines) >= 2:
                    break
    return lines


def _surviving_risks_bullets(surviving_objections: str) -> list[tuple[str, str, str]]:
    """
    Parse surviving objections text into list of (severity, label, snippet).
    Returns up to 5 entries.
    """
    results = []
    pattern = re.compile(
        r'\[(FATAL|MAJOR|MINOR)\]\s+([A-Z][A-Z\s]+?)\s+\(Score (\d+)/10\)[:\s]+(.+?)(?=\n•|\Z)',
        re.DOTALL,
    )
    for m in pattern.finditer(surviving_objections):
        sev, persona, score, text = m.group(1), m.group(2).strip(), m.group(3), m.group(4).strip()
        snippet = text[:120].replace("\n", " ").rstrip(".")
        results.append((sev, f"{persona} ({score}/10)", snippet))
        if len(results) >= 5:
            break
    return results


# ------------------------------------------------------------------
# Short report (default)
# ------------------------------------------------------------------

def print_short_report(result: DebateResult) -> None:
    usage = get_token_usage()
    verdict_color = VERDICT_COLORS.get(result.verdict, "white")
    state = result.state
    data = state.to_dict

    console.print()
    console.rule("[bold]RFA ENGINE[/bold]", style="bright_blue")

    # Verdict
    verdict_text = Text(
        f"  VERDICT: {result.verdict} ({result.verdict_subtype})",
        style=verdict_color,
        justify="left",
    )
    console.print(Panel(verdict_text, box=box.DOUBLE, padding=(0, 1)))

    # Surviving risks
    risks = _surviving_risks_bullets(result.surviving_objections)
    if risks:
        console.print("\n  [bold]SURVIVING RISKS:[/bold]")
        for sev, label, snippet in risks:
            color = SEVERITY_COLORS.get(sev, "white")
            console.print(
                f"  [{color}]•[/{color}] {snippet} "
                f"[dim]({label})[/dim]"
            )
    else:
        console.print("\n  [green]No surviving risks — all objections resolved.[/green]")

    # Next build prompt
    build_prompt = _extract_next_build_prompt(state)
    if build_prompt:
        console.print("\n  [bold]NEXT BUILD PROMPT:[/bold]")
        console.print(Panel(
            build_prompt[:800],
            box=box.SIMPLE,
            padding=(0, 2),
        ))

    # Assumptions to test
    if result.assumption_test:
        assumptions = _extract_assumptions_brief(result.assumption_test)
        if assumptions:
            console.print("  [bold]ASSUMPTIONS TO TEST:[/bold]")
            for i, a in enumerate(assumptions, 1):
                console.print(f"  {i}. {a}")

    # Footer
    console.print()
    console.print(
        f"  [dim]Full debate: {state.file_path}[/dim]"
    )
    console.print(
        f"  [dim]Rounds: {len(data['rounds'])}  |  "
        f"API calls: {data['total_api_calls']}  |  "
        f"Est. cost: ~${usage['estimated_cost_usd']}[/dim]"
    )
    console.rule(style="bright_blue")
    console.print()


# ------------------------------------------------------------------
# Verbose report
# ------------------------------------------------------------------

def print_verbose_report(result: DebateResult) -> None:
    state = result.state
    data = state.to_dict

    console.print()
    console.rule("[bold]RFA ENGINE — FULL DEBATE[/bold]", style="bright_blue")
    console.print(f"  Idea: [italic]{data['input']['idea']}[/italic]\n")

    for round_data in data["rounds"]:
        rnum = round_data["round_number"]
        console.rule(f"[bold]ROUND {rnum}[/bold]", style="dim")

        # Critic panels
        for persona, critique in round_data.get("critiques", {}).items():
            sevs = round_data.get("severities", {}).get(persona, [])
            scores = round_data.get("scores", {}).get(persona, [])
            tag_str = "  ".join(
                f"[{SEVERITY_COLORS.get(s, 'white')}][{s}:{sc}][/{SEVERITY_COLORS.get(s, 'white')}]"
                for s, sc in zip(sevs, scores)
            )
            console.print(Panel(
                critique,
                title=f"[bold]{persona.upper()}[/bold]  {tag_str}",
                box=box.ROUNDED,
                padding=(1, 2),
            ))

        # Architect panel
        architect_text = round_data.get("architect") or ""
        if architect_text:
            console.print(Panel(
                architect_text,
                title="[bold cyan]THE ARCHITECT[/bold cyan]",
                box=box.ROUNDED,
                padding=(1, 2),
            ))

    # Final verdict
    print_short_report(result)


# ------------------------------------------------------------------
# Quick Strike report
# ------------------------------------------------------------------

def print_quick_strike_report(qs_result: dict) -> None:
    usage = get_token_usage()
    threat = qs_result["threat_level"]
    threat_color = THREAT_COLORS.get(threat, "white")

    console.print()
    console.rule("[bold]RFA ENGINE — QUICK STRIKE[/bold]", style="bright_blue")

    # Threat level
    console.print(Panel(
        Text(f"  THREAT LEVEL: {threat}", style=threat_color),
        box=box.DOUBLE,
        padding=(0, 1),
    ))

    # Full synthesis
    console.print("\n" + qs_result["synthesis"])

    # Footer
    console.print()
    console.print(
        f"  [dim]Elapsed: {qs_result['elapsed_seconds']}s  |  "
        f"Est. cost: ~${usage['estimated_cost_usd']}[/dim]"
    )
    console.rule(style="bright_blue")
    console.print()
