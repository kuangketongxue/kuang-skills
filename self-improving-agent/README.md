# self-improving-agent

Curate Claude Code's auto-memory into durable, enforceable project knowledge — and back up the whole "self" to a private repo you can restore after a PC reset.

## What it does

- **Curates** `MEMORY.md`: finds promotion candidates (patterns that recur 2-3x), stale entries, and consolidation opportunities.
- **Promotes** proven learnings to `CLAUDE.md` or `.claude/rules/` — enforced rules, not just notes.
- **Extracts** recurring debugging solutions into standalone, reusable skills.
- **Reviews the full session transcript** (not just MEMORY.md), so today's mistakes don't get lost to `/compact`.
- **Backs up** CLAUDE.md + auto-memory + playbooks + encrypted secrets to the private `claude-memory-backup` repo in one Git Data API commit.
- **Restores** everything after a PC reset and decrypts secrets (incl. `web-search.env`) with your passphrase.

## Attribution

Fork from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) (MIT). This fork adds the **Backup & Restore** section in `SKILL.md`, covering the `claude-memory-backup` private repo's `/si:backup` / `/si:restore` flow — including encrypting `web-search.env` into the repo and auto-restoring it on decrypt.

Upstream ships the memory architecture, the promotion lifecycle, and the `extract_transcript.py` script. This fork keeps all of that intact and only adds the backup/restore layer on top.

## Install

From this repo (preferred — gets the backup/restore customization):

```bash
cp -r self-improving-agent ~/.claude/skills/self-improving-agent
```

Or install upstream from the marketplace, then overwrite `SKILL.md` with this fork's version to add backup/restore:

```
/plugin marketplace add alirezarezvani/claude-skills
/plugin install self-improving-agent@claude-code-skills
```

## Upstream

[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — the original self-improving-agent skill.

## License

MIT. Upstream © 2025 [Alireza Rezvani](https://github.com/alirezarezvani). This fork © 2026 kuangketongxue.
