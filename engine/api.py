"""
Async Claude API wrapper for the RFA Engine.
All calls go through call_claude(); streaming is used by default.
Token usage is accumulated per-session for cost estimation.
"""

import asyncio
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-6"

# Pricing per million tokens (claude-opus-4-6)
_INPUT_COST_PER_MTOK  = 15.00
_OUTPUT_COST_PER_MTOK = 75.00

_client: anthropic.AsyncAnthropic | None = None

# Session-level token accumulator
_total_input_tokens  = 0
_total_output_tokens = 0


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment or .env file")
        _client = anthropic.AsyncAnthropic(api_key=api_key)
    return _client


def reset_token_counter() -> None:
    global _total_input_tokens, _total_output_tokens
    _total_input_tokens = 0
    _total_output_tokens = 0


def get_token_usage() -> dict:
    """Return token counts and estimated cost for the current session."""
    input_cost  = (_total_input_tokens  / 1_000_000) * _INPUT_COST_PER_MTOK
    output_cost = (_total_output_tokens / 1_000_000) * _OUTPUT_COST_PER_MTOK
    return {
        "input_tokens":  _total_input_tokens,
        "output_tokens": _total_output_tokens,
        "total_tokens":  _total_input_tokens + _total_output_tokens,
        "estimated_cost_usd": round(input_cost + output_cost, 4),
    }


async def call_claude(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2048,
    _retries: int = 5,
) -> str:
    """
    Make a single async Claude API call and return the response text.
    Retries on overload/rate-limit errors with exponential backoff.
    Accumulates token usage for cost estimation.
    """
    global _total_input_tokens, _total_output_tokens

    client = get_client()
    delay = 8.0

    for attempt in range(_retries + 1):
        try:
            response = await client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            if response.usage:
                _total_input_tokens  += response.usage.input_tokens
                _total_output_tokens += response.usage.output_tokens

            text_blocks = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_blocks)

        except anthropic.APIStatusError as e:
            if e.status_code in (429, 500, 529) and attempt < _retries:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise
        except anthropic.APIConnectionError:
            if attempt < _retries:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise
