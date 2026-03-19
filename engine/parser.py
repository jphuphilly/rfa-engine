"""
Input parser for the RFA Engine.
Handles plain text, --file (markdown), and --url (fetch + extract).
"""

import re
from pathlib import Path


async def parse_input(
    text: str | None = None,
    file_path: str | None = None,
    url: str | None = None,
) -> str:
    """
    Resolve the idea input from one of three sources.
    Returns cleaned plain text suitable for the debate loop.
    Raises ValueError if no source is provided or content is empty.
    """
    if url:
        return await _fetch_url(url)
    if file_path:
        return _read_file(file_path)
    if text:
        return text.strip()
    raise ValueError("Provide an idea (text), --file, or --url.")


def _read_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"File is empty: {file_path}")
    return content


async def _fetch_url(url: str) -> str:
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise ImportError(
            "httpx and beautifulsoup4 are required for --url. "
            "Run: pip install httpx beautifulsoup4"
        ) from e

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; RFA-Engine/1.0; "
            "+https://github.com/rfa-engine/rfa-engine)"
        )
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove navigation, scripts, styles, footers
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # Prefer article/main content
    main = soup.find("article") or soup.find("main") or soup.find("body")
    raw = main.get_text(separator="\n") if main else soup.get_text(separator="\n")

    # Collapse whitespace
    lines = [line.strip() for line in raw.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r'\n{3,}', '\n\n', text)

    if not text.strip():
        raise ValueError(f"Could not extract readable content from: {url}")

    # Truncate to ~4000 chars to stay within reasonable token limits
    if len(text) > 4000:
        text = text[:4000] + "\n\n[Content truncated for length]"

    return text.strip()
