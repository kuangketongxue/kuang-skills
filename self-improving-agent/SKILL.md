---
name: "self-improving-agent"
description: "Curate Claude Code's auto-memory into durable project knowledge. Analyze MEMORY.md for patterns, promote proven learnings to CLAUDE.md and .claude/rules/, extract recurring solutions into reusable skills. Use when: (1) reviewing what Claude has learned about your project, (2) graduating a pattern from notes to enforced rules, (3) turning a debugging solution into a skill, (4) checking memory health and capacity."
---

# Self-Improving Agent

> Auto-memory captures. This plugin curates.

## ⚠️ 第一步永远是：完整回顾本次会话（强制，不可跳过）

运行本 skill 的任何命令前，必须先做这一步——**分析对象不只是 MEMORY.md 文件，还包括当前对话的全部内容**：

1. **从头到尾回顾本次会话（用脚本拉全量，不受 /compact 影响）**：先运行提取脚本 `python ~/.claude/skills/self-improving-agent/scripts/extract_transcript.py --all --out /tmp/si-transcript.md`（**Windows 本机用绝对路径** `python "C:/Users/kuang/.claude/skills/self-improving-agent/scripts/extract_transcript.py" --all --out "C:/Users/kuang/AppData/Local/Temp/si-transcript.md"`——`~` 和 `/tmp` 在 Windows python 不认，会 FileNotFoundError）。neat-freak skill 也复用此脚本，读 Claude Code 会话 transcript jsonl。transcript jsonl 是磁盘原始会话记录，**compact 只压缩 LLM 上下文窗口、不动磁盘文件**，所以脚本能拉到 compact 前被"忘掉"的全部真实用户输入（不传任何参数时默认扫全部 jsonl + 覆盖 compact 前后；实际 argparse 默认 `n=None` → `discover_jsonl(n=None)` 返回全部文件，行为等价于 `--all`；按消息 timestamp 只保留最近 24 小时——收尾聚焦本次会话不扫历史全量，曾因无时间窗扫到 850 条 / 跨 58 个 jsonl 18 天浪费上下文；`--hours N` 调时间窗 / `--hours 0` 关闭过滤取全量历史（跨天全量审计才用，输出大务必 `--out` 写文件分段 Read）；`--n N` 调文件数量；`<path>` 指定单文件）。脚本过滤掉 tool_result / system-reminder 注入 / task-notification / skill body 全文（按 `isSidechain`/`isMeta` 标志跳过系统注入——这是过滤 skill body 污染的最可靠标志，标签检测会漏因为注入是纯文本无 `<command-message>` 标签），只留真实用户文本 + 用户调过的命令名。**Read 输出文件全量回顾**，逐条核对用户提过的每个需求、每条纠正（如"不要说英文""这个选项不要出现"）、每个踩坑与修复、每次用户表达的不满或偏好。**禁止只靠会话内的摘要或最近几轮**——compact 摘要会丢细节（曾漏飞书字段规则、漏"用 frontend-design"等明确需求），transcript 原文不丢。
2. **对照检查三个问题**：
   - 本次会话里有哪些经验/纠正**还没写进** MEMORY.md / playbook / CLAUDE.md？（漏记 → 立即补）
   - 已有记忆里有没有被本次会话证伪的条目？（过时 → 就地修正或删除）
   - 有没有重复出现 2 次以上的模式值得晋升为规则/skill？（候选 → 走 promote 流程）
3. **输出回顾清单**再执行具体命令：列出「新发现 N 条、修正 M 条、晋升候选 K 条」，让用户能看到本次沉淀了什么。

只读 MEMORY.md 不看对话 = 只整理旧账、漏掉今天刚犯的错，这是本 skill 最大的失败模式。

---

Claude Code's auto-memory (v2.1.32+) automatically records project patterns, debugging insights, and your preferences in `MEMORY.md`. This plugin adds the intelligence layer: it analyzes what Claude has learned, promotes proven patterns into project rules, and extracts recurring solutions into reusable skills.

## Quick Reference

| 动作 | 怎么执行 |
|------|----------|
| （所有动作） | **先完整回顾本次会话**（见上方强制第一步），再执行下述动作 |
| memory-review / memory-status | `python "C:/Users/kuang/.claude/skills/self-improving-agent/scripts/memory-audit.py" --memory <MEMORY.md路径>` —— 一次跑出健康看板（行数 / topic 文件）+ 晋升候选 + 死链 / 超限。exit 0 = clean；1 = blocking（DEAD_LINK / OVER_LIMIT）；DUPLICATE / STALE 为 advisory |
| backup | `PP='你的passphrase' bash "C:/Users/kuang/.claude/backups/work/backup.sh"` —— 单 commit 推 CLAUDE.md + memory + playbooks + 加密密钥到 `claude-memory-backup` 私有仓（Git Data API，不克隆）。完整 allowlist / 加密流程见 [backup-restore.md](references/backup-restore.md) |
| restore | PC 重置后：`git clone git@github.com:kuangketongxue/claude-memory-backup.git`，在仓库根目录跑 `PP='你的passphrase' bash restore.sh` 一键复原。完整 SOP 见 [backup-restore.md](references/backup-restore.md) |
| promote（手动） | 从 MEMORY.md 提炼重复 ≥ 2-3 次的模式，写成规则进 `~/.claude/CLAUDE.md`（全局）或 `.claude/rules/<scope>.md`（按文件类型 scoped）。晋升后从 MEMORY.md 删原条目腾空间。详见下方 Promotion lifecycle |
| extract（手动） | 把复用模式封装成新 skill：`~/.claude/skills/<name>/SKILL.md`（带 frontmatter）+ `references/` + examples |
| remember（手动） | 直接 Write 记忆文件：`~/.claude/projects/<path>/memory/MEMORY.md`（主索引）或同目录 `<topic>.md`（topic 溢出） |

## How It Fits Together

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code Memory Stack                │
├─────────────┬──────────────────┬────────────────────────┤
│  CLAUDE.md  │   Auto Memory    │   Session Memory       │
│  (you write)│   (Claude writes)│   (Claude writes)      │
│  Rules &    │   MEMORY.md      │   Conversation logs    │
│  standards  │   + topic files  │   + continuity         │
│  Full load  │   200行/25KB（先到为止）│   Contextual load      │
├─────────────┴──────────────────┴────────────────────────┤
│              ↑ 手动晋升            ↑ memory-audit       │
│         Self-Improving Agent (this plugin)               │
│              ↓ 手动封装 skill    ↓ 手动 Write          │
├─────────────────────────────────────────────────────────┤
│  .claude/rules/    │    New Skills    │   Error Logs     │
│  (scoped rules)    │    (extracted)   │   (auto-captured)│
└─────────────────────────────────────────────────────────┘
```

## Memory Architecture

### Where things live

| File | Who writes | Scope | Loaded |
|------|-----------|-------|--------|
| `./CLAUDE.md` | You (+ 手动晋升) | Project rules | Full file, every session |
| `~/.claude/CLAUDE.md` | You | Global preferences | Full file, every session |
| `~/.claude/projects/<path>/memory/MEMORY.md` | Claude (auto) | Project learnings | First 200 lines or 25KB (whichever first) |
| `~/.claude/projects/<path>/memory/*.md` | Claude (overflow) | Topic-specific notes | On demand |
| `.claude/rules/*.md` | You (+ 手动晋升) | Scoped rules | When matching files open |

### The promotion lifecycle

```
1. Claude discovers pattern → auto-memory (MEMORY.md)
2. Pattern recurs 2-3x → 手动跑 memory-audit 标记为 promotion candidate
3. You approve → 手动晋升进 CLAUDE.md or rules/
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

## Backup & Restore

> Full allowlist, encrypt flow, one-commit upload, and reset restore SOP live in [references/backup-restore.md](references/backup-restore.md) — this SKILL.md only keeps the high-level pointer so a PC-reset recovery path is always findable. See also memory file [[claude-memory-backup-repo]].
