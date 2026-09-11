#!/usr/bin/env python3
"""memory-audit.py — detect stale/duplicate/oversized MEMORY.md entries.

Purpose: make self-improving-agent's "curate" promise machine-checkable.
Without this, "curate" relies on agent self-discipline — which is exactly
the failure mode MindStudio flags: "People create memory files but never
update them, so they become stale and eventually" (source [3]).

Catches seven categories (blocking ones marked *):
  1. DEAD_LINK*   — MEMORY.md points to a topic file that no longer exists
  2. ORPHAN*      — a topic file exists in memory/ but is NOT indexed in MEMORY.md
                    (invisible to index-based auto-load: the knowledge silently dies)
  3. OVER_LIMIT*  — MEMORY.md exceeds Claude's 200-line / 25KB load cap
  4. DUPLICATE    — two+ entries share the same short title (fuzzy)
  5. STALE        — entries whose linked topic file hasn't been touched in 60+ days
  6. BUDGET       — MEMORY.md has crossed 70% of the load cap; time to promote/merge
  7. PROMOTE_CANDIDATE / ALREADY_PROMOTED — the curation queue:
                    candidate = topic file showing a recurring lesson (>=2 recurrence
                                markers) or self-declaring promotion readiness
                    promoted  = entry whose rule already graduated to CLAUDE.md/rules/,
                                so it is now index overhead (keep only if it still holds
                                unique supporting evidence)

Exit code: 0 if no DEAD_LINK / ORPHAN / OVER_LIMIT; 1 otherwise.
(DUPLICATE, STALE, BUDGET, PROMOTE_CANDIDATE and ALREADY_PROMOTED are advisory.)

Usage:
  python ~/.claude/skills/self-improving-agent/scripts/memory-audit.py [--memory <path>]

Default --memory: ~/.claude/projects/<cwd-slug>/memory/MEMORY.md

Version: 1.2.0 (2026-09-10) — implement BUDGET (70% cap warning), PROMOTE_CANDIDATE and
  ALREADY_PROMOTED; the SKILL.md Quick Reference promised a "晋升候选" list that the script
  never actually produced (implementation now matches the promise). Fixed docstring: ORPHAN
  blocks too, which the old docstring omitted.
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
BUDGET_WARN_RATIO = 0.70  # user rule: report readings once past 70% of the platform budget

# Recurrence markers — the same lesson showing up repeatedly is what justifies promotion
# (promote-extract.md 判据 1: 重复 >= 2~3 次).
_PROMOTE_RECUR = re.compile(
    r'(反复|重复出现|多次|再次|两次|三次|第四次|第[二三]次|'
    r'一周内[两二三]次|一周内\s*\d+\s*次|\d+\s*次纠正|纠正\s*\d+\s*次|'
    r'同类(?:纠正|事故|错误)|又(?:犯|踩))'
)
# Self-declaring readiness ("值得晋升 / 应晋升").
_PROMOTE_READY = re.compile(r'(应晋升|值得晋升|建议晋升|晋升候选|候选晋升)')
# Already graduated to the rule layer.
_PROMOTED_MARK = re.compile(r'已晋升|已经晋升|规则本体已晋升|晋升进')

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

    # --- BUDGET (advisory): report once past 70% of the cap, before it becomes blocking ---
    # Whisper at 70%, not at 100%: hitting the cap silently truncates what auto-loads.
    used_l = n_lines / MEM_LOAD_CAP_LINES if MEM_LOAD_CAP_LINES else 0
    used_b = n_bytes / MEM_LOAD_CAP_BYTES if MEM_LOAD_CAP_BYTES else 0
    used = max(used_l, used_b)
    if used > 1:
        pass  # OVER_LIMIT already blocked; no need to nag twice
    elif used >= BUDGET_WARN_RATIO:
        driver = 'bytes' if used_b >= used_l else 'lines'
        print(f'  ⚠️  BUDGET: {used:.0%} of the load cap used ({driver}-bound) — '
              f'>={BUDGET_WARN_RATIO:.0%} threshold crossed: promote/merge/drop entries now.')
    else:
        print(f'  ✅ BUDGET: {used:.0%} of the load cap used (warn at {BUDGET_WARN_RATIO:.0%})')

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
    # Exception: files logged as promoted in ~/.claude/promotions.md are intentionally
    # de-indexed (rule graduated to CLAUDE.md, topic file kept as evidence per SKILL.md
    # promote flow: "晋升后从 MEMORY.md 删原条目腾空间").
    indexed_targets = {os.path.normcase(os.path.normpath(os.path.join(base_dir, t)))
                       for _, t, _, _ in entries}
    actual_files = {f for f in os.listdir(base_dir)
                    if f.endswith('.md') and f != os.path.basename(path)}
    # Whitelist: files whose rules graduated to CLAUDE.md are de-indexed on purpose.
    promoted_files = set()
    prom_path = os.path.join(os.path.expanduser('~'), '.claude', 'promotions.md')
    if os.path.isfile(prom_path):
        try:
            with open(prom_path, encoding='utf-8', errors='replace') as fh:
                prom_text = fh.read()
            promoted_files = {m.group(1) for m in re.finditer(r'- 来源：`([^`]+\.md)`', prom_text)}
        except OSError:
            pass
    orphans = sorted(f for f in actual_files
                     if os.path.normcase(os.path.normpath(os.path.join(base_dir, f))) not in indexed_targets
                     and f not in promoted_files)
    n_promoted = len(actual_files & promoted_files)
    if orphans:
        print(f'  ❌ ORPHAN: {len(orphans)} memory file(s) NOT in MEMORY.md index (invisible to auto-load):')
        for f in orphans[:10]:
            print(f'     {f}')
        if len(orphans) > 10:
            print(f'     ... and {len(orphans) - 10} more')
        print(f'     → add an index line "- [Title](file.md) — hook", or delete the file if one-off completed.')
        _BLOCKING = 1
    elif n_promoted:
        print(f'  ✅ ORPHAN: all topic files are indexed or whitelisted ({n_promoted} promoted via promotions.md)')
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

    # --- PROMOTE_CANDIDATE / ALREADY_PROMOTED (advisory): the curation queue ---
    # This is the whole point of the skill ("auto-memory captures, this curates"), so the
    # audit has to emit the queue instead of leaving the agent to eyeball 87 entries.
    candidates, promoted = [], []
    for title, target, line, ln in entries:
        abspath = os.path.join(base_dir, target)
        body = ''
        if os.path.isfile(abspath):
            try:
                with open(abspath, encoding='utf-8', errors='replace') as fh:
                    body = fh.read(6000)
            except OSError:
                body = ''
        ready = bool(_PROMOTE_READY.search(body))
        already = bool(_PROMOTED_MARK.search(body) or _PROMOTED_MARK.search(line))
        recur = len(_PROMOTE_RECUR.findall(body))
        if already and not ready:
            promoted.append((title, target, ln))
        elif ready or recur >= 2:
            candidates.append((title, target, ln, recur))

    if candidates:
        print(f'  ⚠️  PROMOTE_CANDIDATE: {len(candidates)} entry(ies) look promotion-ready '
              f'(recurring lesson or self-declared) — 判据见 promote-extract.md:')
        for title, target, ln, recur in candidates[:10]:
            why = 'self-declared ready' if recur < 2 else f'{recur} recurrence markers'
            print(f'     line {ln}: [{title}]({target})  — {why}')
        if len(candidates) > 10:
            print(f'     ... and {len(candidates) - 10} more')
        print(f'     → 人工确认后晋升进 CLAUDE.md / rules/，然后从 MEMORY.md 删原条目腾空间，')
        print(f'       并在 promotions.md 追加一条日志（没有日志下次会重复提同一件事）。')
    else:
        print(f'  ✅ PROMOTE_CANDIDATE: no recurring-lesson entries awaiting promotion')

    if promoted:
        print(f'  ⚠️  ALREADY_PROMOTED: {len(promoted)} entry(ies) whose rule already lives in '
              f'CLAUDE.md / rules/ — keep only if the file holds unique supporting evidence:')
        for title, target, ln in promoted[:10]:
            print(f'     line {ln}: [{title}]({target})')
        if len(promoted) > 10:
            print(f'     ... and {len(promoted) - 10} more')
        print(f'     → 规则层已全文加载，这些索引行是重复真相；只是留证据就标清楚，否则可删索引行腾空间。')
        print(f'       （删的是 MEMORY.md 里的索引行，不是 topic 文件本身。）')
    else:
        print(f'  ✅ ALREADY_PROMOTED: no graduated rules still occupying index lines')

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
