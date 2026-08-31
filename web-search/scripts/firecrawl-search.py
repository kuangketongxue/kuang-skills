#!/usr/bin/env python3
"""Firecrawl search skill script (Python stdlib only).

POST https://api.firecrawl.dev/v1/search (Bearer key read from env, auto-loaded).
Default output: one line per result: "title | url | description[:200]".
Pass --raw to print the original JSON response instead.
Errors are reported as {"error": "...", "exit_code": 1} on stdout, exit 1, never a traceback.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Callable, Dict, NoReturn, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Force UTF-8 so Chinese/emoji never crash on Windows GBK terminals.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API_URL = "https://api.firecrawl.dev/v1/search"


def _load_env() -> None:
    """Load ~/.claude/.secrets/web-search.env so scripts work without an env prefix."""
    from pathlib import Path
    env_file = Path.home() / ".claude" / ".secrets" / "web-search.env"
    if not env_file.exists():
        return
    try:
        text = env_file.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()
API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
SECRET = API_KEY  # redacted wherever it appears in output
REQUEST_TIMEOUT_SECONDS = 45
RETRY_COUNT = 1
RETRY_DELAY_SECONDS = 2


def print_usage() -> None:
    print(
        "Usage:\n"
        '  python3 firecrawl-search.py \'{"query":"Claude Code","limit":5}\' [--raw]\n\n'
        "Parameters (JSON, first positional arg):\n"
        "  query    required, search query string\n"
        "  limit    optional, default 5\n\n"
        "Options:\n"
        "  --raw          print raw JSON response instead of formatted lines\n"
        "  -h, --help     show this help\n"
    )


def _redact(text: str) -> str:
    if SECRET:
        text = text.replace(SECRET, "***")
    return text


def die(message: str, *, body: Any = None) -> NoReturn:
    payload: Dict[str, Any] = {"error": _redact(message), "exit_code": 1}
    if body is not None:
        payload["body"] = _redact(str(body))
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(1)


def emit_raw(body_text: str) -> None:
    safe = _redact(body_text)
    sys.stdout.write(safe)
    if not safe.endswith("\n"):
        sys.stdout.write("\n")


def emit_formatted(body_text: str) -> None:
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        die("Non-JSON response from Firecrawl API", body=body_text)
    if not isinstance(data, dict):
        die("Unexpected response shape (not an object)", body=body_text)
    items = data.get("data", [])
    if not isinstance(items, list):
        die("Unexpected 'data' shape (not a list)", body=body_text)
    for r in items:
        if not isinstance(r, dict):
            continue
        title = str(r.get("title") or "")
        url = str(r.get("url") or "")
        description = str(r.get("description") or "")[:200]
        print(f"{title} | {url} | {description}")


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die("Invalid JSON payload")
    if not isinstance(data, dict):
        die("Invalid JSON payload (not an object)")
    return data


def parse_params(payload: Dict[str, Any]) -> Tuple[str, int]:
    query = payload.get("query") or payload.get("Query") or ""
    if not isinstance(query, str) or not query.strip():
        die("query is required")
    query = query.strip()
    raw_limit = payload.get("limit", 5)
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, limit)
    return query, limit


def request_firecrawl(query: str, limit: int) -> str:
    if not API_KEY:
        die("missing FIRECRAWL_API_KEY — set in ~/.claude/.secrets/web-search.env or FIRECRAWL_API_KEY env var")
    body = json.dumps(
        {"query": query, "limit": limit}, ensure_ascii=False
    ).encode("utf-8")

    def build_req() -> Request:
        return Request(
            API_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
        )

    return _request_with_retry(build_req)


def _request_with_retry(build_req: Callable[[], Request]) -> str:
    last_exc: Exception | None = None
    for attempt in range(RETRY_COUNT + 1):
        if attempt > 0:
            time.sleep(RETRY_DELAY_SECONDS)
        req = build_req()
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as err:
            body_text = err.read().decode("utf-8", errors="replace")
            if 400 <= err.code < 500:
                die(f"HTTP {err.code} from Firecrawl API", body=body_text)
            last_exc = err
            continue
        except (URLError, TimeoutError) as err:
            last_exc = err
            continue
    die(f"Firecrawl request failed after {RETRY_COUNT + 1} attempts: {last_exc}")


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in {"-h", "--help"}:
        print_usage()
        return
    if not args:
        print_usage()
        raise SystemExit(1)
    raw_flag = "--raw" in args
    json_arg = next((a for a in args if not a.startswith("-")), None)
    if json_arg is None:
        die("missing JSON payload argument")
    payload = parse_payload(json_arg)
    query, limit = parse_params(payload)
    body_text = request_firecrawl(query, limit)
    if raw_flag:
        emit_raw(body_text)
    else:
        emit_formatted(body_text)


if __name__ == "__main__":
    main()
