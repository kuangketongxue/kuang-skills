#!/usr/bin/env bash
# self-check.sh — run before declaring a neat-freak closeout "complete".
#
# Purpose: turn the SKILL.md "最终自检" checklist (currently 13 text-only items
# that rely on agent self-discipline) into a machine-checkable gate with an
# exit code. This makes neat-freak walk the talk of the "确定性验证纪律"
# discipline in CLAUDE.md — the meta-ruler must measure itself.
#
# Exit code: 0 = all checks passed; 1 = one or more FAIL.
# Only FAIL is blocking; WARN is advisory (print but don't fail).
#
# Usage:
#   bash ~/.claude/skills/neat-freak/scripts/self-check.sh <project-root>
#
# Version: 1.0.0 (2026-09-01)
# Refs: SKILL.md "最终自检" §; references/verification.md "风险决定证据深度"

set -uo pipefail

ROOT="${1:-.}"
PASS=0
FAIL=0
WARN=0

pass() { PASS=$((PASS+1)); printf '  ✅ PASS  %s\n' "$1"; }
fail() { FAIL=$((FAIL+1)); printf '  ❌ FAIL  %s\n' "$1"; }
warn() { WARN=$((WARN+1)); printf '  ⚠️  WARN  %s\n' "$1"; }
info() { printf '  ℹ️   %s\n' "$1"; }

printf '=== neat-freak self-check :: %s ===\n\n' "$(cd "$ROOT" && pwd)"

# ------------------------------------------------------------------
# 1. Workspace cleanliness: no residual lane artifacts
# ------------------------------------------------------------------
info "[1/6] Workspace residue (build/deps/hidden dirs)"
RESIDUE=0
for d in node_modules __pycache__ .next dist build .pytest_cache .mypy_cache .ruff_cache .vite; do
  if [ -e "$ROOT/$d" ]; then
    # node_modules / dist may be legitimate; warn not fail
    warn "residual dir present: $ROOT/$d (legit or leftover — verify manually)"
    WARN=$((WARN+1))
  fi
done
# .DS_Store / Thumbs.db anywhere = definite residue
if find "$ROOT" -maxdepth 3 \( -name '.DS_Store' -o -name 'Thumbs.db' \) 2>/dev/null | grep -q .; then
  fail "macos/windows residue (.DS_Store / Thumbs.db) found under $ROOT"
else
  pass "no .DS_Store / Thumbs.db residue"
fi
RESIDUE_DIRS="$(find "$ROOT" -maxdepth 2 \( -name '*_old' -o -name '*_backup' -o -name '*_tmp' -o -name '*_backup' \) -type d 2>/dev/null)"
if [ -n "$RESIDUE_DIRS" ]; then
  warn "possible leftover dirs (old/backup/tmp): $RESIDUE_DIRS"
else
  pass "no *_old / *_backup / *_tmp leftover dirs"
fi

# ------------------------------------------------------------------
# 2. Secret leak scan (CLAUDE.md red line: "密钥不进代码")
# ------------------------------------------------------------------
info "[2/6] Secret scan (sk-/ghp_/github_pat_/fc-/cfut_/EXA- prefixes)"
SECRET_HITS=$(grep -rInE --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=__pycache__ \
  -E '(sk-[0-9A-Za-z]{20,}|ghp_[0-9A-Za-z]{20,}|github_pat_[0-9A-Za-z]{20,}|fc-[0-9a-f]{32}|cfut_[0-9A-Za-z]{32}|EXA-[0-9A-Za-z]{32}|0224ed0b[0-9a-f]{30})' \
  "$ROOT" 2>/dev/null || true)
if [ -n "$SECRET_HITS" ]; then
  fail "possible secret leaks detected:"
  echo "$SECRET_HITS" | sed 's/^/     /'
else
  pass "no secret prefixes in tracked files"
fi

# ------------------------------------------------------------------
# 3. Requirement-completion matrix present in the closeout transcript
# ------------------------------------------------------------------
info "[3/6] Requirement-completion matrix (需求完成度)"
NF_OUT="/tmp/nf-transcript.md"
if [ -f "$NF_OUT" ]; then
  if grep -qE '✅|📋|⚠️|❌|❓' "$NF_OUT"; then
    if grep -qE '⚠️' "$NF_OUT"; then
      warn "requirement matrix present but contains ⚠️ (被顶掉) — ensure each is addressed"
    else
      pass "requirement-completion matrix present with statuses"
    fi
  else
    fail "nf-transcript.md exists but no requirement-status emoji (✅/📋/⚠️/❌/❓) found"
  fi
else
  warn "nf-transcript.md not at /tmp/nf-transcript.md — run extract_transcript.py --all --out /tmp/nf-transcript.md first"
fi

# ------------------------------------------------------------------
# 4. Rule-file health (CLAUDE.md / AGENTS.md exist + size sanity)
# ------------------------------------------------------------------
info "[4/6] Rule-file health"
for f in CLAUDE.md AGENTS.md .claude/CLAUDE.md; do
  if [ -f "$ROOT/$f" ]; then
    LINES=$(wc -l < "$ROOT/$f")
    if [ "$LINES" -gt 200 ]; then
      warn "$f is $LINES lines (>200 — consider splitting per references/agent-paths.md)"
    else
      pass "$f present ($LINES lines)"
    fi
  fi
done
if ! ls "$ROOT"/CLAUDE.md "$ROOT"/AGENTS.md "$ROOT"/.claude/CLAUDE.md 2>/dev/null | grep -q .; then
  warn "no CLAUDE.md / AGENTS.md / .claude/CLAUDE.md found (may be legitimate for pre-project dirs)"
fi

# ------------------------------------------------------------------
# 5. Cross-file version consistency for shared scripts
# ------------------------------------------------------------------
info "[5/6] Shared-script version consistency"
SHARED="$HOME/.claude/skills/_shared/extract_transcript.py"
NF_SCRIPT="$HOME/.claude/skills/neat-freak/scripts/extract_transcript.py"
SI_SCRIPT="$HOME/.claude/skills/self-improving-agent/scripts/extract_transcript.py"
if [ -f "$SHARED" ]; then
  pass "shared source exists: $SHARED"
  # both wrappers should reference _shared (thin wrapper check)
  for w in "$NF_SCRIPT" "$SI_SCRIPT"; do
    if [ -f "$w" ] && grep -q '_shared' "$w" 2>/dev/null && [ "$(wc -l < "$w")" -lt 40 ]; then
      pass "wrapper thin & references _shared: $(basename $(dirname $w))/$(basename $w)"
    else
      warn "wrapper may have drifted (not thin or missing _shared ref): $w"
    fi
  done
else
  warn "shared source missing at $SHARED (expected; non-blocking if not yet set up)"
fi

# ------------------------------------------------------------------
# 6. git state awareness (don't claim "clean" if dirty)
# ------------------------------------------------------------------
info "[6/6] git state awareness"
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git -C "$ROOT" diff --quiet HEAD -- 2>/dev/null; then
    pass "working tree clean"
  else
    warn "working tree has unstaged changes — verify they're intentional before closeout"
  fi
else
  info "not a git repo — skipping git-clean check"
fi

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
printf '\n=== Summary: %d ✅ PASS · %d ❌ FAIL · %d ⚠️ WARN ===\n' "$PASS" "$FAIL" "$WARN"
if [ "$FAIL" -gt 0 ]; then
  printf 'BLOCKED — fix %d FAIL before declaring closeout complete.\n' "$FAIL"
  exit 1
fi
printf 'PASS — all blocking checks clear (WARN items are advisory, verify manually).\n'
exit 0
