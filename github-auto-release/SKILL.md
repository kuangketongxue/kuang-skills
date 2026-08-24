---
name: github-auto-release
description: Open source a local project to GitHub as a fully dressed repo in one command — privacy scan, About/topics, bilingual badge-wall READMEs (EN/中文/JA), CHANGELOG, package.json, LICENSE, Release. Use when the user wants to publish/open-source a skill, project, or tool to GitHub ("开源到GitHub", "发布到GitHub", "open source this").
---

# GitHub Auto Release v2

一条命令把本地项目开源成「全副武装」的 GitHub 仓库。v2 合并了完整的仓库门面流程（2026-08-24，源自 gaokao-learn 实战）。

## 什么时候用

用户想把项目/skill/工具开源到 GitHub，要求包含：中英 README、About、release、package、贡献者等完整门面。

## 核心能力（一条命令全做完）

1. **隐私扫描**：上传前检测 token / API key（含 `sk-`）/ 密码 / 私钥 / 微信凭证；发现可疑先列出来要确认
2. **创建仓库**：GitHub API（已存在则继续更新门面）
3. **门面设置**：About 描述 + homepage + topics（PATCH /repos/{repo} + PUT /topics）
4. **推代码**：git push；**git 被墙时加 `--api-push` 走 Contents API 逐文件上传**
5. **双语徽章墙 README**：README.md（EN）+ README_zh.md（中文），模板在 `references/`——release/stars/forks/issues/license/changelog/website 徽章 + 语言切换链接 + 贡献者图 + Star History
6. **脚手架**：CHANGELOG.md（Keep a Changelog）、package.json、MIT LICENSE（缺哪个补哪个，已有的不覆盖）
7. **Release**：自动打 tag v1.0.0 + release notes（`--no-release` 跳过）
8. **小红书宣发**（可选）：`--publish-xhs` 经 opencli 发长文草稿

## 快速命令

```bash
python scripts/github_release.py \
  --repo "owner/repo-name" \
  --path ./project \
  --title "Project Title" \
  --desc "一句话描述" \
  --homepage "https://site.example.dev" \
  --topics "python,cli,automation"
```

常用变体：`--api-push`（被墙时）、`--readme-langs en,zh,ja`（加日文）、`--no-release`、`--private`。

Token 解析顺序：`--token` > 环境变量 `GITHUB_TOKEN` > `gh auth token`（本机 gh 已登录时无需传 token）。

## Agent 执行要点（踩过的坑）

- **中国网络**：`git push` 走 github.com:443 常连不上；api.github.com 稳定。push 失败报 `Failed to connect` → 重跑加 `--api-push`
- **多文件改动**：对已有仓库批量改文件用 Git Data API 一个 commit（blob→tree→commit→ref 四步），不要逐文件 PUT 触发 N 次 CI
- **Contents API PUT 二次提交必须带最新 sha**：每次 PUT 后 sha 变，重新 GET 取
- **Windows Bash PATH 坑**：命令前 `export PATH="$PATH:/c/Program Files/Git/usr/bin"`；python 用 `PYTHONIOENCODING=utf-8` 防 GBK 崩
- **README 语言切换链接命名**：用下划线 `README_zh.md`（不是 `README.zh.md`），与 GitHub 社区惯例一致
- **Trendshift 徽章**：不能凭空生成，需 trendshift.io 提交仓库 → 上 trending 拿数字 ID 后才能加
- **Social preview 图**：GitHub 无 API，提醒用户去 Settings → General → Social preview 手动传

## 发布后检查清单（agent 应逐项验证）

- [ ] About 描述 + website 链接显示
- [ ] topics 显示在 About 下方
- [ ] README.md 与 README_zh.md 互相链接、徽章墙渲染
- [ ] CHANGELOG.md / package.json / LICENSE 存在
- [ ] Release 页有 tag + notes
- [ ] 贡献者图表加载（contrib.rocks）

## 参数速查

见 `README.md` 全参数表；脚本自带 `--help`。

## 资源引用

- 三语 README 模板：`references/readme_template.{en,zh,ja}.md`（变量 `{{repo}} {{title}} {{description}} {{version}} {{homepage}} {{topics_line}} {{website_badge}} {{lang_switch}} {{author}} {{year}} {{repo_name}}`）
