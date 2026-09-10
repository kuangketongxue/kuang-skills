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
# Version: 1.2.0 (2026-09-10) — [3/6] no longer false-WARNs: auto-discovers the newest
#   *transcript*.md under TMPDIR/TEMP/TMP/AppData-Local-Temp (the old hardcoded
#   /tmp/nf-transcript.md default never matched the timestamped name the extractor
#   actually writes, so every run printed a bogus WARN). Also warns on >24h transcript
#   residue, since the extract contains the full conversation incl. pasted secrets.
# Version: 1.1.0 (2026-09-09) — fix WARN double-count; fix [4/6] false WARN
#   (ls multi-file check → per-file -f test); fix [6/6] false WARN (enclosing
#   repo like a dirty $HOME no longer counts as this project's git state);
#   [3/6] transcript path via NF_TRANSCRIPT env, matrix via NF_REPORT env.
# Usage:
#   bash ~/.claude/skills/neat-freak/scripts/self-check.sh <project-root>
#   NF_TRANSCRIPT=/path/to/transcript.md NF_REPORT=/path/to/report.md bash self-check.sh <root>
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
# 3. Requirement-completion matrix (需求完成度)
# ------------------------------------------------------------------
info "[3/6] Requirement-completion matrix (需求完成度)"
NF_REPORT_FILE="${NF_REPORT:-}"
if [ -n "$NF_REPORT_FILE" ] && [ -f "$NF_REPORT_FILE" ]; then
  if grep -qE 'OK|PENDING|CANCEL|BLOCKED|UNKNOWN|✅|📋|⚠|❌|❓' "$NF_REPORT_FILE"; then
    if grep -qE '⚠' "$NF_REPORT_FILE"; then
      warn "closeout report contains blocked/topped-out items - ensure each is addressed"
    else
      pass "closeout report has requirement statuses"
    fi
  else
    fail "report file exists but no requirement-status marker found: $NF_REPORT_FILE"
  fi
else
  info "no report file on disk (matrix lives in chat output) - set NF_REPORT to machine-check it"
fi

# Transcript discovery. NF_TRANSCRIPT wins; otherwise auto-discover the newest
# *transcript*.md under the platform temp dirs. The old hardcoded default
# /tmp/nf-transcript.md emitted a false WARN on literally every run, because
# extract_transcript.py writes nf-transcript-<timestamp>.md (timestamped on
# purpose - the output contains the whole conversation). 3.1.1 fixed sibling
# false WARNs in [4/6] and [6/6] and missed this one.
NF_OUT=""
NF_OUT_SRC=""
if [ -n "${NF_TRANSCRIPT:-}" ]; then
  NF_OUT="$NF_TRANSCRIPT"
  NF_OUT_SRC="NF_TRANSCRIPT"
  if [ -f "$NF_OUT" ]; then
    pass "session transcript present (via NF_TRANSCRIPT): $NF_OUT"
  else
    fail "NF_TRANSCRIPT points at a missing file: $NF_OUT"
  fi
else
  for d in "${TMPDIR:-}" "${TEMP:-}" "${TMP:-}" "$HOME/AppData/Local/Temp" /tmp; do
    [ -n "$d" ] && [ -d "$d" ] || continue
    cand="$(ls -t "$d"/*transcript*.md 2>/dev/null | head -1)"
    if [ -n "$cand" ]; then
      NF_OUT="$cand"
      NF_OUT_SRC="auto-discovered"
      break
    fi
  done
  if [ -n "$NF_OUT" ]; then
    info "transcript auto-discovered ($NF_OUT_SRC): $NF_OUT"
    info "  (export NF_TRANSCRIPT=\"$NF_OUT\" to verify this exact file)"
    # Sensitive residue: the extract contains the full conversation, including any
    # secret the user ever pasted (see memory [[transcript-plaintext-key-risk]]).
    # SKILL.md 要求回顾完成后立即删除；>24h 未删就是残留。
    if [ -n "$(find "$NF_OUT" -mtime +0 2>/dev/null)" ]; then
      warn "transcript residue >24h old - delete it after the review (contains raw keys/passphrases)"
    fi
  else
    info "no transcript found in temp dirs - run extract_transcript.py --out <file> first"
  fi
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
RULE_FOUND=0
for f in CLAUDE.md AGENTS.md .claude/CLAUDE.md; do
  [ -f "$ROOT/$f" ] && RULE_FOUND=1
done
if [ "$RULE_FOUND" -eq 0 ]; then
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
      pass "wrapper thin & references _shared: $(basename "$(dirname "$(dirname "$w")")")/$(basename "$w")"
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
GIT_TOP="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -n "$GIT_TOP" ]; then
  # skip entirely when nothing under ROOT is tracked by the enclosing repo
  # (scratch/temp dirs inside e.g. a $HOME repo must not false-alarm)
  if [ -z "$(git -C "$ROOT" ls-files -- . 2>/dev/null | head -1)" ]      && [ -z "$(git -C "$ROOT" status --porcelain -- . 2>/dev/null)" ]; then
    info "no tracked files under $ROOT in enclosing repo ($GIT_TOP) — skipping git-clean check"
  # scope to $ROOT so an enclosing dirty repo (e.g. a $HOME repo) does not false-alarm
  elif git -C "$ROOT" diff --quiet HEAD -- . 2>/dev/null      && [ -z "$(git -C "$ROOT" status --porcelain -- . 2>/dev/null)" ]; then
    pass "project tree clean (scoped to $ROOT; repo: $GIT_TOP)"
  else
    warn "project tree has changes (scoped to $ROOT; repo: $GIT_TOP) — verify they're intentional"
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
