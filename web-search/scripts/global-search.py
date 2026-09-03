#!/usr/bin/env python3
"""Global search skill script (Python stdlib only)."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, NoReturn
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Force UTF-8 so Chinese/emoji never crash on Windows GBK terminals.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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


DEFAULT_BASE_URL = "https://developer.zhihu.com"
# 20s（原 5s）：与 zhihu-search.py 同源同网络环境，5s 在国内网络下极易超时；
# 全网是中文查询的默认引擎之一（SKILL.md「铁律：默认并行带知乎」）。
REQUEST_TIMEOUT_SECONDS = 20
RETRY_COUNT = 1
RETRY_DELAY_SECONDS = 2


def print_usage() -> None:
    print(
        "Usage:\n"
        "  python3 global-search.py "
        '\'{"query":"如何理解 rave 文化","count":8,"filter":"host==\\"example.com\\"","search_db":"all"}\'\n\n'
        "Environment:\n"
        "  ZHIHU_ACCESS_SECRET      Bearer auth token\n"
        "  ZHIHU_OPENAPI_BASE_URL   Optional, default https://developer.zhihu.com\n"
        "  ZHIHU_GLOBAL_SEARCH_URL  Optional full endpoint override\n"
    )


def die(message: str, *, body: Any | None = None) -> NoReturn:
    payload: Dict[str, Any] = {"error": message, "exit_code": 1}
    if body is not None:
        payload["body"] = body
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(1)


def emit_raw(body_text: str) -> None:
    secret = os.getenv("ZHIHU_ACCESS_SECRET", "")
    if secret:
        body_text = body_text.replace(secret, "***")
    sys.stdout.write(body_text)
    if not body_text.endswith("\n"):
        sys.stdout.write("\n")


def emit_formatted(body_text: str) -> None:
    """Default: one line per item: "Title | Url | ContentText[:200]"."""
    secret = os.getenv("ZHIHU_ACCESS_SECRET", "")
    if secret:
        body_text = body_text.replace(secret, "***")
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        die("Non-JSON response from API")
    if not isinstance(data, dict):
        die("Unexpected response shape (not an object)")
    items = (data.get("Data") or {}).get("Items") or []
    if not isinstance(items, list):
        items = []
    for i in items:
        if not isinstance(i, dict):
            continue
        title = str(i.get("Title") or "")
        url = str(i.get("Url") or "")
        content = str(i.get("ContentText") or "")[:200]
        print(f"{title} | {url} | {content}")


def die_http(err: HTTPError) -> NoReturn:
    body_text = err.read().decode("utf-8", errors="replace")
    if body_text:
        emit_raw(body_text)
        raise SystemExit(1)
    die(f"HTTP {err.code}")


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die("Invalid JSON payload")
    if not isinstance(data, dict):
        die("Invalid JSON payload")
    return data


def parse_query(payload: Dict[str, Any]) -> str:
    query = payload.get("query") or payload.get("Query") or ""
    if not isinstance(query, str) or not query.strip():
        die("query is required")
    query = query.strip()
    return query


def parse_count(payload: Dict[str, Any]) -> int:
    raw = payload.get("count", payload.get("Count", 10))
    try:
        count = int(raw)
    except (TypeError, ValueError):
        count = 10
    return max(1, min(20, count))


def parse_filter(payload: Dict[str, Any]) -> str:
    raw = payload.get("filter", payload.get("Filter", ""))
    if raw is None:
        return ""
    if not isinstance(raw, str):
        die("filter must be a string")
    return raw.strip()


def parse_search_db(payload: Dict[str, Any]) -> str:
    raw = payload.get("search_db", payload.get("SearchDB", ""))
    if raw is None:
        return ""
    if not isinstance(raw, str):
        die("search_db must be a string")
    value = raw.strip().lower()
    if value and value not in {"all", "realtime", "static"}:
        die("search_db must be one of all, realtime, static")
    return value


def get_endpoint() -> str:
    explicit = os.getenv("ZHIHU_GLOBAL_SEARCH_URL", "").strip()
    if explicit:
        return explicit
    base_url = os.getenv("ZHIHU_OPENAPI_BASE_URL", DEFAULT_BASE_URL).strip()
    return f"{base_url.rstrip('/')}/api/v1/content/global_search"


def request_global_search(query: str, count: int, filter_expr: str, search_db: str) -> str:
    secret = os.getenv("ZHIHU_ACCESS_SECRET", "").strip()
    if not secret:
        die("Set ZHIHU_ACCESS_SECRET first (Bearer auth only)")

    params_dict = {"Query": query, "Count": str(count)}
    if filter_expr:
        params_dict["Filter"] = filter_expr
    if search_db:
        params_dict["SearchDB"] = search_db
    params = urlencode(params_dict)
    url = f"{get_endpoint()}?{params}"

    last_exc: Exception | None = None
    for attempt in range(RETRY_COUNT + 1):
        if attempt > 0:
            time.sleep(RETRY_DELAY_SECONDS)
        # 每次尝试都重建 Request：X-Request-Timestamp 必须是当前时间，
        # 沿用旧时间戳会让重试请求被服务端判为过期，重试就白试了。
        req = Request(
            url=url,
            method="GET",
            headers={
                "Authorization": f"Bearer {secret}",
                "X-Request-Timestamp": str(int(time.time())),
            },
        )
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                body_text = resp.read().decode("utf-8", errors="replace")
            break
        except HTTPError as err:
            # 5xx 服务端错误值得重试一次；4xx（401 鉴权 / 429 频控）重试无益，直接报。
            if err.code >= 500 and attempt < RETRY_COUNT:
                err.read()
                last_exc = err
                continue
            die_http(err)
        except (URLError, TimeoutError) as err:
            last_exc = err
            continue
    else:
        die(f"Global search request failed after {RETRY_COUNT + 1} attempt(s): {last_exc}")

    try:
        json.loads(body_text)
    except json.JSONDecodeError:
        die("Non-JSON response from API")
    return body_text


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
    query = parse_query(payload)
    count = parse_count(payload)
    filter_expr = parse_filter(payload)
    search_db = parse_search_db(payload)

    body_text = request_global_search(query, count, filter_expr, search_db)
    if raw_flag:
        emit_raw(body_text)
    else:
        emit_formatted(body_text)


if __name__ == "__main__":
    main()
