#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wiki_fts.py — 本地检索助手（BM25，SQLite FTS5）

用途：在 200+ 条笔记里定位关键词 / 【编号】 / 疑似冲突，避免靠 grep 瞎撞。
先跑 `python scripts/fetch_kb.py --index` 建索引（落在 temp，**不落盘**——
索引含全文 body，属原文副本范畴，必须随 --clean 一起清零）。

用法：
  python wiki_fts.py search "抄底"          # BM25 检索，默认 10 条
  python wiki_fts.py search "【1113】" -n 5
  python wiki_fts.py search "抄底" --full   # 打印完整段落而非摘要
"""

from __future__ import annotations

import argparse
import glob
import os
import sqlite3
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def resolve_db() -> str | None:
    """索引在 temp 里（不落盘），取最新的那个。"""
    cands = sorted(glob.glob(os.path.join(tempfile.gettempdir(), "debate_kb_*", "fts.sqlite")))
    return cands[-1] if cands else None


def connect(db: str) -> sqlite3.Connection:
    return sqlite3.connect(db)


def ensure_table(con: sqlite3.Connection) -> str:
    cur = con.execute("SELECT sql FROM sqlite_master WHERE name='notes'")
    row = cur.fetchone()
    if row and row[0]:
        tok = "trigram" if "trigram" in row[0] else "unicode61"
        if tok != "trigram":
            print("[!] 索引是 unicode61，中文检索会落空。重建：python scripts/fetch_kb.py --index")
        return tok
    for tok in ("trigram", "unicode61"):
        try:
            con.execute(f"CREATE VIRTUAL TABLE notes USING fts5(path, title, body, tokenize='{tok}')")
            con.commit()
            return tok
        except sqlite3.OperationalError:
            continue
    raise SystemExit("[FATAL] 无法创建 FTS5 表。")


def like_search(con, q: str, n: int, full: bool) -> None:
    """trigram 要求查询 ≥3 字符；短查询走 LIKE 兜底，按出现频次排序。"""
    rows = con.execute("SELECT path, title, body FROM notes_raw WHERE body LIKE ?", (f"%{q}%",)).fetchall()
    rows.sort(key=lambda r: -r[2].count(q))
    print(f"tokenizer=LIKE 兜底（查询 <3 字符，trigram 不支持）  命中 {len(rows)}")
    for path, title, body in rows[:n]:
        print(f"\n--- {path}  x{body.count(q)}")
        print(f"    {title.strip()}")
        print(f"    {body.strip() if full else excerpt(body, q)}")


def excerpt(body: str, q: str, width: int = 120) -> str:
    i = body.find(q)
    if i < 0:
        return body[:width].strip()
    return ("…" + body[max(0, i - width // 2): i + width // 2] + "…").replace("\n", " ")


def search(q: str, n: int, full: bool) -> None:
    db = resolve_db()
    if not db:
        print("[!] 找不到索引。先跑：python scripts/fetch_kb.py --index")
        return
    con = connect(db)
    tok = ensure_table(con)
    total = con.execute("SELECT count(*) FROM notes").fetchone()[0]
    if total == 0:
        print("[!] 索引为空。先跑：python scripts/fetch_kb.py --index")
        return

    if len(q.strip()) < 3:
        like_search(con, q, n, full)
        return

    cols = "path, title, body" if full else "path, title, snippet(notes, 2, '[', ']', '…', 12)"
    sql = f"SELECT {cols}, bm25(notes) FROM notes WHERE notes MATCH ? ORDER BY bm25(notes) LIMIT ?"
    try:
        rows = con.execute(sql, (q, n)).fetchall()
    except sqlite3.OperationalError as e:
        print(f"[!] 查询失败：{e}\n    多关键词用空格（AND），或用 \"词1\" OR \"词2\"")
        return
    print(f"db={db}\ntokenizer={tok}  命中 {len(rows)}/{total}")
    for row in rows:
        path, title, body, score = row
        print(f"\n--- {path}  bm25={score:.3f}")
        print(f"    {title.strip()}")
        print(f"    {body.strip()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search"])
    ap.add_argument("query")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--full", action="store_true", help="打印完整段落而非摘要")
    args = ap.parse_args()
    if args.cmd == "search":
        search(args.query, args.n, args.full)


if __name__ == "__main__":
    main()
