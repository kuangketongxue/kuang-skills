#!/usr/bin/env python3
"""
飞书笔记追加脚本
用法：
    python scripts/append.py --title "标题" --content "正文" --wiki-url "https://..."
    python scripts/append.py --title "标题" --content "正文" --format-only  # 仅预览
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


def format_note(title: str, content: str, date_str: str = "") -> str:
    """格式化为标准笔记格式。"""
    if not date_str:
        date_str = date.today().strftime("%Y.%m.%d")
    # Clean date format
    date_str = date_str.replace("-", ".")

    body = f"\n## 【{date_str}】{title}\n\n{content}\n"
    return body


def append_to_local(formatted: str, local_path: str) -> bool:
    """追加到本地文件。"""
    path = Path(local_path).resolve()
    if not path.exists():
        print(f"  ⚠️  本地文件不存在: {path}")
        return False

    # Backup
    bak_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak_path)

    # Read current content
    current = path.read_text(encoding="utf-8")

    # Check if the content is in JSON wrapper
    try:
        data = json.loads(current)
        if "data" in data and "document" in data["data"] and "content" in data["data"]["document"]:
            # JSON wrapped format - append to content field
            data["data"]["document"]["content"] += formatted
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✅ 已追加到本地 JSON 文件")
            return True
    except (json.JSONDecodeError, KeyError):
        pass

    # Plain markdown - append directly
    path.write_text(current + formatted, encoding="utf-8")
    print(f"  ✅ 已追加到本地文件")
    return True


def append_to_feishu(formatted: str, wiki_url: str) -> dict:
    """使用 lark-cli 追加到飞书文档末尾。"""
    cmd = [
        "lark-cli", "docs", "+update",
        "--doc", wiki_url,
        "--command", "append",
        "--content", formatted,
        "--format", "json"
    ]

    # Windows fix
    if sys.platform == "win32" and cmd[0] == "lark-cli":
        cmd[0] = "lark-cli.cmd" if shutil.which("lark-cli.cmd") else "lark-cli"

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120, encoding="utf-8")
        output = result.stdout or result.stderr

        if result.returncode == 0:
            return {"success": True, "output": output.strip()}
        else:
            return {"success": False, "error": output.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "TIMEOUT"}
    except FileNotFoundError:
        return {"success": False, "error": "lark-cli not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="飞书笔记追加工具")
    parser.add_argument("--title", required=True, help="笔记标题")
    parser.add_argument("--content", required=True, help="正文内容")
    parser.add_argument("--date", default="", help="日期（默认今天）")
    parser.add_argument("--wiki-url", default="", help="飞书 Wiki URL/token")
    parser.add_argument("--local-path", default="", help="本地同步路径")
    parser.add_argument("--format-only", action="store_true", help="仅格式化预览，不写入")
    args = parser.parse_args()

    formatted = format_note(args.title, args.content, args.date)

    print("=" * 50)
    print("📝 格式化后的笔记：")
    print("=" * 50)
    print(formatted.strip())
    print("=" * 50)
    print(f"  字符数: {len(formatted.strip())}")
    print()

    if args.format_only:
        print("💡 --format-only 模式，未写入任何内容")
        return

    confirm = input("确认追加到飞书？(y/N): ").strip().lower()
    if confirm != "y":
        print("❌ 已取消")
        sys.exit(1)

    results = []

    # Append to Feishu
    if args.wiki_url:
        print(f"\n📤 正在追加到飞书...")
        result = append_to_feishu(formatted, args.wiki_url)
        results.append(("飞书", result))
        if result["success"]:
            print(f"  ✅ {result['output'][:200]}")
        else:
            print(f"  ❌ {result['error'][:200]}")

    # Sync local
    if args.local_path:
        print(f"\n📁 正在同步本地...")
        local_ok = append_to_local(formatted, args.local_path)
        results.append(("本地", {"success": local_ok}))

    # Summary
    print()
    print("=" * 50)
    print("📊 结果汇总：")
    for name, r in results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {name}")
    print("=" * 50)


if __name__ == "__main__":
    main()