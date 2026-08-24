---
name: feishu-note-appender
description: 将阅读笔记追加到飞书 Wiki 末尾。用户发来笔记内容，确认后格式化并追加到指定的飞书读书笔记合集文档，同时同步本地副本。
---

# 飞书笔记追加 Skill

把阅读笔记追加到飞书读书笔记合集末尾的工具。不负责内容创作，只负责格式化+写入。

## 工作流

```
用户发笔记 → 确认内容 → 格式化 → 追加到飞书 Wiki → 同步本地
```

## 使用前提

1. 已安装并配置 `lark-cli`（`lark-cli docs +fetch --help` 确认可用）
2. 飞书 Wiki 的 URL 或 token 已知（通过 `--wiki-url` 传入）
3. 本地笔记文件路径已知（通过 `--local-path` 传入）

## 快速使用

### 方式一：手动（标准流程）

用户发来笔记 → 你确认内容 → 执行：

```bash
python scripts/append.py \
  --title "笔记标题" \
  --content "正文内容" \
  --date "2026.07.28" \
  --wiki-url "https://my.feishu.cn/wiki/YOUR_WIKI_TOKEN" \
  --local-path "/path/to/local/notes.md"
```

### 方式二：由 Agent 自动组装

用户发来笔记 → Agent 按标准格式组装 → 用户确认 → 执行追加。

标准格式：
```
## 【YYYY.MM.DD】标题

正文内容
```

## 脚本参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` | 是 | 笔记标题 |
| `--content` | 是 | 正文内容（支持 Markdown） |
| `--date` | 否 | 日期，默认当天（如 `2026.07.28`） |
| `--wiki-url` | 是 | 飞书 Wiki URL 或 token |
| `--local-path` | 否 | 本地同步路径，不传则不同步 |
| `--format-only` | 否 | 仅输出格式化结果，不写入（用于预览确认） |

## 安全

- 每次写入前必须经用户确认
- 不修改已有内容，只在末尾追加
- 本地同步自动创建备份 `.bak` 文件