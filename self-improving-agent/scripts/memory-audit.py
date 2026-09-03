#!/usr/bin/env python3
"""memory-audit.py — detect stale/duplicate/oversized MEMORY.md entries.

Purpose: make self-improving-agent's "curate" promise machine-checkable.
Without this, "curate" relies on agent self-discipline — which is exactly
the failure mode MindStudio flags: "People create memory files but never
update them, so they become stale and eventually" (source [3]).

Catches five categories:
  1. DEAD_LINK    — MEMORY.md points to a topic file that no longer exists
  2. ORPHAN       — a topic file exists in memory/ but is NOT indexed in MEMORY.md
                    (invisible to index-based auto-load: the knowledge silently dies)
  3. DUPLICATE    — two+ entries share the same short title (fuzzy)
  4. OVER_LIMIT   — MEMORY.md exceeds Claude's 200-line / 25KB load cap
  5. STALE        — entries whose linked topic file hasn't been touched in 60+ days

Exit code: 0 if no DEAD_LINK / OVER_LIMIT; 1 otherwise.
(DUPLICATE and STALE are advisory — printed, don't block.)

Usage:
  python ~/.claude/skills/self-improving-agent/scripts/memory-audit.py [--memory <path>]

Default --memory: ~/.claude/projects/<cwd-slug>/memory/MEMORY.md

Version: 1.1.0 (2026-09-03) — add ORPHAN check (file present but unindexed; 15 real orphans found in prod MEMORY.md motivated this)
Sources:
  [1] https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
  [2] https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
  [3] https://www.mindstudio.ai/blog/self-improving-ai-skills-claude-code
"""
import argparse
import os
import re
import sys
import time
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

MEM_LOAD_CAP_LINES = 200
MEM_LOAD_CAP_BYTES = 25 * 1024
STALE_DAYS = 60

_BLOCKING = 0  # bumped to 1 when a blocking issue is found


def find_default_memory():
    """Discover the MEMORY.md for the current cwd using Claude's slug rule."""
    home = os.path.expanduser('~')
    cwd = os.getcwd()
    slug = cwd.replace(':', '-').replace('\\', '-').replace('/', '-')
    return os.path.join(home, '.claude', 'projects', slug, 'memory', 'MEMORY.md')


def slug_to_lines(text):
    """MEMORY.md lines look like: - [Title](file.md) — hook.  Returns list of (title, target_file, line_text, lineno)."""
    entries = []
    link_re = re.compile(r'^- \[(.+?)\]\((.+?)\)\s*[—-]')
    for i, line in enumerate(text.splitlines(), 1):
        m = link_re.match(line.strip())
        if m:
            entries.append((m.group(1).strip(), m.group(2).strip(), line, i))
    return entries


def audit(path):
    global _BLOCKING
    if not os.path.isfile(path):
        print(f'ERROR: MEMORY.md not found at {path}')
        return 1
    with open(path, encoding='utf-8') as f:
        raw = f.read()

    lines = raw.splitlines()
    n_lines = len(lines)
    n_bytes = len(raw.encode('utf-8'))
    base_dir = os.path.dirname(os.path.abspath(path))

    print(f'=== memory-audit :: {path} ===')
    print(f'size: {n_lines} lines / {n_bytes} bytes  (load cap: {MEM_LOAD_CAP_LINES} lines / {MEM_LOAD_CAP_BYTES} bytes)')
    print()

    entries = slug_to_lines(raw)
    print(f'index entries: {len(entries)}')

    # --- OVER_LIMIT (blocking) ---
    if n_lines > MEM_LOAD_CAP_LINES or n_bytes > MEM_LOAD_CAP_BYTES:
        print(f'  ❌ OVER_LIMIT: MEMORY.md exceeds Claude auto-load cap (200 lines / 25KB).')
        print(f'     → migrate older/less-used entries to topic files under memory/, keep only short index pointers.')
        _BLOCKING = 1
    else:
        margin_l = MEM_LOAD_CAP_LINES - n_lines
        margin_b = MEM_LOAD_CAP_BYTES - n_bytes
        print(f'  ✅ OVER_LIMIT: OK (headroom {margin_l} lines / {margin_b} bytes)')

    # --- DEAD_LINK (blocking) ---
    dead = []
    for title, target, line, ln in entries:
        abspath = os.path.join(base_dir, target)
        if not os.path.isfile(abspath):
            # tolerate relative cross-links like [[name]] which don't use ()
            dead.append((title, target, ln))
    if dead:
        print(f'  ❌ DEAD_LINK: {len(dead)} entries point to missing files:')
        for title, target, ln in dead:
            print(f'     line {ln}: [{title}]({target})  — file not found')
        print(f'     → either restore the file, rewrite the pointer, or drop the entry.')
        _BLOCKING = 1
    else:
        print(f'  ✅ DEAD_LINK: all {len(entries)} indexed files exist')

    # --- ORPHAN (blocking): topic file exists but is not indexed in MEMORY.md ---
    indexed_targets = {os.path.normcase(os.path.normpath(os.path.join(base_dir, t)))
                       for _, t, _, _ in entries}
    actual_files = {f for f in os.listdir(base_dir)
                    if f.endswith('.md') and f != os.path.basename(path)}
    orphans = sorted(f for f in actual_files
                     if os.path.normcase(os.path.normpath(os.path.join(base_dir, f))) not in indexed_targets)
    if orphans:
        print(f'  ❌ ORPHAN: {len(orphans)} memory file(s) NOT in MEMORY.md index (invisible to auto-load):')
        for f in orphans[:10]:
            print(f'     {f}')
        if len(orphans) > 10:
            print(f'     ... and {len(orphans) - 10} more')
        print(f'     → add an index line "- [Title](file.md) — hook", or delete the file if one-off completed.')
        _BLOCKING = 1
    else:
        print(f'  ✅ ORPHAN: all {len(actual_files)} topic files are indexed')

    # --- DUPLICATE (advisory) ---
    norm = lambda s: re.sub(r'[^a-z0-9一-鿿]', '', s.lower())
    buckets = defaultdict(list)
    for title, target, line, ln in entries:
        buckets[norm(title)].append((title, target, ln))
    dups = {k: v for k, v in buckets.items() if len(v) > 1}
    if dups:
        print(f'  ⚠️  DUPLICATE: {len(dups)} title-collision group(s) (advisory):')
        for k, items in list(dups.items())[:8]:
            locs = ', '.join(f'line {ln}' for _, _, ln in items)
            print(f'     "{items[0][0]}" → {locs}')
    else:
        print(f'  ✅ DUPLICATE: no title collisions')

    # --- STALE (advisory) ---
    now = time.time()
    stale = []
    for title, target, line, ln in entries:
        abspath = os.path.join(base_dir, target)
        if os.path.isfile(abspath):
            try:
                mtime = os.path.getmtime(abspath)
                if (now - mtime) / 86400 > STALE_DAYS:
                    days = int((now - mtime) / 86400)
                    stale.append((title, target, ln, days))
            except OSError:
                pass
    if stale:
        print(f'  ⚠️  STALE: {len(stale)} entries whose topic file untouched {STALE_DAYS}+ days (advisory):')
        for title, target, ln, days in stale[:10]:
            print(f'     line {ln}: [{title}]({target})  — {days}d old')
        if len(stale) > 10:
            print(f'     ... and {len(stale) - 10} more')
    else:
        print(f'  ✅ STALE: no entries older than {STALE_DAYS} days')

    print()
    print(f'=== verdict: {"BLOCKING ISSUE(S) FOUND" if _BLOCKING else "clean (all blocking checks pass)"} ===')
    return 1 if _BLOCKING else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--memory', default=None, help='path to MEMORY.md (default: auto-discover for cwd)')
    args = ap.parse_args()
    path = args.memory or find_default_memory()
    sys.exit(audit(path))


if __name__ == '__main__':
    main()
