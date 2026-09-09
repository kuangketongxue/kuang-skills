# adversarial-debate

Claude Code 技能：**对抗性审查 + 第一性原理的多角色辩论**。正方构建最强支持论证，反方专职对抗驳斥（优先用你自己的原则打你），裁判只按客观规律裁决、不替你拍板。多轮交锋、有理有据、拒绝和稀泥与谄媚。

## 何时用

- 「辩一下 / 审查一下 / 这个目标现实吗 / 我能不能做到 X」
- 人生 / 策略 / 赚钱 / 投资 / 事业 / 关系 / 目标可行性类决策
- ❌ 技术方案、代码、工程可行性审查——知识源不同，别用本 skill

## 结构（Karpathy LLM Wiki 三层）

```
adversarial-debate/
├── SKILL.md          # 薄入口：触发边界 + 五步辩论流程
├── SCHEMA.md         # 行为契约：raw / wiki / schema 三层、Ingest-Query-Lint、铁律
├── scripts/
│   ├── fetch_kb.py   # 拉取知识源 → 无损瘦身 → 按字节切块 → 自检报告
│   └── wiki_fts.py   # BM25 检索（SQLite FTS5 trigram，中文可用）
└── wiki/             # 派生知识层（LLM 拥有，跨会话复利）
    ├── index.md      # 目录：主题锚点
    ├── log.md        # append-only 操作日志
    ├── overview.md   # 认知宪法总纲：笔记权重 / 编号体系 / 已知缺陷
    ├── synthesis/    # 反方弹药库、时效冲突
    └── concepts/ entities/ comparisons/ queries/
```

## 使用

把本目录放进 `~/.claude/skills/`，然后对 Claude 说「辩一下：……」。

知识源是一份你自己维护的飞书文档（你的认知宪法），通过环境变量指定：

```bash
export ADVERSARIAL_KB_URL="https://your.feishu.cn/wiki/xxxx"
```

每次调用都会**逐字通读全文**再开辩（Ingest），辩论后把增量结论沉淀进 `wiki/`（Lint）。

## 关键约束

- 知识源文档**只读**，且不留本地副本（临时块读完即清，BM25 索引同样只落 temp）
- 所有论据必须标注文档内出处 `【编号】标题`，文档没覆盖的角度明确标注「文档未覆盖」
- 裁判只交付判断（能 / 不能 / 有条件能 + 置信度 + 关键变量），**不替用户做决定**

## LICENSE

MIT
