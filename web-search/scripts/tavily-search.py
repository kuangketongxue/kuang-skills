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
from typing import Any, Dict, NoReturn, Tuple
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
PRIMARY_KEY_ENV = "TAVILY_API_KEY"
KEYS_ENV = "TAVILY_API_KEYS"
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


class _QuotaExceeded(Exception):
    """当前 key 额度/频率耗尽，切换下一个 key 重试。"""

    def __init__(self, code: int, body_text: str) -> None:
        super().__init__(f"HTTP {code}")
        self.code = code
        self.body_text = body_text


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
    if not KEYS:
        die(f"missing {PRIMARY_KEY_ENV} / {KEYS_ENV} — set in ~/.claude/.secrets/web-search.env")

    last_exc: Exception | None = None
    last_body: str = ""
    for key_idx, api_key in enumerate(KEYS):
        # 对每个 key，最多 RETRY_COUNT+1 次普通重试
        for attempt in range(RETRY_COUNT + 1):
            if attempt > 0:
                time.sleep(RETRY_DELAY_SECONDS)
            body = json.dumps(
                {
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                },
                ensure_ascii=False,
            ).encode("utf-8")
            req = Request(
                API_URL,
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
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
                    die(f"HTTP {err.code} from Tavily API", body=body_text)
                continue
            except (URLError, TimeoutError) as err:
                last_exc = err
                continue
    die(
        f"Tavily request failed across {len(KEYS)} key(s) after retries: {last_exc}"
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
    query, max_results, search_depth = parse_params(payload)
    body_text = request_tavily(query, max_results, search_depth)
    if raw_flag:
        emit_raw(body_text)
    else:
        emit_formatted(body_text)


if __name__ == "__main__":
    main()
