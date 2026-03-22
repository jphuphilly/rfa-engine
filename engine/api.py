"""
Async Claude API wrapper for the RFA Engine.
All calls go through call_claude(); uses the Claude CLI for auth.
Token usage tracking is approximate (CLI does not expose token counts).
"""

import asyncio
import shutil

MODEL = "claude-opus-4-6"

# Session-level token accumulator (approximate — CLI does not expose counts)
_total_input_tokens  = 0
_total_output_tokens = 0


def reset_token_counter() -> None:
    global _total_input_tokens, _total_output_tokens
    _total_input_tokens = 0
    _total_output_tokens = 0


def get_token_usage() -> dict:
    """Return token counts and estimated cost for the current session."""
    return {
        "input_tokens":  _total_input_tokens,
        "output_tokens": _total_output_tokens,
        "total_tokens":  _total_input_tokens + _total_output_tokens,
        "estimated_cost_usd": 0.0,  # not available via CLI
    }


async def call_claude(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2048,
    _retries: int = 5,
) -> str:
    """
    Make a single async Claude call via the Claude CLI and return the response text.
    Retries on transient failures with exponential backoff.
    """
    cli = shutil.which("claude") or "claude"
    delay = 8.0

    for attempt in range(_retries + 1):
        try:
            proc = await asyncio.create_subprocess_exec(
                cli,
                "--model", MODEL,
                "--system-prompt", system_prompt,
                "-p", user_message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            if proc.returncode != 0:
                err = stderr.decode().strip()
                if attempt < _retries:
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 60.0)
                    continue
                raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {err}")

            return stdout.decode().strip()

        except asyncio.TimeoutError:
            if attempt < _retries:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise RuntimeError("Claude CLI call timed out")
        except Exception:
            if attempt < _retries:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise
