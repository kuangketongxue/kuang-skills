#!/usr/bin/env python3
"""Firecrawl Developer Index search skill script (Python stdlib only).

GET https://api.firecrawl.dev/v2/search/developer?query=<q>&k=10 (Bearer key read from env, auto-loaded).
Default output: one line per result: "id | url | title(or '(no title)') | passages首段[:150]".
Pass --raw to print the original JSON response instead.
Errors are reported as {"error": "...", "exit_code": 1} on stdout, exit 1, never a traceback.

Note: /v2/ path (different from Firecrawl v1). FIRECRAWL_API_KEY is sent as Bearer
for a higher rate limit; the script dies with a clear error if it is not set.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, NoReturn, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Force UTF-8 so Chinese/emoji never crash on Windows GBK terminals.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API_URL = "https://api.firecrawl.dev/v2/search/developer"


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
PRIMARY_KEY_ENV = "FIRECRAWL_API_KEY"
KEYS_ENV = "FIRECRAWL_API_KEYS"
DEFAULT_K = 10
REQUEST_TIMEOUT_SECONDS = 45
RETRY_COUNT = 1
RETRY_DELAY_SECONDS = 2


def _load_keys(primary_env: str, list_env: str) -> list[str]:
    """读 list_env（逗号分隔多个 key）；未设时回退 primary_env（单个）。去重保序。"""
    keys: list[str] = []
    for part in os.getenv(list_env, "").split(","):
        part = part.strip().strip('"').strip("'")
        if part and part not in keys:
            keys.append(part)
    if not keys:
        single = os.getenv(primary_env, "").strip().strip('"').strip("'")
        if single:
            keys.append(single)
    return keys


def _is_quota_error(code: int, body_text: str) -> bool:
    """402/429 必是额度或计费；403 带额度关键词才算（避免把 401 权限错当额度用）。"""
    if code in (402, 429):
        return True
    if code == 403:
        low = body_text.lower()
        return any(w in low for w in ("quota", "limit", "rate", "usage", "exceeded", "allowance", "plan"))
    return False


KEYS = _load_keys(PRIMARY_KEY_ENV, KEYS_ENV)  # 主用在前，额度用完自动切备用


def print_usage() -> None:
    print(
        "Usage:\n"
        '  python3 firecrawl-dev.py \'{"query":"claude code update failed npm registry"}\' [--raw]\n\n'
        "Parameters (JSON, first positional arg):\n"
        "  query    required, search query string (English works best)\n"
        "  k        optional, default 10, number of results\n\n"
        "Options:\n"
        "  --raw          print raw JSON response instead of formatted lines\n"
        "  -h, --help     show this help\n"
    )


def _redact(text: str) -> str:
    for key in KEYS:
        text = text.replace(key, "***")
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


def extract_passage(passages: Any) -> str:
    """passages may be list[{"text":...}], str, or None."""
    if passages is None:
        return ""
    if isinstance(passages, str):
        return passages
    if isinstance(passages, list) and passages:
        first = passages[0]
        if isinstance(first, dict):
            return str(first.get("text") or "")
        return str(first)
    return ""


def emit_formatted(body_text: str) -> None:
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        die("Non-JSON response from Firecrawl Developer API", body=body_text)
    if not isinstance(data, dict):
        die("Unexpected response shape (not an object)", body=body_text)
    items = data.get("results", data.get("data", []))
    if not isinstance(items, list):
        die("Unexpected 'results'/'data' shape (not a list)", body=body_text)
    for r in items:
        if not isinstance(r, dict):
            continue
        rid = str(r.get("id") or "")
        url = str(r.get("url") or "")
        title = r.get("title")
        title_str = str(title) if title else "(no title)"
        passage = extract_passage(r.get("passages"))[:150]
        print(f"{rid} | {url} | {title_str} | {passage}")


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
    raw_k = payload.get("k", DEFAULT_K)
    try:
        k = int(raw_k)
    except (TypeError, ValueError):
        k = DEFAULT_K
    k = max(1, k)
    return query, k


def request_dev(query: str, k: int) -> str:
    if not KEYS:
        die(f"missing {PRIMARY_KEY_ENV} / {KEYS_ENV} — set in ~/.claude/.secrets/web-search.env")
    params = urlencode({"query": query, "k": str(k)})
    url = f"{API_URL}?{params}"

    last_exc: Exception | None = None
    last_body: str = ""
    for key_idx, api_key in enumerate(KEYS):
        for attempt in range(RETRY_COUNT + 1):
            if attempt > 0:
                time.sleep(RETRY_DELAY_SECONDS)
            req = Request(url, method="GET", headers={"Authorization": f"Bearer {api_key}"})
            try:
                with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            except HTTPError as err:
                body_text = err.read().decode("utf-8", errors="replace")
                last_exc = err
                last_body = body_text
                # 额度/频率耗尽 → 切下一个 key；401 等客户端错误不重试。
                if _is_quota_error(err.code, body_text) and key_idx + 1 < len(KEYS):
                    break
                if 400 <= err.code < 500:
                    die(f"HTTP {err.code} from Firecrawl Developer API", body=body_text)
                continue
            except (URLError, TimeoutError) as err:
                last_exc = err
                continue
    die(
        f"Firecrawl Developer request failed across {len(KEYS)} key(s) after retries: {last_exc}"
        f" (last body: {last_body[:200]})",
        body=last_body,
    )


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
    query, k = parse_params(payload)
    body_text = request_dev(query, k)
    if raw_flag:
        emit_raw(body_text)
    else:
        emit_formatted(body_text)


if __name__ == "__main__":
    main()
