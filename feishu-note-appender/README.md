# 飞书笔记追加工具

<p align="center">
  <a href="https://github.com/kuangketongxue/feishu-note-appender/releases"><img src="https://img.shields.io/github/v/release/kuangketongxue/feishu-note-appender?label=release&color=blue" alt="release"></a>
  <a href="https://github.com/kuangketongxue/feishu-note-appender/stargazers"><img src="https://img.shields.io/github/stars/kuangketongxue/feishu-note-appender?style=flat&logo=github&color=yellow" alt="stars"></a>
  <a href="https://github.com/kuangketongxue/feishu-note-appender/forks"><img src="https://img.shields.io/github/forks/kuangketongxue/feishu-note-appender?style=flat&logo=github" alt="forks"></a>
  <a href="https://github.com/kuangketongxue/feishu-note-appender/issues"><img src="https://img.shields.io/github/issues/kuangketongxue/feishu-note-appender?style=flat&logo=github" alt="issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
</p>

<p align="center"><em>Feishu/Lark Wiki note appender</em></p>


把阅读笔记格式化后追加到飞书读书笔记合集，同时同步本地副本。

## 用途

你读了一篇笔记/文章，整理后想加入飞书知识库。这个工具帮你：

1. 格式化笔记（日期 + 标题 + 正文）
2. 追加到飞书 Wiki 末尾
3. 同步更新本地文件

## 安装

```bash
# 依赖：lark-cli
# 本 skill 放在 ~/.cc-switch/skills/feishu-note-appender/
```

## 使用

```bash
python scripts/append.py \
  --title "笔记标题" \
  --content "正文内容" \
  --wiki-url "https://my.feishu.cn/wiki/TOKEN"
```

## 参数

| 参数 | 说明 |
|------|------|
| `--title` | 笔记标题 |
| `--content` | 正文 |
| `--date` | 日期（默认今天） |
| `--wiki-url` | 飞书 Wiki URL |
| `--local-path` | 本地同步路径 |
| `--format-only` | 仅预览不写入 |

## 作者

@binlo