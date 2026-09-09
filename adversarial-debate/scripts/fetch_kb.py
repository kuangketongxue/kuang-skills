#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_kb.py — adversarial-debate 的 Layer 1 入口（raw 拉取器）

一次跑完原本要手工串的 5 步：
  解析 lark-cli → 拉飞书原文 → 解码 → 无损瘦身 → 按 UTF-8 字节切块 → 输出读后自检报告

设计约束（来自 SCHEMA.md）：
  - raw 层不可变：本脚本只读，绝不写飞书文档
  - 不留原文副本：块文件落在系统 temp，读完由 --clean 清零
  - 无损瘦身：只删「无内容残留」（图占位符）与「完全重复的块」，正文一字不改

用法：
  python fetch_kb.py                 # 拉取 + 切块 + 打印自检报告
  python fetch_kb.py --index         # 额外建 BM25 索引（供 wiki_fts.py 查询）
  python fetch_kb.py --clean         # 删除 temp 下所有 debate_kb_* 残留
  python fetch_kb.py --max-bytes 120000   # 调小块大小（默认 170000）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

# 知识源文档：默认本机飞书文档，可用环境变量 ADVERSARIAL_KB_URL 覆盖（公开版请设成你自己的文档）
DOC_URL = os.environ.get("ADVERSARIAL_KB_URL", "")  # 换成你自己的知识源文档 URL
TEMP_PREFIX = "debate_kb_"

# lark-cli 候选：环境变量 > PATH > 已知安装位置（按优先级尝试，第一个 rc=0 的胜出）
LARK_CLI_CANDIDATES = [
    r"C:\Users\kuang\AppData\Roaming\npm\node_modules\@larksuite\cli\bin\lark-cli.exe",
]

# 图占位符：markdown 导出残留，无内容
RE_IMAGE_PLACEHOLDER = re.compile(r"!\[\]\[image\d+\]")
# 块分隔：二级标题（所有笔记都是 ## 开头）
RE_BLOCK_SPLIT = re.compile(r"\n(?=## )")
# 编号：【1028】/【2026.8.13】/【P137~139】
RE_NOTE_MMDD = re.compile(r"【(\d{4})】")
RE_NOTE_DATE = re.compile(r"【(\d{4})\.(\d{1,2})\.(\d{1,2})】")
# 注意：导出文本里 ~ 一律被转义成 \~（如【P137\~139】、【2026.3.6\~3.20】），引用时要还原成 ~
RE_NOTE_PAGE = re.compile(r"【P(\d+)(?:\\?~(\d+))?】")


def resolve_lark_cli() -> str:
    env = os.environ.get("LARK_CLI")
    candidates = [env] if env else []
    found = shutil.which("lark-cli")
    if found:
        candidates.append(found)
    candidates.extend(LARK_CLI_CANDIDATES)
    for c in candidates:
        if not c:
            continue
        if not (os.path.exists(c) or shutil.which(c)):
            continue
        try:
            r = subprocess.run([c, "--version"], capture_output=True, timeout=90)
            if r.returncode == 0:
                return c
        except Exception:
            continue
    raise SystemExit(
        "[FATAL] 找不到可用的 lark-cli。设置 LARK_CLI 环境变量，或把它加入 PATH。\n"
        "        辩论作废——不得凭记忆引用知识源。"
    )


def fetch(cli: str, out_path: str) -> None:
    cmd = [cli, "docs", "+fetch", "--doc", DOC_URL, "--doc-format", "markdown", "--as", "user"]
    with open(out_path, "wb") as fh:
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE, timeout=600)
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", "replace")[:800]
        raise SystemExit(
            f"[FATAL] lark-cli 拉取失败 rc={r.returncode}\n{err}\n"
            "        常见原因：未登录 / token 过期 / 网络被墙。修好再跑，"
            "        不得凭记忆开辩。"
        )


def decode_and_parse(path: str):
    raw = open(path, "rb").read()
    text = None
    for enc in ("utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise SystemExit("[FATAL] 响应既非 UTF-8 也非 GB18030，无法解码。")
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"[FATAL] 响应不是合法 JSON（前 200 字符：{text[:200]!r}）\n{e}")
    try:
        doc = d["data"]["document"]
        content = doc["content"]
    except (KeyError, TypeError):
        raise SystemExit(
            f"[FATAL] JSON 结构变了，找不到 data.document.content。\n"
            f"        顶层键：{list(d.keys()) if isinstance(d, dict) else type(d)}"
        )
    return doc, content


def slim(blocks: list[str]):
    """无损瘦身：删图占位符、删完全重复的块。返回 (新块列表, 报告)。"""
    cleaned, ph_total = [], 0
    for b in blocks:
        new, n = RE_IMAGE_PLACEHOLDER.subn("", b)
        ph_total += n
        cleaned.append(new)

    seen, kept, dups = {}, [], []
    for b in cleaned:
        key = hashlib.md5(re.sub(r"\s+", " ", b).strip().encode("utf-8")).hexdigest()
        if key in seen:
            head = b.strip().split("\n", 1)[0][:60]
            dups.append(head)
        else:
            seen[key] = True
            kept.append(b)
    return kept, {"placeholders_removed": ph_total, "dup_blocks_removed": dups}


def chunk_by_bytes(blocks: list[str], max_bytes: int, outdir: str):
    chunks, cur, nbytes = [], [], 0
    for b in blocks:
        bb = len(b.encode("utf-8")) + 1
        if cur and nbytes + bb > max_bytes:
            chunks.append("\n".join(cur))
            cur, nbytes = [], 0
        cur.append(b)
        nbytes += bb
    if cur:
        chunks.append("\n".join(cur))

    paths = []
    for i, c in enumerate(chunks, 1):
        p = os.path.join(outdir, f"p{i}.md")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(c)
        paths.append((p, len(c.encode("utf-8"))))
    return paths


def note_stats(content: str):
    mmdd = RE_NOTE_MMDD.findall(content)
    dates = RE_NOTE_DATE.findall(content)
    pages = RE_NOTE_PAGE.findall(content)
    latest = None
    for y, m, d in dates:
        try:
            t = (int(y), int(m), int(d))
        except ValueError:
            continue
        if latest is None or t > latest:
            latest = t
    return {
        "count_mmdd": len(mmdd),
        "count_dated": len(dates),
        "count_page": len(pages),
        "latest_dated": ("【%d.%d.%d】" % latest) if latest else None,
    }


def tail_note(blocks: list[str]):
    """最后一条有正文的笔记标题（自检项：尾部是否触达）。"""
    for b in reversed(blocks):
        lines = [ln for ln in b.strip().split("\n") if ln.strip()]
        if not lines:
            continue
        head = lines[0]
        body = "\n".join(lines[1:]).strip()
        if len(body) > 20:  # 有正文，不是空标题
            return head[:80]
    return None


def build_fts(outdir: str, db_path: str) -> int:
    import sqlite3

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    # trigram 才能正确处理中文（unicode61 会把整段中文当成一个 token，检索必空）
    used = None
    for tok in ("trigram", "unicode61"):
        try:
            con.execute(f"CREATE VIRTUAL TABLE notes USING fts5(path, title, body, tokenize='{tok}')")
            used = tok
            break
        except sqlite3.OperationalError:
            continue
    if used is None:
        raise SystemExit("[FATAL] FTS5 建表失败（trigram/unicode61 都不可用）。")
    # 短查询（<3 字符）trigram 不支持，用这张普通表做 LIKE 兜底
    con.execute("CREATE TABLE notes_raw (path TEXT, title TEXT, body TEXT)")
    n = 0
    for fn in sorted(os.listdir(outdir)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(outdir, fn)
        text = open(p, encoding="utf-8").read()
        for blk in RE_BLOCK_SPLIT.split("\n" + text):
            blk = blk.strip()
            if not blk:
                continue
            title = blk.split("\n", 1)[0][:200]
            con.execute("INSERT INTO notes VALUES (?,?,?)", (fn, title, blk))
            con.execute("INSERT INTO notes_raw VALUES (?,?,?)", (fn, title, blk))
            n += 1
    con.commit()
    con.close()
    return n


def clean_temp() -> int:
    tmp = tempfile.gettempdir()
    removed = 0
    for name in os.listdir(tmp):
        if name.startswith(TEMP_PREFIX) or name.startswith("debate_kb"):
            p = os.path.join(tmp, name)
            try:
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
                removed += 1
            except Exception:
                pass
    if removed:
        print(f"[clean] 已删除 {removed} 个残留：{tmp}")
    else:
        print("[clean] 无残留。")
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-bytes", type=int, default=170000, help="单块 UTF-8 字节上限（Read 上限 256KB）")
    ap.add_argument("--index", action="store_true", help="额外建 BM25 索引")
    ap.add_argument("--clean", action="store_true", help="清理 temp 残留")
    ap.add_argument("--keep", action="store_true", help="不自动删除源 JSON（调试用）")
    args = ap.parse_args()

    if args.clean:
        clean_temp()
        return

    cli = resolve_lark_cli()
    print(f"[cli] {cli}")

    tmp = tempfile.gettempdir()
    outdir = os.path.join(tmp, TEMP_PREFIX + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(outdir, exist_ok=True)
    src = os.path.join(outdir, "_raw.json")

    fetch(cli, src)
    doc, content = decode_and_parse(src)
    if not args.keep:
        os.remove(src)

    blocks = [b for b in RE_BLOCK_SPLIT.split(content) if b.strip()]
    blocks, report = slim(blocks)
    paths = chunk_by_bytes(blocks, args.max_bytes, outdir)
    stats = note_stats("\n".join(blocks))

    print("\n===== 读后自检报告（逐项核对，不要凭记忆） =====")
    print(f"document_id : {doc.get('document_id')}")
    print(f"revision    : {doc.get('revision_id')}   <- 与 wiki/log.md 基线比对")
    print(f"字符数      : {len(content)}")
    print(f"UTF-8 字节  : {len(content.encode('utf-8'))}")
    print(f"笔记块总数  : {len(blocks)}（已去重）")
    print(f"图占位符删除: {report['placeholders_removed']}")
    print(f"重复块删除  : {len(report['dup_blocks_removed'])}")
    for t in report["dup_blocks_removed"][:10]:
        print(f"    - {t}")
    print(f"编号统计    : MMDD {stats['count_mmdd']} 条 / 日期型 {stats['count_dated']} 条 / 页码型 {stats['count_page']} 条")
    print(f"最新日期编号: {stats['latest_dated']}")
    print(f"尾部笔记    : {tail_note(blocks)}")
    print(f"\n切块 {len(paths)} 块（上限 {args.max_bytes} 字节）：")
    for p, nb in paths:
        print(f"  {p}  {nb} B")
    print(f"\n✅ 逐块 Read 上面 {len(paths)} 个文件，一块都不能跳。读完报「已读 {len(paths)}/{len(paths)}，0 跳过」。")
    print(f"读完清理：python {os.path.abspath(__file__)} --clean")

    if args.index:
        # 索引含全文 body，属原文副本范畴 → 只落在 temp，随 --clean 清零，绝不写进 wiki/
        db = os.path.join(outdir, "fts.sqlite")
        n = build_fts(outdir, db)
        print(f"\n[index] BM25 索引已建：{n} 块 -> {db}")
        print("[index] 注意：索引随 --clean 一并删除，不落盘（不留原文副本）。")


if __name__ == "__main__":
    main()
