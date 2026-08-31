#!/usr/bin/env python3
"""Exa search skill script (Python stdlib only, no exa-py SDK needed).

POST https://api.exa.ai/search (API key from env, auto-loaded, sent as x-api-key header).
Default output: one line per result: "title | url | highlights首段[:200]".
When the response carries a synthesized `output.content` (outputSchema/deep mode),
it is appended after the results block so nothing is lost.
Pass --raw to print the original JSON response instead.
Errors are reported as {"error": "...", "exit_code": 1} on stdout, exit 1, never a traceback.

Canonical reference: https://docs.exa.ai/reference/search-api-guide-for-coding-agents
If anything here contradicts real API behavior, fetch that URL — it is the source of truth.
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

API_URL = "https://api.exa.ai/search"

# type -> timeout. deep variants can take much longer than auto/fast.
TYPE_TIMEOUTS = {
    "instant": 15,
    "fast": 30,
    "auto": 45,
    "deep-lite": 60,
    "deep": 90,
    "deep-reasoning": 120,
}
DEFAULT_TIMEOUT = 45
VALID_TYPES = set(TYPE_TIMEOUTS)


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
API_KEY = os.getenv("EXA_API_KEY", "")
SECRET = API_KEY  # redacted wherever it appears in output
RETRY_COUNT = 1
RETRY_DELAY_SECONDS = 2


def print_usage() -> None:
    print(
        "Usage:\n"
        '  python3 exa-search.py \'{"query":"recent AI safety papers","numResults":5}\' [--raw]\n\n'
        "Parameters (JSON, first positional arg):\n"
        "  query            required, search query string\n"
        "  type             optional, default 'auto'. One of:\n"
        "                     instant | fast | auto | deep-lite | deep | deep-reasoning\n"
        "                   (auto=balanced, deep/deep-reasoning=multi-step synthesis, slower)\n"
        "  numResults       optional, default 5, range 1-10\n"
        "  contents         optional, default {\"highlights\": true}.\n"
        "                     {\"highlights\": true}   query-relevant excerpts (token-efficient, default)\n"
        "                     {\"text\": {\"maxCharacters\": 20000}}  full page content\n"
        "                     {\"summary\": true}       per-result LLM summary\n"
        "  includeDomains   optional, list[str] e.g. ['arxiv.org','github.com']\n"
        "  excludeDomains   optional, list[str]\n"
        "  maxAgeHours      optional, cache-freshness cap. 0=always livecrawl, omit=default\n"
        "  systemPrompt     optional, source/synthesis guidance (pairs with outputSchema)\n"
        "  outputSchema     optional, JSON schema -> Exa returns synthesized output.content\n"
        "                     (do NOT add citation/confidence fields; grounding is automatic)\n\n"
        "Options:\n"
        "  --raw            print raw JSON response instead of formatted lines\n"
        "  -h, --help       show this help\n"
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


def _first_highlight(hl: Any) -> str:
    """highlights may be a list[str], a str, None, or list[dict] — take the first usable chunk."""
    if not hl:
        return ""
    if isinstance(hl, str):
        return hl
    if isinstance(hl, list):
        for item in hl:
            if isinstance(item, str) and item.strip():
                return item
            if isinstance(item, dict):
                t = item.get("text") or item.get("content")
                if isinstance(t, str) and t.strip():
                    return t
    return ""


def emit_formatted(body_text: str) -> None:
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        die("Non-JSON response from Exa API", body=body_text)
    if not isinstance(data, dict):
        die("Unexpected response shape (not an object)", body=body_text)

    results = data.get("results", [])
    if isinstance(results, list):
        for r in results:
            if not isinstance(r, dict):
                continue
            title = str(r.get("title") or "(no title)")
            url = str(r.get("url") or "")
            hl = _first_highlight(r.get("highlights"))
            text = str(r.get("text") or "")  # present when contents.text requested
            excerpt = hl or text
            print(f"{title} | {url} | {excerpt[:200]}")

    # Synthesized output (outputSchema / deep modes). Print after results so it's not lost.
    output = data.get("output")
    if isinstance(output, dict) and output.get("content") is not None:
        print("--- synthesized output ---")
        content = output["content"]
        if isinstance(content, (dict, list)):
            print(json.dumps(content, ensure_ascii=False, indent=2))
        else:
            print(str(content))

    if not results and not output:
        print("(no results and no synthesized output — use --raw to inspect the full response)")


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die("Invalid JSON payload")
    if not isinstance(data, dict):
        die("Invalid JSON payload (not an object)")
    return data


def parse_params(payload: Dict[str, Any]) -> Tuple[str, str, int, Dict[str, Any]]:
    query = payload.get("query") or payload.get("Query") or ""
    if not isinstance(query, str) or not query.strip():
        die("query is required")
    query = query.strip()

    search_type = payload.get("type", "auto")
    if not isinstance(search_type, str):
        search_type = "auto"
    search_type = search_type.strip().lower()
    if search_type not in VALID_TYPES:
        die(
            f"invalid type '{search_type}' — choose one of: {', '.join(sorted(VALID_TYPES))}"
        )

    raw_num = payload.get("numResults", payload.get("num_results", 5))
    try:
        num_results = int(raw_num)
    except (TypeError, ValueError):
        num_results = 5
    num_results = max(1, min(10, num_results))

    # contents: default to highlights. Allow user override (text/summary/highlights combos).
    contents = payload.get("contents")
    if contents is None:
        contents = {"highlights": True}

    return query, search_type, num_results, contents


def build_request_body(
    query: str,
    search_type: str,
    num_results: int,
    contents: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Assemble the Exa /search body. Known fields are normalized; extras are passed through."""
    body: Dict[str, Any] = {
        "query": query,
        "type": search_type,
        "numResults": num_results,
        "contents": contents,
    }
    # Optional pass-through fields (only included when the user supplied them).
    for key in (
        "includeDomains",
        "excludeDomains",
        "maxAgeHours",
        "systemPrompt",
        "system_prompt",
        "outputSchema",
        "output_schema",
        "additionalQueries",
        "category",
    ):
        if key in payload:
            # normalize snake_case -> camelCase for the two that need it
            camel = key.replace("_", "", 1) if key in {"system_prompt", "output_schema"} else key
            body[camel] = payload[key]
    return body


def request_exa(body_dict: Dict[str, Any], search_type: str) -> str:
    if not API_KEY:
        die("missing EXA_API_KEY — set in ~/.claude/.secrets/web-search.env or EXA_API_KEY env var")
    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")

    timeout = TYPE_TIMEOUTS.get(search_type, DEFAULT_TIMEOUT)

    def build_req() -> Request:
        return Request(
            API_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
            },
        )

    return _request_with_retry(build_req, timeout)


def _request_with_retry(build_req: Callable[[], Request], timeout: int) -> str:
    last_exc: Exception | None = None
    for attempt in range(RETRY_COUNT + 1):
        if attempt > 0:
            time.sleep(RETRY_DELAY_SECONDS)
        req = build_req()
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as err:
            body_text = err.read().decode("utf-8", errors="replace")
            # 4xx client errors won't be fixed by retrying.
            if 400 <= err.code < 500:
                die(f"HTTP {err.code} from Exa API", body=body_text)
            last_exc = err
            continue
        except (URLError, TimeoutError) as err:
            last_exc = err
            continue
    die(f"Exa request failed after {RETRY_COUNT + 1} attempts: {last_exc}")


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
    query, search_type, num_results, contents = parse_params(payload)
    body_dict = build_request_body(query, search_type, num_results, contents, payload)
    body_text = request_exa(body_dict, search_type)
    if raw_flag:
        emit_raw(body_text)
    else:
        emit_formatted(body_text)


if __name__ == "__main__":
    main()
