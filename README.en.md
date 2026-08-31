<div align="center">

[中文](./README.md) · **English**

# 🧰 Kuang Skills

#### Claude Code skills I use every day, all open-sourced here

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-8-10B981?style=for-the-badge)](#skills)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)

</div>

Every skill here has been battle-tested in my daily projects before being open-sourced. Nothing fancy — just a few genuinely useful things.

Each directory is a complete, self-contained skill (SKILL.md + scripts/ + references/) that any Agent supporting the skills standard can load.

---

## 📋 Skills

| Name | One-liner |
|---|---|
| 🚀 [**github-auto-release**](#-github-auto-release) | One command: local project → fully dressed public GitHub repo (privacy scan, About/topics, bilingual badge-wall README, CHANGELOG, LICENSE, Release) |
| ⚔️ [**adversarial-debate**](#️-adversarial-debate) | Steelman proponent × dedicated opponent × judge bound only by objective reality — answers "can my goal actually be achieved?" |
| 🧹 [**neat-freak**](#-neat-freak) | Run `/neat` after work: auto-sync project docs, CLAUDE.md, and agent memory; audit whether rules are actually followed |
| 💬 [**crazy-wechat-auto**](#-crazy-wechat-auto) | Search, write, and auto-publish WeChat Official Account articles to drafts |
| 📚 [**feishu-note-appender**](#-feishu-note-appender) | Format reading notes and append them to a Feishu/Lark Wiki, synced locally |
| 📬 [**agent-mail-readiness**](#-agent-mail-readiness) | Mail-channel readiness check for proactive agents |
| 🔍 [**web-search**](#-web-search) | Five parallel engines: Tavily / Firecrawl (+ Developer Index) / Zhihu; Chinese queries always pair with Zhihu; API keys live in local env, never in the repo |
| 🧠 [**self-improving-agent**](#-self-improving-agent) | Curate Claude Code's auto-memory into durable project rules/skills; back up to a private repo and restore after a PC reset |

---

## 📦 Install

In Claude Code, just say:

```
Install this skill: https://github.com/kuangketongxue/kuang-skills/tree/main/<skill-name>
```

Or copy any skill folder into `~/.claude/skills/<skill-name>/`.

---

## ✨ Details

### 🚀 github-auto-release

Most repos get pushed half-naked: code up, no description, no release. This closes the whole loop in one command — privacy scan first, then repo creation, About/topics, bilingual badge-wall READMEs (EN + 中文, optional 日本語), CHANGELOG/package.json/LICENSE scaffolds, and an initial Release. Works even when git push is blocked (`--api-push` uploads via the Contents API).

```bash
python scripts/github_release.py \
  --repo "you/your-project" --path ./project \
  --title "Title" --desc "Description" \
  --homepage "https://site.dev" --topics "python,cli"
```

See [github-auto-release/README.md](./github-auto-release/README.md).

### ⚔️ adversarial-debate

When you ask AI "is this plan feasible?", the two most common useless answers are flattery ("great idea!") and fence-sitting ("both sides have a point"). This skill forces three roles: a steelman proponent, a dedicated opponent attacking the strongest version, and a judge that must rule yes / no / conditionally with confidence and key variables.

See [adversarial-debate/SKILL.md](./adversarial-debate/SKILL.md).

### 🧹 neat-freak

Knowledge closeout for agents: reconciles docs, CLAUDE.md/rules files, and agent memory against what the code actually does. Cross-platform.

See [neat-freak/README.md](./neat-freak/README.md).

### 💬 crazy-wechat-auto

One-stop WeChat Official Account automation: article search, long-form writing, draft-box publishing via API with fixed template support.

See [crazy-wechat-auto/SKILL.md](./crazy-wechat-auto/SKILL.md).

### 📚 feishu-note-appender

Formats notes (date + title + body), appends to a Feishu reading-notes Wiki, and syncs a local copy. Requires lark-cli.

See [feishu-note-appender/SKILL.md](./feishu-note-appender/SKILL.md).

### 📬 agent-mail-readiness

Readiness check for the mail channel before a proactive agent sends notifications.

See [agent-qq-auto/SKILL.md](./agent-qq-auto/SKILL.md).

---

### 🔍 web-search

Five parallel search engines: Tavily, Firecrawl (incl. Developer Index for issue/PR/docs lookup), and Zhihu OpenAPI (in-site + global). Chinese queries always pair with Zhihu for better recall on Chinese resources (GitHub repos, net-disk materials, study notes). API keys are read from `~/.claude/.secrets/web-search.env` locally — **the repo ships key-free**; bring your own keys after a reset.

```bash
python3 scripts/tavily-search.py '{"query":"Claude Code"}'
python3 scripts/firecrawl-dev.py '{"query":"npm install error"}'
python3 scripts/zhihu-search.py '{"query":"gaokao study tips"}'
```

See [web-search/SKILL.md](./web-search/SKILL.md).

### 🧠 self-improving-agent

Curates Claude Code's auto-memory (MEMORY.md) into enforceable project knowledge: analyzes patterns, graduates proven learnings to CLAUDE.md or `.claude/rules/`, and extracts recurring debugging solutions into standalone skills. Includes `/si:backup` and `/si:restore` — restore the whole "self" from the private `claude-memory-backup` repo after a PC reset (encrypted web-search keys ride along).

See [self-improving-agent/README.md](./self-improving-agent/README.md)。

---

## License

MIT © 2026 kuangketongxue — individual skill folders keep their original LICENSE files.
