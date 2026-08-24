# 洁癖 — Knowledge Base Neat-Freak

<p align="center">
  <a href="https://github.com/kuangketongxue/neat-freak/releases"><img src="https://img.shields.io/github/v/release/kuangketongxue/neat-freak?label=release&color=blue" alt="release"></a>
  <a href="https://github.com/kuangketongxue/neat-freak/stargazers"><img src="https://img.shields.io/github/stars/kuangketongxue/neat-freak?style=flat&logo=github&color=yellow" alt="stars"></a>
  <a href="https://github.com/kuangketongxue/neat-freak/forks"><img src="https://img.shields.io/github/forks/kuangketongxue/neat-freak?style=flat&logo=github" alt="forks"></a>
  <a href="https://github.com/kuangketongxue/neat-freak/issues"><img src="https://img.shields.io/github/issues/kuangketongxue/neat-freak?style=flat&logo=github" alt="issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
</p>

<p align="center"><em>AI knowledge base cleanup skill · Claude Code / Codex / OpenCode</em></p>


> **Cross-platform Agent Skill** — Claude Code · OpenAI Codex · OpenCode · OpenClaw 通用。
> 你的 AI 协作不该只有代码能力，还应该有**记忆能力**。

## 为什么需要这个 Skill

AI 协作开发最大的问题不是代码写得不好，而是**上下文断裂**——上次对话做了什么决策、踩了什么坑、用户有什么偏好，下次对话全忘了。

Neat-Freak 解决这个问题：**每次对话结束后，自动审查、同步、清理整个知识体系**，让跨会话协作质量持续累积。

## 它能做什么

| 能力 | 说明 |
|------|------|
| **自动同步文档** | 代码改了 → docs/ 跟着改，不让文档过期 |
| **记忆膨胀治理** | CLAUDE.md 超 300 行自动精简，防止重要规则被淹没 |
| **对话开头检查** | 强制检查是否完整读取了用户特质+知识库+经验，防止 AI 在不完整上下文中工作 |
| **对话结尾打分** | 强制请用户打分（0-100）→ 复盘 → 写入文件，让每次对话都有可追溯的质量反馈 |
| **飞书云端备份** | 本地关键文件修改后自动备份到飞书多维表格，防止本地文件丢失导致数据消失 |
| **自我介绍加载** | 对话开始时自动读取用户个人档案（特质、经验、知识库），让 AI 每次都知道在和谁打交道 |
| **用户特质追踪** | 跨会话自动识别并记录用户的决策偏好、工作习惯、沟通风格 |
| **可复用经验提取** | 每次对话的避坑指南、方法论自动沉淀，不让经验随对话消失 |
| **全平台内容关联** | 扫描 GitHub、小红书收藏、B站收藏、YouTube收藏、Twitter收藏、浏览器书签、飞书内容，与当前对话交叉比对 |
| **变更影响矩阵** | 一张表告诉你"改了 X → 哪些文档也要改"，防漏改 |
| **多平台兼容** | 同一套 Skill 在 Claude Code、Codex、OpenCode、OpenClaw 都能用 |

## 安装

**把下面这段话复制发给你的 AI Agent：**

> 请帮我安装 Neat-Freak 这个 Agent Skill。步骤如下：
> 1. 创建目录 `~/.claude/skills/neat-freak/`（Claude Code）或 `~/.codex/skills/neat-freak/`（OpenAI Codex）
> 2. 从 https://github.com/kuangketongxue/neat-freak 下载 SKILL.md 和 references/ 目录下的所有文件，放入刚创建的目录
> 3. 安装完成后告诉我"已安装"

**如果你之前装过 khazix-skills-main 版本的 neat-freak：**

> 我之前装过 khazix-skills-main 版本的 neat-freak，现在要升级到最新版。找到旧目录（`~/.claude/skills/` 或 Codex skills 目录下的 neat-freak 文件夹），直接删掉，再按全新安装走一遍。

## 快速开始

在对话中说：
- `/neat-freak` — 触发完整同步流程
- "同步一下" / "整理文档" / "收尾" — 自然语言触发

## 全平台数据源

Neat-Freak 会扫描你**所有平台的内容沉淀**，不只是 GitHub。在 EXTEND.md 中配置你的数据源路径：

```markdown
# 我的个性化配置

## 数据源（Neat-Freak 会扫描这些，与当前对话交叉比对）

### 代码
- GitHub 用户名：your-username

### 内容收藏
- 小红书收藏导出文件：`data/xiaohongshu-favorites.json`
- B站收藏导出文件：`data/bilibili-favorites.json`
- YouTube收藏导出文件：`data/youtube-favorites.json`
- Twitter/X收藏导出文件：`data/twitter-favorites.json`
- 浏览器书签导出文件：`data/bookmarks.html`

### 文档
- 飞书内容导出目录：`data/feishu/`
- Notion 导出目录：`data/notion/`
- 语雀导出目录：`data/yuque/`

### 本地文件
- 下载文件夹：`~/Downloads/`
- 桌面：`~/Desktop/`
```

### 各平台导出方式

| 平台 | 导出方式 |
|------|---------|
| **小红书** | 小红书网页版 → 收藏 → 全选 → 导出 JSON（或用 web-access skill 抓取） |
| **B站** | B站网页版 → 收藏夹 → 导出（或用 opencli / web-access 抓取） |
| **YouTube** | Google Takeout → YouTube → 订阅和收藏 → JSON |
| **Twitter/X** | X 设置 → 下载数据存档 → JSON |
| **浏览器书签** | Chrome：`书签管理器 → 导出书签 → HTML` |
| **飞书** | 飞书云文档 → 批量导出 → Markdown/JSON |

### 扫描逻辑

每次同步时，Neat-Freak 会：

1. **读取**所有配置的数据源文件
2. **提取关键词**：标题、标签、描述、正文前200字
3. **与当前对话主题交叉比对**：语义相似度 > 阈值则命中
4. **输出关联结果**：列出相关收藏/内容，说明为什么跟当前对话有关

**示例输出：**

```
## 全平台内容关联

当前对话主题：AI Agent 记忆管理

命中：
├─ GitHub: neat-freak (自己的仓库，⭐0) — 直接相关
├─ B站收藏: "Claude Code 记忆系统详解" — 讲 Agent 记忆架构
├─ 小红书收藏: "AI工具链2026推荐" — 提到记忆管理工具
├─ YouTube: "Building a Second Brain with AI" — 知识管理方法论
└─ 浏览器书签: "Memex: 个人知识库工具" — 类似产品定位

未命中：
└─ Twitter收藏、飞书文档（与当前主题无关）
```

## 核心设计

### 三类知识，三种受众

| 位置 | 受众 | 职责 |
|------|------|------|
| Agent 记忆系统 | AI 自己（跨会话） | 个人偏好、非显而易见的项目事实 |
| 项目 CLAUDE.md / AGENTS.md | 当前项目的 AI | 项目约定、红线、路由清单 |
| 项目 docs/ + README | 其他人 | 接入指南、架构、运维手册 |

### CLAUDE.md 是规则手册，不是变更日志

判断一条信息该不该进 CLAUDE.md，问一句：**下次 AI 写代码时如果没看到这条，会不会犯错？**

- ✅ "Prisma 查询只写在 `modules/**/data/`" → 会犯错，必须进
- ❌ "2026-05-08 X 功能上线，详见 docs/Y.md" → 不会犯错，删

### 反膨胀优先

| 文件 | 软限制 | 超了怎么办 |
|------|--------|-----------|
| CLAUDE.md | ~300 行 | 删历史叙事，迁 docs |
| 记忆索引 | ~150 行 | 合并重复，删过期 |
| 单条记忆 | ~100 行 | 拆分或删 |

## 文件结构

```
neat-freak/
├── SKILL.md              # 核心 Skill（6 步执行流程）
├── EXTEND.md             # 你的个性化配置（数据源路径等）
├── references/
│   ├── agent-paths.md    # 多平台 Agent 路径速查
│   ├── sync-matrix.md    # 变更影响矩阵
│   └── github-scan.md    # GitHub 扫描参考
├── README.md             # 本文件
└── LICENSE               # MIT
```

## 特色功能详解

### 用户特质追踪

Neat-Freak 会在每次对话后自动识别用户的：
- **决策偏好**（"用户总是选择最简方案"）
- **工作习惯**（"用户深夜效率最高"）
- **沟通风格**（"用户喜欢直接给结论不要过程"）
- **技术偏好**（"用户只用 TypeScript 不碰 Python"）

这些特质会编号沉淀（T1, T2, T3...），下次对话自动加载，让 AI 越来越懂你。

### 可复用经验提取

不只是记录"做了什么"，而是提炼"下次遇到类似情况怎么办"：
- 避坑指南（"Windows PowerShell 下 npx 要用 cmd /c 绕过"）
- 方法论（"搜索必须并行调多个引擎防遗漏"）
- 决策框架（"做不做一件事：先看自己有没有能力，再看能不能赚钱"）

### 全平台内容关联

每次同步自动扫描：
1. GitHub 仓库和 star
2. 小红书 / B站 / YouTube / Twitter 收藏
3. 浏览器书签
4. 飞书 / Notion / 语雀文档
5. 与当前对话主题交叉比对，输出关联结果

**价值**：你收藏过的内容、写过的东西，不会再"躺在收藏夹里吃灰"——下次对话时，AI 会自动帮你关联起来。

## 贡献

欢迎提交 Issue 和 PR。

## License

MIT