#!/usr/bin/env python3
"""
RFA Engine — CLI entry point.
Usage: python rfa.py "your idea"   (or after install: rfa "your idea")
"""

import argparse
import asyncio
import sys

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rfa",
        description="RFA Engine — adversarial AI debate on any idea.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rfa "An app that tracks habits with AI coaching"
  rfa "my idea" --quick
  rfa --file pitch.md --verbose
  rfa --url https://example.com --rounds 2
  rfa "feature idea" --mode feature --amp-after 1
        """,
    )

    # Idea input (mutually exclusive)
    input_group = p.add_mutually_exclusive_group()
    input_group.add_argument(
        "idea",
        nargs="?",
        metavar="IDEA",
        help="Idea text (wrap in quotes)",
    )
    input_group.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Read idea from a markdown or text file",
    )
    input_group.add_argument(
        "--url", "-u",
        metavar="URL",
        help="Fetch and extract idea from a URL",
    )

    # Mode flags
    p.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick Strike mode: 1 objection per critic, ~60 seconds",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full debate in terminal (default: short summary only)",
    )

    # Debate parameters
    p.add_argument(
        "--rounds", "-r",
        type=int,
        default=3,
        metavar="N",
        help="Max debate rounds (default: 3)",
    )
    p.add_argument(
        "--mode", "-m",
        choices=["idea", "feature", "positioning"],
        default="idea",
        help="Debate preset (default: idea)",
    )
    p.add_argument(
        "--amp-after",
        type=int,
        default=None,
        metavar="N",
        help="Trigger amplification after N rounds with 0 FATALs (default: 2 for idea, 1 for feature/positioning)",
    )

    return p


def _resolve_amp_after(args: argparse.Namespace) -> int:
    if args.amp_after is not None:
        return args.amp_after
    if args.mode in ("feature", "positioning"):
        return 1
    return 2


async def _run(args: argparse.Namespace) -> None:
    from engine.parser import parse_input
    from engine.api import reset_token_counter

    reset_token_counter()

    # Resolve idea text
    try:
        idea = await parse_input(
            text=args.idea,
            file_path=args.file,
            url=args.url,
        )
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if not idea:
        console.print("[red]Error:[/red] No idea provided. Run `rfa --help` for usage.")
        sys.exit(1)

    if args.quick:
        await _run_quick_strike(idea, args)
    else:
        await _run_full(idea, args)


async def _run_quick_strike(idea: str, args: argparse.Namespace) -> None:
    from engine.quick_strike import run_quick_strike
    from engine.report import print_quick_strike_report

    console.print(f"\n[dim]Idea: {idea[:80]}{'...' if len(idea) > 80 else ''}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Running Quick Strike...", total=None)
        result = await run_quick_strike(idea, log_fn=lambda _: None)
        progress.remove_task(task)

    print_quick_strike_report(result)


async def _run_full(idea: str, args: argparse.Namespace) -> None:
    from engine.loop import run_debate
    from engine.report import print_short_report, print_verbose_report

    amp_after = _resolve_amp_after(args)

    console.print(
        f"\n[dim]Idea: {idea[:80]}{'...' if len(idea) > 80 else ''}[/dim]"
    )
    console.print(
        f"[dim]Mode: {args.mode}  |  Max rounds: {args.rounds}  |  Amp after: {amp_after}[/dim]\n"
    )

    log_lines = []

    def _log(msg: str) -> None:
        log_lines.append(msg)
        if args.verbose:
            console.print(msg)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=not args.verbose,
        console=console,
    ) as progress:
        task = progress.add_task("Debating...", total=None) if not args.verbose else None

        result = await run_debate(
            idea=idea,
            mode=args.mode,
            max_rounds=args.rounds,
            amp_after=amp_after,
            log_fn=_log,
        )

        if task is not None:
            progress.remove_task(task)

    if args.verbose:
        print_verbose_report(result)
    else:
        print_short_report(result)

    # OVERRIDE prompt if FATALs survive
    if result.verdict == "KILL" and "FATAL" in result.surviving_objections:
        console.print(
            "[bold red]⚠  FATAL objections survived. "
            "Type OVERRIDE to proceed anyway, or press Enter to exit:[/bold red] ",
            end="",
        )
        try:
            answer = input().strip()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer != "OVERRIDE":
            console.print("[dim]Exiting. Revise your idea and try again.[/dim]")
            sys.exit(0)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not any([args.idea, args.file, args.url]):
        parser.print_help()
        sys.exit(1)

    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
