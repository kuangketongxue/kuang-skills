---
name: neat-freak
description: >
  实时错误记录 + 会话复盘 + 知识库洁癖审查。三合一 skill：
  (1) 实时捕获：命令失败/用户纠正/知识gap 发生时立刻写 ERRORS.md 或 LEARNINGS.md；
  (2) 复盘沉淀：用户说"/neat""复盘""打分后"时触发，提取本次 session 的教训/错误/特质，写入 .learnings/，更新 memory/MEMORY.md 索引；
  (3) 洁癖审查：CLAUDE.md/docs/ 尺寸 & 过期检查、记忆链接验证、跨层同步。
agent_created: true
---

# Neat-Freak：实时记录 + 复盘沉淀 + 洁癖审查

> **Cross-platform Agent Skill** — Claude Code · OpenAI Codex · OpenCode · OpenClaw 通用。
> 跨平台 SKILL.md，遵循开放 Agent Skill 规范。

你是一个**知识库编辑**，不是记录员。记录员只会往后追加，编辑会审查全局、合并重复、修正过期、删除废弃。你的工作是让整个项目的知识体系始终保持**干净、准确、对新人友好**的状态——像有洁癖一样。

---

## 三大模式（按触发时机分）

| 模式 | 触发时机 | 入口 | 核心产出 |
|------|----------|------|----------|
| **实时捕获** | 会话进行中，每次失败/纠正后立刻触发 | 本 skill §"实时捕获" | ERRORS.md / LEARNINGS.md 单条追加 |
| **复盘沉淀** | 对话末尾，用户说"/neat""复盘""打分后" | 本 skill §"复盘工作流" | session 文件 + MEMORY.md 索引更新 |
| **洁癖审查** | 阶段结束/用户说"收尾""同步一下""整理文档"，或每次复盘之后顺带跑 | 本 skill §"洁癖审查清单" | CLAUDE.md/docs/ 修正 + 尺寸控制 |

**默认行为**：每次对话结尾先跑"复盘沉淀"，再跑一次"洁癖审查"（30 秒能跑完）。实时捕获是会话进行中随发的，不等结尾。

---

## 实时捕获：会话进行中的错误/教训记录

### 触发（任一命中即写）
- 命令/操作失败（lark-cli 报错、API 调用失败、Bash 命令报错）
- 用户纠正（"不对"/"应该是…"/"你搞错了"）
- 外部工具失败（WARP 断连、Read 工具失败、网络超时）
- 知识过时 / 发现更好方案

### 写入格式（精简，1-3 行）

**ERRORS.md**：
```markdown
## [ERR-YYYYMMDD-XXX] 标题
**Priority**: high/medium | **Status**: pending
**One-line**: 一句话
- Root cause: 为什么
- Fix: 怎么修 / Pattern-Key: xxx.repeating_thing
```

**LEARNINGS.md**：
```markdown
## [LRN-YYYYMMDD-XXX] 标题
**Priority**: high/medium | **Status**: pending
**One-line**: 一句话教训
- Fix/Pattern: 怎么复用 / Pattern-Key: xxx
```

### 规则
- **没有新内容就不写**——每次失败都写会淹没真正的高频 pattern
- **已解决 + 已提升的** 移入 `.learnings/ARCHIVE.md`
- **不写**"Logged"/"Area"/"Metadata"等冗余字段
- **`ERR-`/`LRN-` 编号互不重用**——错过一次不要补
- **`Pattern-Key`** 跨 session 复用：同一 Pattern-Key 出现 2 次以上，这是防复发核心
- **合并优于追加**：先 grep LEARNINGS.md 看有没有同 Key 的，有就合并升级，没有才新建
- **`Priority: high`** = 会再次踩且代价大的（精确匹配误删、VPN 不重试）；**medium** = 单次但有价值；**low** = 经验性

### 完成输出
`已记录：ERR-001 / LRN-001（简要）`

---

## 复盘沉淀：对话末尾的 session 复盘

### 触发
"打分后"/"复盘"/"沉淀经验"/"总结"/"/neat"

### 工作流

#### 1. 读现有经验
读 `.learnings/ERRORS.md` + `.learnings/LEARNINGS.md`（会话开头已读，不重复）。

#### 2. 提取本次新增
扫本次 session，找出：
- **错误** → 写入 ERRORS.md（已在实时捕获里写了的不重复）
- **教训** → 写入 LEARNINGS.md
- **特质**（仅当观察到的**新的、可复用的**行为模式才写）

#### 3. session 文件写入格式
```markdown
# Session YYYYM-DD-主题
> 当天打分：XX/100
> 任务：一句话任务描述

## 背景
一段话：本次在做什么

## 完成清单
分表/分功能列出改动（带数据）

## 新特质
### T-XXX：特质名 | 背景 + 用户原话 + 结果（3 行以内）

## 经验/教训
- Pattern-Key + 教训 1 行

## 验证（本次无法验证的列入待验证清单）
- [ ] xxx

## 关联
- T-XXX 关联到其他 T
```

#### 4. 更新 MEMORY.md 索引
只在新增文件时更新索引。格式：
```markdown
- [主题](session-YYYYMMDD-主题.md) — T-XXX~T-YYY（N条）
```

**MEMORY.md 尺寸 ≤ 150 行**。超过先清理：> 30 天的 session 保留一行索引 + "仅读索引"标注。

#### 5. grep 验证（必跑）
```bash
grep -c "## 特质 T-" <session-file>
grep -c "验证" <session-file>    # 必须 ≥ Trait 数量
```
Trait 数量和验证数量必须对不上。

---

## 洁癖审查：AGENTS.md / AGENTS.md / docs/ 健康度检查

### 触发
"收尾"/"同步一下"/"整理文档"/"整理一下"/"这个阶段做完了"/"新人能直接上手"。或**每次复盘沉淀后默认跑一次**。

### 三类知识，三种受众（不要混淆）

| 位置 | 受众 | 职责 |
|------|------|------|
| Agent 记忆系统 | Agent 跨会话复用 | 个人偏好、项目事实、跨项目 reference |
| 项目根 `AGENTS.md` / `AGENTS.md` | 当前项目 AI | 项目约定、结构、红线、环境变量、路由清单 |
| 项目 `docs/` + `README.md` | **其他人**（人类/下游/未来 AI） | 接入指南、架构图、运维手册、交接说明、API 参考 |

AGENTS.md 写"新增了 device flow 五个路由" ≠ docs/integration-guide 里"下游怎么接这套 flow" —— **两份都要写，角色不混**。

### AGENTS.md / AGENTS.md 是规则手册，不是变更日志
最常见的翻车：每次开发完在顶部加一段 blockquote 历史叙事。
判断标准：**下次 AI 写代码时如果没看到这条，会不会犯错？**
- ✅ 进：硬边界规则、禁止事项、命令速查、权限模型、协作流程、踩坑警示、深入文档指针表
- ❌ 不进：历史叙事、详细机制说明、单次事故复盘、bug fix 流水账

### 审查清单（每项必过）

**尺寸**：
- `wc -l AGENTS.md` ≤ 300 行（超了先删叙事段）
- `wc -l MEMORY.md` ≤ 150 行
- 单条 memory 文件 ≤ 100 行

**相对时间清零**：
```bash
grep -nE "今天|昨天|刚刚|最近|上周|today|yesterday|recently" <file>
```
只在用户原话引用里接受，叙述里不能有。

**链接有效性**：MEMORY.md 里每个 `[link](file.md)` 指向真实存在的文件。

**重复/冲突**：grep LEARNINGS.md 看同 Pattern-Key 是否已有条目。

**历史叙事段**：
```bash
grep -nE "^\s*> (202[0-9]|2026-)" AGENTS.md
```
只有明确的"规则引用历史"才保留（如"2026-07-18 教训：精确匹配误删 360 条"），叙事体段落删。

### 完成输出
```
## 洁癖审查完成
- 尺寸：AGENTS.md xx 行 / MEMORY.md xx 行（OK / 超 xx 行 → 已清理）
- 相对时间：0 处残留
- 重复/冲突：0 处
- 链接失效：0 处
- 未处理：xxx（需要用户确认）
```

---

## 执行流程（7 步）

### 第零步：尺寸体检（防膨胀）

任何同步动作之前，先 `wc -l` 关键文件：

| 文件 | Soft limit | 超过怎么办 |
|------|-----------|------------|
| `CLAUDE.md` / `AGENTS.md` | ~300 行 / ~15KB | 先做精简：扫顶部 blockquote / 历史叙事段 → 删 / 迁 docs |
| 记忆索引（如 `MEMORY.md`） | ~150 行 | 找已被新版本取代的、单次事故复盘、详细机制可读代码代替的 → 删 |
| 单条 memory 文件 | ~100 行 | 拆成多条或删 |
| `docs/<single>.md` | ~1500 行 | 切分成多文件，加目录索引 |

**超尺寸是这个 skill 的最高优先级，大于"补本次会话漏掉的同步"。**

### 第零步B：垃圾文件清理（新增，强制）

清理本次对话产生的临时/垃圾文件，防止占用空间和污染工作目录。

**执行流程**：
1. 回顾本次对话中所有 Write / Edit / 文件创建操作，列出生成的非项目文件
2. 判断标准：
   - **临时脚本**（`__*.py`、`_*.py`、`__*.json`、`_*.json`、`__*.txt`）→ 删
   - **测试文件**（对话中创建用于调试/验证的一次性文件）→ 删
   - **结构导出**（`field-list`/`record-list` 的 JSON 导出）→ 删
   - **项目文件**（`CLAUDE.md`、`README.md`、源文件修改）→ 保留
3. 用 `ls/Get-ChildItem` 按命名模式扫描常见位置（`Desktop/`、项目根目录），确认无残留
4. 在"第六步：变更摘要"中列出清理结果

**禁止清理**：
- `.gitignore`、`CLAUDE.md`、`README.md`、`LICENSE`、`requirements.txt` 等合法项目文件
- 用户明确说过要保留的文件

### 第一步：盘点现状（强制机械式枚举，不能跳过）

**先做 ls，再做判断。**

1. 列出 agent 的记忆文件（如有）：
   - Claude Code：`ls ~/.claude/projects/<...>/memory/` 并读 `MEMORY.md` 及所有被引用的 `.md`
   - Codex / OpenCode / 其他：找该 agent 的等价位置（见 references/agent-paths.md）
2. 对本次对话涉及的**每一个项目**：
   - `ls <project-root>/` → 确认根目录结构
   - `ls <project-root>/docs/ 2>/dev/null` → **枚举所有 docs**（缺失也要确认）
   - `find <project-root> -maxdepth 2 -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*"` → 兜底抓散落的 .md
   - 读 `README.md`、`CLAUDE.md` / `AGENTS.md`、每一个 `docs/*.md`
3. 读全局 agent 配置（若有，如 `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）
4. 回顾本次对话全部内容
5. 扫描 GitHub（gh CLI 必须已认证，不可用则跳过并在摘要说明），两路并行：
   - **第一路：我的仓库 + 我的 star**
     - `gh repo list --limit 100 --json name,description,updatedAt,stargazerCount,primaryLanguage,url` → 全量自有仓库
     - `gh api --paginate user/starred -q '.[] | {name: .full_name, stars: .stargazers_count, lang: .language, desc: .description, topics: .topics}'` → 全量 star
   - **第二路：GitHub 全站搜索**（按 star 排序取前 5）
     - 提取本次对话的 2-3 个核心关键词
     - `gh search repos "关键词1 关键词2" --sort stars --limit 5 --json fullName,description,stargazersCount --jq '.[] | "\(.fullName) | ★\(.stargazers_count) | \(.description[0:60] // "N/A")"'`
   - **目标**：判断这些仓库有没有对本次对话有帮助的项目（参考/复用/直接用）

**输出一张文件清单**（内部用，不用给用户看），对每个文件标：「评估过 / 要改 / 不用改」。**漏一个不行**。

### 第二步：识别变更——用"变更影响矩阵"思考

**不要只看对话增量有什么新事实，要看新事实会波及哪些文档层级。**

常见模式速览：
- 新增 API / 路由 → CLAUDE.md 路由清单 + integration-guide + architecture 的 Routes
- 新增 / 改名 环境变量 → CLAUDE.md 环境变量表 + runbook + 下游 integration-guide
- 新增数据库表 → CLAUDE.md + architecture 的 Data Model
- 新增大特性（跨多文件）→ 以上全部 + architecture 新章节 + handoff 已完成清单
- 跨项目改动 → 上下游两边的 docs **都要对齐**
- Base 表结构变更 → 更新 `wiki/topics/` 对应索引文件
- 记忆层面：相对时间→绝对日期、过期事实→改、重复→合并、已完成待办→删

完整映射表见 **[references/sync-matrix.md](references/sync-matrix.md)**。

### 第三步：实际修改（用工具，不只是描述）

你必须**真的用 Edit 修改现有文件、用 Write 创建新文件、用删除命令清理废弃文件**。"我会怎么改"的描述不算完成。

**顺序建议**：先改 docs/（改错影响外部）→ 再改 CLAUDE.md/AGENTS.md → 最后理记忆。

**编辑原则**：

| 原则 | 说明 |
|------|------|
| 减优于加 | CLAUDE.md 净涨幅 >30 行 = 红灯 |
| 合并优于追加 | 新信息是旧信息的更新，改旧条目；先 grep 同关键字 |
| 删除优于保留 | 完成的临时计划、推翻的决策、旧版本记忆 |
| 精确优于冗长 | 一条记忆说清楚一件事，别塞三件 |
| 绝对时间 | 永远 `2026-05-28`，不写"今天"、"最近" |
| 面向读者 | docs/ 读者是外部人，想象对方只有 5 分钟 |
| 受众不混 | CLAUDE.md 不抄 docs/ 全文，docs/ 不写"我记得" |
| 指针不重复 | 同一事实 docs/ 已详写，CLAUDE.md 只在指针表出现一次 |

### 第四步：自检清单（必须逐项过一遍）

改完后逐条检查，打不了勾的**回去补**。

| 分类 | 检查项 |
|------|--------|
| **尺寸/反膨胀** | CLAUDE.md 净涨幅 ≤30 行 · 无 blockquote 历史叙事 · 无抄 docs/ 的机制说明 · 单条 memory ≤100 行 |
| **完整性/反漏改** | 第一步每个文件都判断了"不用改"或"已改" · 记忆索引链接指向存在的文件 · 记忆之间无矛盾 · 路径/命令/环境变量在代码中真实存在 · README 与代码一致 |
| **跨层对齐** | 新增 API 路由：integration-guide + architecture 都有 · 新增环境变量：runbook + 项目根 markdown 都有 · 新增数据库表：architecture + 项目根都有 · 跨项目影响：下游 docs 也改了 |
| **时间合规** | `grep -E "今天|昨天|刚刚|最近|上周|today|yesterday|recently"` 清零 |
| **沉淀** | 个人网站扫描已执行 · 新特质已写入 · 可复用经验已提炼 |

### 第五步：个人特质与经验沉淀（强制，不可跳过）

**无论本次对话内容多简单，以下三个子步骤都必须执行，不得以"没什么新东西"为由省略。**

#### 5a. 个人网站扫描
1. 扫描本次对话全部内容
2. 判断是否有值得加入个人网站的新信息（新产品、成就数据、职业进展、技能提升等）
3. **有** → 列出具体内容并询问用户是否加入，用户确认后真实修改文件
4. **没有** → 明确告知"本次对话无需要加入个人网站的新内容"

#### 5b. 特质识别与写入
1. 回顾本次对话，识别用户表现出的新特质、新偏好、新行为模式
2. 查 `user_traits_unified.md` 最后一个 T 编号，+1 作为新编号
3. 写入 `user_traits_unified.md`
4. **没有新特质** → 说明理由（已有哪个 T 编号覆盖）

#### 5c. 可复用经验提炼与写入
1. 提炼本次对话中产生的方法论、决策经验、避坑指南
2. 写入 `notes/interview-summary.md` 的"可复用经验"章节
3. **没有新经验** → 说明理由

#### 5d. GitHub 活动关联
1. **交叉比对**：将 Step 1 采集的 GitHub 全量数据（star + 自有仓库）与本次对话主题逐一比对
2. **命中** → 在变更摘要中列出相关项目并说明为什么有帮助
3. **不命中** → 说明"本次 GitHub 扫描无相关项目"

### 第六步：变更摘要

在所有文件修改完之后（不是之前），给用户简洁摘要：

```
## 同步完成

### 记忆变更
- 更新：xxx（原因）
- 新增：xxx
- 删除：xxx（原因）

### 文档变更（按项目分组，每个项目列全改动的文件）
- <项目 A>/CLAUDE.md — xxx

### 个人网站
- 有新内容：xxx（已询问用户/已修改） / 无新内容

### 新特质
- Txx：xxx / 无新特质（已有 Tx 覆盖）

### 可复用经验
- xxx / 无新经验

### GitHub 活动关联
- 相关项目：xxx（项目名 → 对本次对话的帮助） / 无相关项目

### 未处理
- xxx（为什么没处理）
```

只列有实际变更的条目。没改的不写。

---

## 通用规则

### 写入原则
- **减优于加**：每次同步净涨幅 > 30 行就是红灯（塞了历史叙事）
- **合并优于追加**：先 grep 有无同 Key/同主题条目，有就升级
- **删除优于保留**：完成的临时计划、推翻的决策、过时的项目记忆、单次事故流水账
- **绝对时间**：写 `2026-04-29`，不写"上周"
- **不做没内容的同步**：无新增 + 文档干净 = 输出"本次无新增"，不硬写

### 禁止
- ❌ 不要写"Logged"/"Area"/"Metadata"等冗余字段
- ❌ 不要每轮都写满 10 步——只在有真实新内容时触发
- ❌ 不要硬凑 trait——只在观察到新的稳定行为模式时才写

### 完成输出模板
```
## 同步完成

### 实时捕获（本次会话中）
- 新增：ERR-001 / LRN-001（简要）

### 复盘沉淀
- 新增：session-YYYYM-DD-主题.md（T-XXX~T-YYY，N 特质）
- 更新：MEMORY.md 索引 +x 行
- 新增：LEARNINGS.md N 条

### 洁癖审查
- 尺寸：AGENTS.md xx 行 / MEMORY.md xx 行 OK
- 相对时间/重复/冲突：0 处
- 历史叙事段：0 处残留

### 个人网站（如有建议）
- 建议写入：xxx

### 未处理
- xxx（原因）
```

---

## 特殊情况

**项目还没有 README 或 CLAUDE.md/AGENTS.md**：判断项目是不是到了"有可运行代码"的阶段。是 → 创建。还在 vibe 阶段 → 跳过，但在摘要里提一句。

**对话没有产生新事实**：审查现有记忆和文档有没有过期 / 冲突 / 相对时间——审查本身就有价值。

**记忆之间出现无法自动判断的矛盾**：列在「未处理」让用户决定。**这是唯一需要用户介入的情况**，其他都自己拍板。

**跨项目改动**：本次对话改了多个项目，每个项目都要跑一次完整的第一步（ls + 读 docs）。不要假设一个项目的 docs 改了，另一个就不用。尤其是上游-下游对接文档（集成指南 / SDK 说明 / API 协议），两边都要对齐。

**发现之前的同步漏了东西**：修掉。不要说"那不是这次对话的事"——你就是这个项目的持续编辑，过去的漏洞也归你管。

## 参考资料

- **[references/sync-matrix.md](references/sync-matrix.md)** — 完整的"变更类型 → 要改哪些文件"映射表
- **[references/agent-paths.md](references/agent-paths.md)** — Claude Code / Codex / OpenCode 各自的记忆与配置路径速查
