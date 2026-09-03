# Backup & Restore

> Goal: after a full PC reset, restore your entire Claude Code "self" from one private repo (`claude-memory-backup`, private).

## What gets backed up (allowlist)

| Local source | Repo path in `claude-memory-backup` |
|-------------|--------------------------------------|
| `~/.claude/CLAUDE.md` | `CLAUDE.md` |
| `~/.claude/projects/C--Users-kuang/memory/**` | `memory/` |
| `~/.claude/feishu-playbook.md` | `playbooks/feishu-playbook.md` |
| `~/.claude/github-playbook.md` | `playbooks/github-playbook.md` |
| `~/.claude/.secrets/*.enc` (openssl re-encrypted) | `secrets/*.enc.aes` |
| `~/.claude/.secrets/web-search.env` (per-engine split + encrypted) | `secrets/{tavily,firecrawl,zhihu,exa}.env.enc.aes` (4 files) |
| `~/.claude/scripts/*` (手写自动化脚本，2026-09-03 起) | `host-scripts/`（如 claude-auto-update.ps1 + register-autoupdate-task.ps1；restore 后跑 register 脚本重建计划任务） |
| — | `scripts/backup.sh`, `scripts/restore.sh`, `scripts/split-keys.sh`, `scripts/scan-leaks.sh`, `scripts/feishu-sync.sh` (6 scripts) |
| — | `RESTORE.md` (restore SOP) |

**Explicitly NOT backed up** (deliberate; RESTORE.md has the post-reset steps):
- `~/.claude/settings.json` (auth tokens) — rebuilt by `gh auth login` / `/login`.
- `~/.claude/skills/` — reinstallable assets, not memory.

## `/si:backup` (push to repo)

1. **Secret scan first**: grep upload set for `sk-`+20 / `ghp_`+20 / `github_pat_`+20 / `tvly-`+20 / `fc-`+32 hex / `cfut_`+32 / `EXA-`+32 / Zhihu prefix (`0224ed0b`+30 hex) / `password=…` patterns. Length suffixes required: bare `github_pat_` prefix false-matches descriptive text; `[0-9A-Za-z]{20,}` only hits a real token. Abort on any hit. (web-search 当前 6 个 key 变量 / 4 引擎 double-key fallback: Tavily×2、Firecrawl×2、Zhihu、Exa；`cfut_` 是 Cloudflare API token 前缀，`EXA-` 是 Exa 搜索 API key 前缀，两者也进 web-search.env 且都加密进备份仓。)
2. **Encrypt secrets**: each `~/.claude/.secrets/*.enc` re-encrypted via `openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:PP`. Output: `secrets/<name>.enc.aes`. Passphrase from `PP` env var (`PP='pass' bash scripts/backup.sh`) — never from argv or file. `web-search.env` encrypted as `secrets/web-search.env.enc.aes`.
3. **Upload — one commit via Git Data API** (not per-file PUT): read `main` ref → `tree.sha` → POST one blob per file (base64 via `--input` tempfile to stay under argv limit) → POST new tree against `base_tree` → POST commit → `PATCH` ref `force:false`. No repo clone — matches `github-playbook.md` §1.7 cloud-only SOP.
4. **True sync prunes ghosts**: enumerates existing tree, marks anything in managed scope (`CLAUDE.md`, `memory/`, `playbooks/`, `secrets/`) that no longer exists locally as `sha: null` in same tree — deleted on disk ⇒ deleted in repo, in one commit. `scripts/` and `RESTORE.md` repo-native, never touched. Without this, deleting a local memory leaves a phantom in backup that resurrects stale knowledge after reset.
5. Script: `claude-memory-backup/scripts/backup.sh`.

## `/si:restore` (after PC reset)

1. `git clone git@github.com:<your-username>/claude-memory-backup.git`
2. Copy `CLAUDE.md`, `memory/`, `playbooks/` back to `~/.claude/…` (paths in `RESTORE.md`). `scripts/restore.sh` also in repo — `PP='pass' bash scripts/restore.sh` single-command restore.
3. Decrypt secrets:
   ```bash
   export PP='YOUR_PASSPHRASE'
   mkdir -p ~/.claude/.secrets
   for f in secrets/*.enc.aes; do
     openssl enc -d -aes-256-cbc -pbkdf2 -in "$f" -pass env:PP \
       -out ~/.claude/.secrets/"$(basename "$f" .enc.aes)"
   done
   unset PP
   ```
4. **web-search keys ride along** — `secrets/web-search.env.enc.aes` decrypts to `~/.claude/.secrets/web-search.env` in the same loop. Nothing to re-apply by hand.
5. **Passphrase NOT in repo** — the one you typed at backup time. Forget it ⇒ secrets layer unrecoverable (re-issue API keys).