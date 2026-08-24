# GitHub Auto Release v2

<div align="center">
  <p><strong>一条命令：本地项目 → 全副武装的公开 GitHub 仓库。</strong></p>
  <p><em>隐私扫描 · About 与 topics · 双语徽章墙 README · CHANGELOG · package.json · LICENSE · Release —— 一次跑完。</em></p>
</div>

<p align="center">
  <a href="https://github.com/kuangketongxue/github-auto-release/releases"><img src="https://img.shields.io/github/v/release/kuangketongxue/github-auto-release?label=release&color=blue" alt="release"></a>
  <a href="https://github.com/kuangketongxue/github-auto-release/stargazers"><img src="https://img.shields.io/github/stars/kuangketongxue/github-auto-release?style=flat&logo=github&color=yellow" alt="stars"></a>
  <a href="https://github.com/kuangketongxue/github-auto-release/forks"><img src="https://img.shields.io/github/forks/kuangketongxue/github-auto-release?style=flat&logo=github" alt="forks"></a>
  <a href="https://github.com/kuangketongxue/github-auto-release/issues"><img src="https://img.shields.io/github/issues/kuangketongxue/github-auto-release?style=flat&logo=github" alt="issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/changelog-Keep%20a%20Changelog-orange" alt="changelog"></a>
</p>

<br/>

<p align="center">
  🌐 <a href="README.md">English</a> · <a href="README_ja.md">日本語</a> ·
  <a href="#contributing">参与贡献</a>
</p>

<br/>

<a id="about"></a>

## 关于

大多数仓库推上去都是「半裸」的：代码传了、没描述、README 一行、没有 release。**GitHub Auto Release** 反过来——一条命令把本地项目**全副武装**地发布：

```
本地项目
  → 隐私扫描（token / 密钥 / 密码，上传前就拦下）
  → 通过 GitHub API 创建仓库
  → 设置 About 描述 + 主页 + topics
  → 推送代码（git；git 被墙时走 Contents API 逐文件上传）
  → 生成 README.md（英文）+ README_zh.md（中文），带完整徽章墙
  → 自动生成 CHANGELOG.md + package.json + LICENSE
  → 发布 Release v1.0.0（含 release notes）
  → （可选）生成小红书宣发草稿
```

既是 **Claude Code skill**（含 `SKILL.md`），也是独立 CLI 工具。

<p align="right">(<a href="#about">回到顶部</a>)</p>

### 核心特性

- **隐私优先扫描器**——拦截 GitHub token、`sk-` API key、密码、私钥、微信凭证，发现可疑先问再传
- **仓库门面**——About 描述、主页、最多 20 个 topics 一并设好
- **双语徽章墙 README**——中英模板：release / stars / forks / issues / license / changelog / website 徽章、语言切换链接、贡献者图表、Star History
- **脚手架文件**——Keep-a-Changelog 格式 CHANGELOG、package.json（repository/bugs/keywords）、MIT LICENSE
- **Release 自动化**——首发自动打 tag + 写 release notes
- **中国网络友好**——`--api-push` 在 `github.com:443` 连不上时改走 Contents API 逐文件上传
- **小红书宣发**——opencli 长文草稿（可选）

<p align="right">(<a href="#about">回到顶部</a>)</p>

### 技术栈

<p align="left">
  <img src="https://skillicons.dev/icons?i=python,git,githubactions" />
</p>

Python 3.9+，纯标准库——零 pip 依赖。

<p align="right">(<a href="#about">回到顶部</a>)</p>

<a id="getting-started"></a>

## 快速开始

### 前置要求

- Python 3.9+
- GitHub PAT（`--token`、`GITHUB_TOKEN` 环境变量、或 `gh auth login`）
- Git（默认推送路径需要）
- 小红书宣发需另装 [opencli](https://github.com/jackwener/opencli)

### 安装

```bash
git clone https://github.com/kuangketongxue/github-auto-release.git
cd github-auto-release
python scripts/github_release.py --help
```

<p align="right">(<a href="#getting-started">回到顶部</a>)</p>

<a id="usage"></a>

## 使用

### 完整首发（推荐）

```bash
python scripts/github_release.py \
  --repo "yourname/your-project" \
  --path ./your-project \
  --title "项目标题" \
  --desc "一句话描述（中英都放效果最好）" \
  --homepage "https://your-site.example.dev" \
  --topics "python,cli,automation"
```

这一条命令产出：仓库 + About + topics + 代码 + README.md/README_zh.md（徽章墙）+ CHANGELOG + package.json + LICENSE + Release v1.0.0。

### 常用变体

```bash
# git push 被墙（如中国网络）？改走 Contents API：
... --api-push

# 不发初始 Release / 不要脚手架：
... --no-release
... --no-facade-files

# 还要日文 README：
... --readme-langs en,zh,ja

# 宣发到小红书草稿箱：
... --publish-xhs --xhs-cover ./cover.jpg
```

### 全部参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--repo` | 是 | — | 目标仓库（`owner/repo-name`） |
| `--path` | 否 | `.` | 本地项目路径 |
| `--token` | 是* | 自动 | GitHub PAT（或 `GITHUB_TOKEN`、`gh auth token`） |
| `--title` | 是 | — | 仓库标题 / README 大标题 |
| `--desc` | 否 | `""` | 描述 → About + READMEs |
| `--private` | 否 | `false` | 创建私有仓库 |
| `--homepage` | 否 | `""` | 网站 URL → About 字段 + website 徽章 |
| `--topics` | 否 | `""` | 逗号分隔 topics（小写，最多 20 个） |
| `--version` | 否 | `1.0.0` | 初始 Release 版本号 |
| `--author` | 否 | 仓库主人 | LICENSE/package.json 的作者名 |
| `--readme-langs` | 否 | `en,zh` | README 语言 |
| `--skip-privacy-check` | 否 | `false` | 跳过隐私扫描（不推荐） |
| `--no-release` | 否 | `false` | 不创建 Release |
| `--no-facade-files` | 否 | `false` | 不生成 CHANGELOG/package.json/LICENSE |
| `--api-push` | 否 | `false` | 用 Contents API 替代 git 推送 |
| `--publish-xhs` | 否 | `false` | 宣发草稿到小红书 |
| `--xhs-cover` | 否 | 自动查找 | 封面图路径 |

<p align="right">(<a href="#usage">回到顶部</a>)</p>

### 隐私扫描

任何内容上传之前：

| 类型 | 检测模式 | 示例 |
|------|---------|---------|
| GitHub Token | `ghp_`、`gho_`、`github_pat_` | `ghp_xxxx…` |
| OpenAI/Anthropic Key | `sk-…` | `sk-proj-…` |
| API Key | `api_key: "…"` | 16 位以上取值 |
| 密码 / Secret | `password=`、`secret=` | — |
| 私钥文件 | `.pem`、`.key`、`.p12`、`.id_rsa` | — |
| 微信凭证 | `wx…`、`app_secret` | — |

`.git/`、`node_modules/`、构建目录自动跳过。发现问题会列出来，必须手动确认才继续。

### 当 Claude Code skill 用

把这个目录拷进 `.claude/skills/github-auto-release/`。之后只要对 agent 说「开源这个项目到 GitHub」，它会读 `SKILL.md` 并替你驱动脚本。

<p align="right">(<a href="#usage">回到顶部</a>)</p>

<a id="roadmap"></a>

## 路线图

- [ ] Social preview 图上传（等 GitHub API 支持）
- [ ] Trendshift 徽章拿到 ID 后自动追加
- [ ] `--update` 模式：对已有仓库重跑门面步骤而不动代码

已发布内容见 [CHANGELOG.md](CHANGELOG.md)。

<p align="right">(<a href="#roadmap">回到顶部</a>)</p>

<a id="contributing"></a>

## 参与贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动
4. 推送分支
5. 发起 Pull Request

### 贡献者

<a href="https://github.com/kuangketongxue/github-auto-release/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=kuangketongxue/github-auto-release" alt="contributors" />
</a>

<p align="right">(<a href="#contributing">回到顶部</a>)</p>

<a id="license"></a>

## 开源协议

基于 **MIT License** 发行，详见 [`LICENSE`](LICENSE)。

<p align="right">(<a href="#license">回到顶部</a>)</p>

<div align="center">
  <b>如果它帮你省下一个下午的配置时间，欢迎点个 ⭐。</b>
</div>
