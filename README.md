<div align="center">

**中文** · [English](./README.en.md)

# 🧰 Kuang Skills

#### 狂客同学每天在用的 Claude Code Skills，全部开源在这里

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-7-10B981?style=for-the-badge)](#-skills-%E7%9B%AE%E5%BD%95)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)

</div>

都是在自己日常项目里跑通了一段时间，确实省事，才搬出来开源的。没什么花活，就是几个挺实用的东西。

这里的每个 Skill 都是 Agent 能直接加载的结构化指令集。Claude Code、Codex 等 Agent 都能装。

---

## 📋 Skills 目录

| 名字 | 一句话 |
|---|---|
| 🚀 [**github-auto-release（开源发布）**](#-github-auto-release开源发布) | 一条命令把本地项目开源成「全副武装」的 GitHub 仓库：隐私扫描 + About/topics + 双语徽章墙 README + CHANGELOG + LICENSE + Release |
| ⚔️ [**adversarial-debate（对抗性辩论）**](#️-adversarial-debate对抗性辩论) | 正方最强立论 × 反方专职攻击 × 裁判只按客观规律裁决——回答「你的目标到底能不能达成」 |
| 🧹 [**neat-freak（洁癖）**](#-neat-freak洁癖) | 干完活跑一下 `/neat`，自动对齐项目文档、CLAUDE.md、Agent 记忆，并审计规则有没有被执行 |
| 💬 [**crazy-wechat-auto（公众号自动化）**](#-crazy-wechat-auto公众号自动化) | 微信公众号文章搜索、撰写与草稿箱自动发布一体化 |
| 📚 [**feishu-note-appender（飞书笔记追加）**](#-feishu-note-appender飞书笔记追加) | 把阅读笔记格式化后追加到飞书 Wiki 末尾，同时同步本地副本 |
| 📬 [**agent-mail-readiness（邮件就绪检查）**](#-agent-mail-readiness邮件就绪检查) | Proactive Agent 发主动通知前的邮件通道就绪检查 |
| 🔍 [**web-search（网络搜索）**](#-web-search网络搜索) | 五引擎并行：Tavily/Firecrawl/知乎，中文默认带知乎，API key 本地配置不进仓 |

---

## 📦 安装方式

在 Claude Code 里直接说：

```
帮我安装这个 skill：https://github.com/kuangketongxue/kuang-skills/tree/main/<skill-name>
```

把 `<skill-name>` 换成你想装的那个，比如 `github-auto-release`、`adversarial-debate`、`neat-freak`。

或者手动复制对应目录的 `SKILL.md` 到 `~/.claude/skills/<skill-name>/SKILL.md`。

> 注意：每个子目录就是一个完整的 skill（SKILL.md + scripts/ + references/），单独拷贝任意一个目录都能独立工作。

---

## ✨ Skills

<a id="-skills-%E7%9B%AE%E5%BD%95"></a>

### 🚀 github-auto-release（开源发布）

**问题**：大多数仓库推上去都是「半裸」的——代码传了、没描述、README 一行、没有 release。

**方案**：一条命令全做完：

```
隐私扫描 → API 建仓 → About/topics → 推代码 → 双语徽章墙 README
→ CHANGELOG / package.json / LICENSE → Release v1.0.0 →（可选）小红书宣发
```

```bash
python scripts/github_release.py \
  --repo "you/your-project" --path ./project \
  --title "Title" --desc "描述" \
  --homepage "https://site.dev" --topics "python,cli"
```

特色：中国网络 git push 被墙时 `--api-push` 走 Contents API 逐文件上传；token 自动从 `gh auth` 读取。

详细参数见 [github-auto-release/README.md](./github-auto-release/README.md)。

---

### ⚔️ adversarial-debate（对抗性辩论）

问 AI「我这个计划可行吗」，最常见的两种废答：谄媚式（「好主意！」）和稀泥式（「双方都有道理」）。本 skill 强制 AI 分饰三角：

| 角色 | 职责 | 约束 |
|---|---|---|
| ✅ 正方 | 构建最强支持论证 | 只能从事实底座推导 |
| ❌ 反方 | 专职推翻 | 必须攻击最强版本（steelman） |
| ⚖️ 裁判 | 客观裁决 | 判定三选一 + 置信度 + 关键变量 |

用法：「辩一下：我高三最后一年想从 500 分提到 650，现实吗？」

详见 [adversarial-debate/SKILL.md](./adversarial-debate/SKILL.md)。

---

### 🧹 neat-freak（洁癖）

干完活跑一下 `/neat`：自动对齐项目文档、CLAUDE.md、规则文件与代码实际状态，同步 Agent 记忆，并审计已有规则有没有被执行。支持跨平台（Claude Code / Codex / OpenCode）。

详见 [neat-freak/README.md](./neat-freak/README.md) 与 [EXTEND.md](./neat-freak/EXTEND.md)。

---

### 💬 crazy-wechat-auto（公众号自动化）

微信公众号文章搜索、按刘润风格撰写长文、草稿箱自动发布（API 直传），自动套用固定模板：作者署名、封面占位、固定结尾文案。

```bash
node scripts/search_wechat.js "关键词" -n 10   # 搜索
python scripts/wechat_publish.py --title "..." # 发布到草稿箱
```

详见 [crazy-wechat-auto/SKILL.md](./crazy-wechat-auto/SKILL.md)。

---

### 📚 feishu-note-appender（飞书笔记追加）

读了一篇好文章整理成笔记后，一条命令格式化（日期 + 标题 + 正文）、追加到飞书读书笔记合集的 Wiki 末尾，并同步本地副本。依赖 lark-cli。

详见 [feishu-note-appender/SKILL.md](./feishu-note-appender/SKILL.md)。

---

### 📬 agent-mail-readiness（邮件就绪检查）

Proactive Agent 在发送主动通知前检查邮件通道是否就绪的 skill（WorkBuddy 场景）。

详见 [agent-qq-auto/SKILL.md](./agent-qq-auto/SKILL.md)。

---

### 🔍 web-search（网络搜索）

五个引擎并行：Tavily、Firecrawl（含 Developer Index 开发者索引）、知乎 OpenAPI（站内 + 全网）。中文默认带知乎并行——对中文资源（含 GitHub 仓库、网盘、学习资料）命中率高于纯英文引擎。API key 本地 `~/.claude/.secrets/web-search.env` 自动读取，**本仓不含 key**，重置电脑后需自备。

```bash
python3 scripts/tavily-search.py '{"query":"Claude Code"}'        # 英文/通用深度搜索
python3 scripts/firecrawl-dev.py '{"query":"npm install error"}'  # 开发者索引：issue/PR/官方文档
python3 scripts/zhihu-search.py '{"query":"高三如何提分"}'         # 知乎站内（学习/高考经验）
```

详见 [web-search/SKILL.md](./web-search/SKILL.md)。

---

## License

MIT © 2026 kuangketongxue —— 各 skill 子目录沿用其原有 LICENSE。
