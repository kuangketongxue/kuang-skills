---
name: "self-improving-agent"
description: "Curate Claude Code's auto-memory into durable project knowledge. Analyze MEMORY.md for patterns, promote proven learnings to CLAUDE.md and .claude/rules/, extract recurring solutions into reusable skills. Use when: (1) reviewing what Claude has learned about your project, (2) graduating a pattern from notes to enforced rules, (3) turning a debugging solution into a skill, (4) checking memory health and capacity."
metadata:
  version: "2.1.0"
  category: memory-curation
---

> **2.1.0（2026-09-10）** 修实证缺陷 + 对齐用户铁律：① `memory-audit.py` 补齐 SKILL.md 一直承诺却从未实现的「晋升候选」——新增 `PROMOTE_CANDIDATE` / `ALREADY_PROMOTED` / `BUDGET`(70% 预警) 三组输出，并把 docstring 的 exit code 口径改正（ORPHAN 也是阻塞项）；② promote 增加硬要求「必须写 `~/.claude/promotions.md` 日志」——审计发现该日志 0 条记录而已晋升 ≥7 条，现按记忆里的真实日期回填；③ 新增「与用户铁律的接口」段（双卡片制 / 红线 / 确定性验证 / 分工 / 70% 预算）；④ `extract_transcript.py` 实现此前只在文档字符串里承诺的跨会话 `requirement_ledger.json`，「被顶掉」需求不再依赖运气被看见；⑤ 与 neat-freak 重复的「第一步」块统一并标注同源约束。

# Self-Improving Agent

> Auto-memory captures. This plugin curates.

## ⚠️ 第一步永远是：完整回顾本次会话（强制，不可跳过）

运行本 skill 的任何命令前，必须先做这一步——**分析对象不只是 MEMORY.md 文件，还包括当前对话的全部内容**：

脚本读 Claude Code 会话 transcript jsonl（磁盘原始记录），**compact 只压缩 LLM 上下文窗口、不动磁盘 jsonl**，所以能拉到 compact 前被"忘掉"的全部真实用户输入。neat-freak skill 复用同一脚本、同一套用法：

1. **用脚本拉全量 transcript（不受 /compact 影响）**：

```
TS=$(date +%Y%m%d-%H%M%S)
python "C:/Users/kuang/.claude/skills/self-improving-agent/scripts/extract_transcript.py" --all --out "C:/Users/kuang/AppData/Local/Temp/si-transcript-$TS.md"
```

- **默认行为**：扫全部 jsonl（argparse 默认 `n=None`，等价 `--all`，覆盖 compact 前后 + 跨 session 连续工作）+ 按消息 timestamp 只保留最近 24 小时（聚焦本次会话，不扫历史全量；曾因无时间窗扫到 850 条 / 跨 58 个 jsonl 18 天浪费上下文）；按 `isSidechain`/`isMeta` 标志过滤 tool_result / system-reminder 注入 / task-notification / skill body 全文（这是过滤 skill body 污染的最可靠标志，标签检测会漏），只留真实用户文本 + 用户调过的命令名
- **参数**：`--hours N` 调时间窗（`--hours 0` 关闭过滤取全部历史，仅用户明确要跨天全量审计时用，输出大务必 `--out` 写文件分段 Read）；`--n N` 调文件数量；`<path>` 指定单文件；`--no-ledger` 关闭跨会话 ledger
- **Windows 必读**：`~` 和 `/tmp` 在 Windows python 不认（FileNotFoundError），命令里必须写 `C:/...` 绝对路径
- **临时文件卫生**：输出含全对话，属敏感残留（含历史粘贴过的明文 key/passphrase，见 [[transcript-plaintext-key-risk]]）——文件名带时间戳避免碰撞/预测，**回顾完成、结论落盘后立即删除**
- **跨会话未闭环需求（ledger）**：脚本用 `~/.claude/state/requirement_ledger.json` 跨会话累计需求状态，输出「跨会话未闭环需求」段——列出更早会话提出、至今仍 ⏳ 的需求，即「被顶掉」候选。**这是会话内检测看不见的盲区**：提出它的 jsonl 早已在 24h 时间窗之外。首次使用建议对该项目跑一次 `--hours 0` 建立基线
- **限制**：跨 cwd 的会话不覆盖（按 cwd 分组），列为限制告知用户

> ⚠️ **本块与 `neat-freak/SKILL.md` 的同源块必须逐字一致。** 两处重复是本 skill 已知的维护负债——脚本已用 `_shared/extract_transcript.py` 去重，散文还没去重，历史上已经漂移过一次（一份多了「限制」、一份多了「范围例外」）。改这里必须同步改那一份；只改一处就是分叉。

2. **Read 输出文件全量回顾**，逐条核对：用户提过的每个需求、每条纠正（如"不要说英文"）、每个踩坑与修复、每次不满或偏好。**禁止只靠会话内摘要或最近几轮**——compact 摘要会丢细节（曾漏飞书字段规则、漏"用 frontend-design"等明确需求），transcript 原文不丢。
3. **对照检查三个问题**：
   - 本次会话里有哪些经验/纠正**还没写进** MEMORY.md / playbook / CLAUDE.md？（漏记 → 立即补）
   - 已有记忆里有没有被本次会话证伪的条目？（过时 → 就地修正或删除）
   - 有没有重复出现 2 次以上的模式值得晋升为规则/skill？（候选 → 走 promote 流程）
4. **输出回顾清单**再执行具体命令：列出「新发现 N 条、修正 M 条、晋升候选 K 条」，让用户能看到本次沉淀了什么。

只读 MEMORY.md 不看对话 = 只整理旧账、漏掉今天刚犯的错，这是本 skill 最大的失败模式。

**范围例外**：`backup` / `restore` 动作**跳过**本步——它们是纯运维操作（打包/还原既有知识），不产生新的待沉淀内容；跑全量回顾纯属浪费上下文。其余动作（review / promote / extract / remember）必须先回顾。

## 与用户铁律的接口（执行时按这个判，不要另立标准）

本 skill 会改规则层文件，是本机权限面最大的 skill 之一，因此把用户 `~/.claude/CLAUDE.md` 里相关的铁律钉在这里：

- **决策交互一律双卡片制**：凡是要用户拍板的（哪些晋升、删哪条、改哪条规则、要不要推公开仓），走 AskUserQuestion——卡片 1 是实质选项（≤4 个满编、推荐项标 `(推荐)` 放第一），卡片 2 是三体通道（`这是计划的一部分`/`主不在乎`/`前进四`/`本次不走`，只表达力度，与卡片 1 正交）。**边界项、自己能判断的先例自己处理掉**，甩进卡片就是抛注意力琐碎（见 [[dont-dump-attention-items]]）。待决 >4 个改纯文本列全量 + 文末附三梗。
- **红线先问**：`git push`、公开发布（含推 `kuangketongxue/kuang-skills` 公开仓）、改密钥/token、删用户真实数据，一律先问；`~/.claude/settings.json` 一律不动（连加字段也不行）。常规的 MEMORY.md 增删改与晋升进本地 CLAUDE.md 属低风险可逆操作，按用户「自主操作」授权直接做。
- **确定性验证**：晋升或封装完必须实跑一次并给出确定性证据（脚本 exit code、读回具体行、独立 grep），不能交付没执行过的命令，也不能凭"应该没问题"下结论（用户 CLAUDE.md「确定性验证纪律」）。
- **分工**：本 skill 的产出多是分析与判断，主对话做；但真正的批量实现（一次改多个规则文件、批量重写 memory）按用户分工约定派 subagent，并在验收时独立读回。用户说"搞定完/亲自做/你来跑"时改为主对话亲自执行。
- **记忆预算 70%**：`BUDGET` 报出 ≥70% 时，本次就要交付腾空间动作（晋升走 promote 并从索引行删除、合并重复、让已完成的一次性任务记忆下架），并把读数写进汇报。不要等到撞 100%——那时自动加载已经在静默截断。

---

Claude Code's auto-memory (v2.1.32+) automatically records project patterns, debugging insights, and your preferences in `MEMORY.md`. This plugin adds the intelligence layer: it analyzes what Claude has learned, promotes proven patterns into project rules, and extracts recurring solutions into reusable skills.

## Quick Reference

| 动作 | 怎么执行 |
|------|----------|
| （所有动作，除 backup/restore） | **先完整回顾本次会话**（见上方强制第一步），再执行下述动作 |
| memory-review / memory-status | `python "C:/Users/kuang/.claude/skills/self-improving-agent/scripts/memory-audit.py" --memory <MEMORY.md路径>` —— 一次跑出健康看板（行数 / topic 文件）+ **晋升队列** + 死链 / 超限。exit 0 = clean；1 = blocking（DEAD_LINK / ORPHAN / OVER_LIMIT）。省略 `--memory` 时自动发现当前 cwd 对应的 MEMORY.md |
| └ 输出怎么读 | **7 组**：阻塞项 `DEAD_LINK` / `ORPHAN` / `OVER_LIMIT`；advisory `DUPLICATE` / `STALE` / **`BUDGET`** / **`PROMOTE_CANDIDATE` + `ALREADY_PROMOTED`**。后两组就是本 skill 的作业队列：`PROMOTE_CANDIDATE`（topic 文件出现 ≥2 个重复模式标记，或自称"应晋升"）→ 走 promote 流程；`ALREADY_PROMOTED`（规则本体已进 CLAUDE.md/rules/ 但仍占索引行）→ **默认用户有意留证据，不要擅自删**，只在报告里点出。`BUDGET` 按用户口径在 **70%** 预警（不是撞上限才说——那时自动加载已经静默截断了；2026-09-10 实测 MEMORY.md 已 72%）|
| backup | `bash "C:/Users/kuang/.claude/backups/work/backup.sh"` —— **不传 PP**，脚本自动从 DPAPI 读原 PP（手动传 PP 会用新 PP 加密覆盖、破坏还原链）。单 commit 推 CLAUDE.md + memory + playbooks + 加密密钥到 `claude-memory-backup` 私有仓（Git Data API，不克隆）。完整 allowlist / 加密流程见 [backup-restore.md](references/backup-restore.md) |
| restore | PC 重置后：`git clone git@github.com:kuangketongxue/claude-memory-backup.git`，在仓库根目录跑 `PP='你的passphrase' bash restore.sh` 一键复原。完整 SOP 见 [backup-restore.md](references/backup-restore.md) |
| promote（手动） | 从 MEMORY.md 提炼重复 ≥ 2-3 次的模式晋升为规则：全局进 `~/.claude/CLAUDE.md`，项目进项目 `CLAUDE.md`，按文件类型生效进 `.claude/rules/<scope>.md`。晋升后从 MEMORY.md 删原条目腾空间。**判据、写法模板、晋升日志见 [promote-extract.md](references/promote-extract.md)**——没有日志的晋升会忘记去向、反复重提。**晋升必须追加 `~/.claude/promotions.md` 日志，这是硬要求不是可选项**：2026-09-10 审计发现该日志自建立起 0 条记录，而 MEMORY.md 里至少有 7 条写着"已晋升进 CLAUDE.md"——promote-extract.md 自己警告的"没有日志下次会重复提"已经真实发生过，现已回填 |
| extract（手动） | 把复用模式封装成新 skill：`~/.claude/skills/<name>/SKILL.md`（带 frontmatter）+ `references/` + `scripts/`。**判据、封装清单、验证要求见 [promote-extract.md](references/promote-extract.md)** |
| remember（手动） | 直接 Write 记忆文件：`~/.claude/projects/<path>/memory/MEMORY.md`（主索引）或同目录 `<topic>.md`（topic 溢出） |
| 跨会话需求闭环（ledger） | `extract_transcript.py` 输出「跨会话未闭环需求」段：更早会话提出、至今 ⏳ 的需求（即"被顶掉"候选）。ledger 在 `~/.claude/state/requirement_ledger.json` 按需求文本哈希跨会话累计；`--hours 0` 跑一次可给某项目建立历史基线（否则 ledger 只知道它运行之后见过的需求），`--no-ledger` 纯只读 |

## 记忆栈全景与晋升原理

架构图、各文件加载方式、promotion lifecycle、"为什么晋升=毕业"等教学材料在
[how-it-works.md](references/how-it-works.md)——执行时不需要，理解或讲解时读它。

一句话版：MEMORY.md 是草稿区（200 行/25KB 截断加载），CLAUDE.md / rules/ 是生效规则（全文加载）；
本 skill 的职责就是把草稿区里反复验证的判断"毕业"到规则层，并腾出空间。

## Backup & Restore

> Full allowlist, encrypt flow, one-commit upload, and reset restore SOP live in [references/backup-restore.md](references/backup-restore.md) — this SKILL.md only keeps the high-level pointer so a PC-reset recovery path is always findable. See also memory file [[claude-memory-backup-repo]].
