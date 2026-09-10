# Promote & Extract — 晋升与封装的操作脚手架

> promote / extract 是本 skill 的两个手动动作。之前只有判据没有脚手架，
> 导致晋升无审计轨迹、封装质量参差。本文件补齐：判据 → 模板 → 落点 → 日志。

## Promote（记忆 → 规则）

### 判据（三条同时满足才晋升）

1. **重复 ≥ 2~3 次**：同一教训在不同会话/不同任务里出现过，单次踩坑不值得。
2. **稳定机制**：讲的是会持续成立的约束，不是某个项目当前阶段的临时状态。
3. **违反有真实代价**：不写下来下次就会再犯错（写"这个项目用 pnpm"这种背景信息留在 MEMORY.md 即可）。

### 落点选择

| 内容性质 | 去向 |
|---|---|
| 跨项目、跨场景都成立的个人偏好/铁律 | `~/.claude/CLAUDE.md`（全局） |
| 只在本项目成立的工作流/命令/红线 | 项目根 `CLAUDE.md` |
| 只在特定文件类型生效（测试/API/前端…） | `.claude/rules/<scope>.md`（带 `paths:` frontmatter） |

### 写法模板（晋升条目）

```markdown
- **<一句话规则>**：<触发条件> 时，<必须/禁止> <动作>。<违反代价或原因，一句话>。
```

好条目是可执行的指令，不是观察记录。❌「发现项目在用 pnpm」✅「包管理一律用 pnpm，不用 npm run，用 pnpm <script>」。

### 晋升后必做（防双份真相）

1. 从 MEMORY.md **删除**原条目（规则层全文加载，不需要第二份指针）。
2. 追加晋升日志（见下）。

## Extract（模式 → skill）

### 判据

- 同一操作流程**跨会话复用 ≥ 3 次**，且步骤足够确定（不是每次都要临场判断）；
- 有可机检的验证方式（脚本/门禁/exit code），否则 skill 只是散文；
- 跨项目成立（单项目专属流程应晋升为项目 CLAUDE.md，不是 skill）。

### 封装清单

```
~/.claude/skills/<name>/
├── SKILL.md          # frontmatter（name/description 带正反触发词）+ 流程 + 输出格式
├── references/       # 大段参考、模板、领域知识（按需加载）
└── scripts/          # 可机检的验证/执行脚本（有 exit code 才算门禁）
```

- description 必须同时写**正向触发词**和**不适用场景**（防止误触发）；
- SKILL.md 只留流程，教学材料进 references/；
- 写完必须实跑一次验证（脚本要跑通，别交付没执行过的命令）。

## 晋升日志（append-only，审计轨迹）

`~/.claude/promotions.md`，每次 promote / extract 追加一条：

```markdown
## YYYY-MM-DD | promote | <一句话标题>
- 来源：<MEMORY.md 条目 / 会话事件>
- 去向：<~/.claude/CLAUDE.md | <项目>/CLAUDE.md | .claude/rules/<x>.md | skills/<name>/>
- 判据：<重复次数 / 场景>
```

作用：下次 review 时先查日志，**防止把已晋升的条目再提一遍**（晋升完从 MEMORY.md 删掉，
没有日志的话几个月后就忘了它去哪了，重复劳动）。
