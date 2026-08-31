#!/usr/bin/env python3
"""Tavily search skill script (Python stdlib only).

POST https://api.tavily.com/search (API key read from env, auto-loaded).
Default output: one line per result: "title | url | content[:200]".
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

API_URL = "https://api.tavily.com/search"


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
API_KEY = os.getenv("TAVILY_API_KEY", "")
SECRET = API_KEY  # redacted wherever it appears in output
REQUEST_TIMEOUT_SECONDS = 45
RETRY_COUNT = 1
RETRY_DELAY_SECONDS = 2


def print_usage() -> None:
    print(
        "Usage:\n"
        '  python3 tavily-search.py \'{"query":"Claude Code","max_results":5,"search_depth":"basic"}\' [--raw]\n\n'
        "Parameters (JSON, first positional arg):\n"
        "  query          required, search query string\n"
        "  max_results    optional, default 5, range 1-10\n"
        "  search_depth   optional, 'basic' (default) or 'advanced'\n\n"
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
        die("Non-JSON response from Tavily API", body=body_text)
    if not isinstance(data, dict):
        die("Unexpected response shape (not an object)", body=body_text)
    results = data.get("results", [])
    if not isinstance(results, list):
        die("Unexpected 'results' shape (not a list)", body=body_text)
    for r in results:
        if not isinstance(r, dict):
            continue
        title = str(r.get("title") or "")
        url = str(r.get("url") or "")
        content = str(r.get("content") or "")[:200]
        print(f"{title} | {url} | {content}")


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die("Invalid JSON payload")
    if not isinstance(data, dict):
        die("Invalid JSON payload (not an object)")
    return data


def parse_params(payload: Dict[str, Any]) -> Tuple[str, int, str]:
    query = payload.get("query") or payload.get("Query") or ""
    if not isinstance(query, str) or not query.strip():
        die("query is required")
    query = query.strip()
    raw_max = payload.get("max_results", 5)
    try:
        max_results = int(raw_max)
    except (TypeError, ValueError):
        max_results = 5
    max_results = max(1, min(10, max_results))
    depth = payload.get("search_depth", "basic")
    if not isinstance(depth, str) or depth.strip().lower() not in {"basic", "advanced"}:
        depth = "basic"
    depth = depth.strip().lower()
    return query, max_results, depth


def request_tavily(query: str, max_results: int, search_depth: str) -> str:
    if not API_KEY:
        die("missing TAVILY_API_KEY — set in ~/.claude/.secrets/web-search.env or TAVILY_API_KEY env var")
    body = json.dumps(
        {
            "api_key": API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    def build_req() -> Request:
        return Request(
            API_URL,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
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
            # 4xx client errors won't be fixed by retrying.
            if 400 <= err.code < 500:
                die(f"HTTP {err.code} from Tavily API", body=body_text)
            last_exc = err
            continue
        except (URLError, TimeoutError) as err:
            last_exc = err
            continue
    die(f"Tavily request failed after {RETRY_COUNT + 1} attempts: {last_exc}")


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
    query, max_results, search_depth = parse_params(payload)
    body_text = request_tavily(query, max_results, search_depth)
    if raw_flag:
        emit_raw(body_text)
    else:
        emit_formatted(body_text)


if __name__ == "__main__":
    main()
