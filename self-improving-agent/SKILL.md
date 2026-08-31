---
name: "self-improving-agent"
description: "Curate Claude Code's auto-memory into durable project knowledge. Analyze MEMORY.md for patterns, promote proven learnings to CLAUDE.md and .claude/rules/, extract recurring solutions into reusable skills. Use when: (1) reviewing what Claude has learned about your project, (2) graduating a pattern from notes to enforced rules, (3) turning a debugging solution into a skill, (4) checking memory health and capacity."
---

# Self-Improving Agent

> Auto-memory captures. This plugin curates.

## ⚠️ 第一步永远是：完整回顾本次会话（强制，不可跳过）

运行本 skill 的任何命令前，必须先做这一步——**分析对象不只是 MEMORY.md 文件，还包括当前对话的全部内容**：

1. **从头到尾回顾本次会话（用脚本拉全量，不受 /compact 影响）**：先运行提取脚本 `python ~/.claude/skills/self-improving-agent/scripts/extract_transcript.py --all --out /tmp/si-transcript.md`（**Windows 本机用绝对路径** `python "C:/Users/kuang/.claude/skills/self-improving-agent/scripts/extract_transcript.py" --all --out "C:/Users/kuang/AppData/Local/Temp/si-transcript.md"`——`~` 和 `/tmp` 在 Windows python 不认，会 FileNotFoundError）。neat-freak skill 也复用此脚本，读 Claude Code 会话 transcript jsonl。transcript jsonl 是磁盘原始会话记录，**compact 只压缩 LLM 上下文窗口、不动磁盘文件**，所以脚本能拉到 compact 前被"忘掉"的全部真实用户输入（默认 `--all` 扫当前 cwd 全部 jsonl 覆盖 compact 前后 + 跨 session 连续工作，并按消息 timestamp 只保留最近 24 小时——收尾聚焦本次会话不扫历史全量，曾因无时间窗扫到 850 条 / 跨 58 个 jsonl 18 天浪费上下文；`--hours N` 调时间窗 / `--hours 0` 关闭过滤取全量历史（跨天全量审计才用，输出大务必 `--out` 写文件分段 Read）；`--n N` 调文件数量；`<path>` 指定单文件）。脚本过滤掉 tool_result / system-reminder 注入 / task-notification / skill body 全文（按 `isSidechain`/`isMeta` 标志跳过系统注入——这是过滤 skill body 污染的最可靠标志，标签检测会漏因为注入是纯文本无 `<command-message>` 标签），只留真实用户文本 + 用户调过的命令名。**Read 输出文件全量回顾**，逐条核对用户提过的每个需求、每条纠正（如"不要说英文""这个选项不要出现"）、每个踩坑与修复、每次用户表达的不满或偏好。**禁止只靠会话内的摘要或最近几轮**——compact 摘要会丢细节（曾漏飞书字段规则、漏"用 frontend-design"等明确需求），transcript 原文不丢。
2. **对照检查三个问题**：
   - 本次会话里有哪些经验/纠正**还没写进** MEMORY.md / playbook / CLAUDE.md？（漏记 → 立即补）
   - 已有记忆里有没有被本次会话证伪的条目？（过时 → 就地修正或删除）
   - 有没有重复出现 2 次以上的模式值得晋升为规则/skill？（候选 → 走 promote 流程）
3. **输出回顾清单**再执行具体命令：列出「新发现 N 条、修正 M 条、晋升候选 K 条」，让用户能看到本次沉淀了什么。

只读 MEMORY.md 不看对话 = 只整理旧账、漏掉今天刚犯的错，这是本 skill 最大的失败模式。

---

Claude Code's auto-memory (v2.1.32+) automatically records project patterns, debugging insights, and your preferences in `MEMORY.md`. This plugin adds the intelligence layer: it analyzes what Claude has learned, promotes proven patterns into project rules, and extracts recurring solutions into reusable skills.

## Quick Reference

| Command | What it does |
|---------|-------------|
| （所有命令） | **先完整回顾本次会话**（见上方强制第一步），再执行下述动作 |
| `/si:memory-review` | Analyze MEMORY.md — find promotion candidates, stale entries, consolidation opportunities |
| `/si:promote` | Graduate a pattern from MEMORY.md → CLAUDE.md or `.claude/rules/` |
| `/si:extract` | Turn a proven pattern into a standalone skill |
| `/si:memory-status` | Memory health dashboard — line counts, topic files, recommendations |
| `/si:remember` | Explicitly save important knowledge to auto-memory |
| `/si:backup` | Push CLAUDE.md + auto-memory + playbooks + encrypted secrets to `claude-memory-backup` private repo |
| `/si:restore` | Restore everything from `claude-memory-backup` after a PC reset (decrypts secrets with your passphrase) |

## How It Fits Together

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code Memory Stack                │
├─────────────┬──────────────────┬────────────────────────┤
│  CLAUDE.md  │   Auto Memory    │   Session Memory       │
│  (you write)│   (Claude writes)│   (Claude writes)      │
│  Rules &    │   MEMORY.md      │   Conversation logs    │
│  standards  │   + topic files  │   + continuity         │
│  Full load  │   First 200 lines│   Contextual load      │
├─────────────┴──────────────────┴────────────────────────┤
│              ↑ /si:promote        ↑ /si:memory-review   │
│         Self-Improving Agent (this plugin)               │
│              ↓ /si:extract    ↓ /si:remember            │
├─────────────────────────────────────────────────────────┤
│  .claude/rules/    │    New Skills    │   Error Logs     │
│  (scoped rules)    │    (extracted)   │   (auto-captured)│
└─────────────────────────────────────────────────────────┘
```

## Installation

### Claude Code (Plugin)
```
/plugin marketplace add alirezarezvani/claude-skills
/plugin install self-improving-agent@claude-code-skills
```

### OpenClaw
```bash
clawhub install self-improving-agent
```

### Codex CLI
```bash
./scripts/codex-install.sh --skill self-improving-agent
```

## Memory Architecture

### Where things live

| File | Who writes | Scope | Loaded |
|------|-----------|-------|--------|
| `./CLAUDE.md` | You (+ `/si:promote`) | Project rules | Full file, every session |
| `~/.claude/CLAUDE.md` | You | Global preferences | Full file, every session |
| `~/.claude/projects/<path>/memory/MEMORY.md` | Claude (auto) | Project learnings | First 200 lines |
| `~/.claude/projects/<path>/memory/*.md` | Claude (overflow) | Topic-specific notes | On demand |
| `.claude/rules/*.md` | You (+ `/si:promote`) | Scoped rules | When matching files open |

### The promotion lifecycle

```
1. Claude discovers pattern → auto-memory (MEMORY.md)
2. Pattern recurs 2-3x → /si:memory-review flags it as promotion candidate
3. You approve → /si:promote graduates it to CLAUDE.md or rules/
4. Pattern becomes an enforced rule, not just a note
5. MEMORY.md entry removed → frees space for new learnings
```

## Core Concepts

### Auto-memory is capture, not curation

Auto-memory is excellent at recording what Claude learns. But it has no judgment about:
- Which learnings are temporary vs. permanent
- Which patterns should become enforced rules
- When the 200-line limit is wasting space on stale entries
- Which solutions are good enough to become reusable skills

That's what this plugin does.

### Promotion = graduation

When you promote a learning, it moves from Claude's scratchpad (MEMORY.md) to your project's rule system (CLAUDE.md or `.claude/rules/`). The difference matters:

- **MEMORY.md**: "I noticed this project uses pnpm" (background context)
- **CLAUDE.md**: "Use pnpm, not npm" (enforced instruction)

Promoted rules have higher priority and load in full (not truncated at 200 lines).

### Rules directory for scoped knowledge

Not everything belongs in CLAUDE.md. Use `.claude/rules/` for patterns that only apply to specific file types:

```yaml
# .claude/rules/api-testing.md
---
paths:
  - "src/api/**/*.test.ts"
  - "tests/api/**/*"
---
- Use supertest for API endpoint testing
- Mock external services with msw
- Always test error responses, not just happy paths
```

This loads only when Claude works with API test files — zero overhead otherwise.

## Agents

### memory-analyst
Analyzes MEMORY.md and topic files to identify:
- Entries that recur across sessions (promotion candidates)
- Stale entries referencing deleted files or old patterns
- Related entries that should be consolidated
- Gaps between what MEMORY.md knows and what CLAUDE.md enforces

### skill-extractor
Takes a proven pattern and generates a complete skill:
- SKILL.md with proper frontmatter
- Reference documentation
- Examples and edge cases
- Ready for `/plugin install` or `clawhub publish`

## Hooks

### error-capture (PostToolUse → Bash)
Monitors command output for errors. When detected, appends a structured entry to auto-memory with:
- The command that failed
- Error output (truncated)
- Timestamp and context
- Suggested category

**Token overhead:** Zero on success. ~30 tokens only when an error is detected.

## Platform Support

| Platform | Memory System | Plugin Works? |
|----------|--------------|---------------|
| Claude Code | Auto-memory (MEMORY.md) | ✅ Full support |
| OpenClaw | workspace/MEMORY.md | ✅ Adapted (reads workspace memory) |
| Codex CLI | AGENTS.md | ✅ Adapted (reads AGENTS.md patterns) |
| GitHub Copilot | `.github/copilot-instructions.md` | ⚠️ Manual promotion only |

## Related

- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory)
- [pskoett/self-improving-agent](https://clawhub.ai/pskoett/self-improving-agent) — inspiration
- [playwright-pro](engineering-team/playwright-pro/) — sister plugin in this repo

## Backup & Restore

> Goal: after a full PC reset, restore your entire Claude Code "self" from one private repo.

### What gets backed up (allowlist — bare `.secrets/` explicitly excluded)

| Local source | Repo path in `claude-memory-backup` |
|-------------|--------------------------------------|
| `~/.claude/CLAUDE.md` | `CLAUDE.md` |
| `~/.claude/projects/C--Users-kuang/memory/**` | `memory/` |
| `~/.claude/feishu-playbook.md` | `playbooks/feishu-playbook.md` |
| `~/.claude/github-playbook.md` | `playbooks/github-playbook.md` |
| `~/.claude/.secrets/*.enc` (openssl re-encrypted) | `secrets/*.enc.aes` |
| `~/.claude/.secrets/web-search.env` (encrypted once, then same flow) | `secrets/web-search.env.enc.aes` |
| — | `RESTORE.md` (restore SOP) |

**Explicitly NOT backed up** (deliberate; RESTORE.md has the post-reset steps for each):
- `~/.claude/settings.json` (auth tokens) — rebuilt by `gh auth login` / `/login`.
- `~/.claude/skills/` — reinstallable assets, not memory.

### `/si:backup` (run this to update the repo)
1. **Secret scan first**: grep the upload set for `sk-`+20 chars / `ghp_`+20 / `github_pat_`+20 / `tvly-`+20 / `fc-`+32 hex / Zhihu-key prefix / `password=…` patterns — abort on any hit. Length suffixes are required: a bare `github_pat_` prefix false-matches descriptive text that literally writes the prefix string; `[0-9A-Za-z]{20,}` only hits a real token. Plaintext tokens never reach the repo. (A bare `sk-`-only pattern misses `fc-` and the Zhihu secret; the scan covers all five web-search engines.)
2. **Encrypt secrets**: each `~/.claude/.secrets/*.enc` is re-encrypted with `openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:PP` using your passphrase. Output: `secrets/<name>.enc.aes`. The passphrase comes from the `PP` environment variable (`PP='pass' bash scripts/backup.sh`) — never from argv or a file, so nothing lands in the process list or on disk. `web-search.env` (plaintext .env) is encrypted once into `web-search.env.enc` and runs through the same loop, landing as `secrets/web-search.env.enc.aes` — the strip-`.enc.aes` on restore brings it back as `web-search.env`.
3. **Upload — one commit via the Git Data API** (not per-file `PUT /contents`): read the `main` ref → its `tree.sha` → POST one blob per file (base64 content via an `--input` tempfile to stay under argv limits) → POST a new tree against that `base_tree` → POST a commit → `PATCH` the ref with `force:false`. No repo clone — matches the cloud-only SOP in `github-playbook.md` §1.7.
4. **True sync prunes ghosts**: the script also enumerates the existing tree recursively and marks anything inside its managed scope (`CLAUDE.md`, `memory/`, `playbooks/`, `secrets/`) that no longer exists locally as `sha: null` in the same tree — deleted on disk ⇒ deleted in repo, in that one commit. `scripts/` and `RESTORE.md` are repo-native and never touched. Without this, deleting a local memory leaves a phantom copy in the backup that resurrects stale or contradictory knowledge after a reset.
5. The reusable script lives at `claude-memory-backup/scripts/backup.sh`.

### `/si:restore` (run this after a reset)
1. `git clone git@github.com:kuangketongxue/claude-memory-backup.git`
2. Copy `CLAUDE.md`, `memory/`, `playbooks/` back to `~/.claude/…` (paths in `RESTORE.md`).
3. Decrypt secrets with your passphrase:
   ```bash
   export PP='YOUR_PASSPHRASE'
   mkdir -p ~/.claude/.secrets
   for f in secrets/*.enc.aes; do
     openssl enc -d -aes-256-cbc -pbkdf2 -in "$f" -pass env:PP \
       -out ~/.claude/.secrets/"$(basename "$f" .enc.aes)"
   done
   unset PP
   ```
4. **web-search keys ride along with the tokens** — `secrets/web-search.env.enc.aes` decrypts to `~/.claude/.secrets/web-search.env` in the same loop (the `basename … .enc.aes` strip handles it), so nothing to re-apply by hand.
5. **The passphrase is NOT in the repo** — it's the one you typed at backup time. Forget it and the secrets layer is unrecoverable (re-issue API keys).
