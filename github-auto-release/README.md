# GitHub Auto Release v2

<div align="center">
  <p><strong>One command: local project → fully dressed public GitHub repository.</strong></p>
  <p><em>Privacy scan · About & topics · bilingual badge-wall README · CHANGELOG · package.json · LICENSE · Release — all in a single run.</em></p>
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
  🌐 <a href="README_zh.md">中文</a> · <a href="README_ja.md">日本語</a> ·
  <a href="#contributing">Contributing</a>
</p>

<br/>

<a id="about"></a>

## About

Most repos get pushed half-naked: code up, no description, one line of README, no release. **GitHub Auto Release** is the opposite workflow — it publishes a local project *fully dressed* in one command:

```
local project
  → privacy scan (tokens / keys / passwords blocked before anything leaves your machine)
  → repo created via GitHub API
  → About description + homepage + topics set
  → code pushed (git, or Contents API fallback when git push is blocked)
  → README.md (EN) + README_zh.md (中文) generated with full badge wall
  → CHANGELOG.md + package.json + LICENSE scaffolded
  → Release v1.0.0 published with notes
  → (optional) Xiaohongshu promotional draft
```

Works as a **Claude Code skill** (`SKILL.md` included) or a standalone CLI.

<p align="right">(<a href="#about">back to top</a>)</p>

### Highlights

- **Privacy-first scanner** — blocks GitHub tokens, `sk-` API keys, passwords, private keys, WeChat credentials; asks before uploading
- **Repo facade** — About description, homepage, and up to 20 topics set via API
- **Bilingual badge-wall READMEs** — EN + 中文 from templates: release / stars / forks / issues / license / changelog / website badges, language switch links, contributors chart, Star History
- **Scaffolds** — Keep-a-Changelog CHANGELOG, package.json (repository/bugs/keywords), MIT LICENSE
- **Release automation** — tag + release notes on first publish
- **CN-network friendly** — `--api-push` uploads file-by-file via the Contents API when `github.com:443` is unreachable
- **Xiaohongshu promotion** — long-form draft via opencli (optional)

<p align="right">(<a href="#about">back to top</a>)</p>

### Built With

<p align="left">
  <img src="https://skillicons.dev/icons?i=python,git,githubactions" />
</p>

Python 3.9+, stdlib only — no pip dependencies.

<p align="right">(<a href="#about">back to top</a>)</p>

<a id="getting-started"></a>

## Getting Started

### Prerequisites

- Python 3.9+
- A GitHub PAT (`--token`, `GITHUB_TOKEN` env, or `gh auth login`)
- Git (for the default push path)
- [opencli](https://github.com/jackwener/opencli) only if using Xiaohongshu promotion

### Installation

```bash
git clone https://github.com/kuangketongxue/github-auto-release.git
cd github-auto-release
python scripts/github_release.py --help
```

<p align="right">(<a href="#getting-started">back to top</a>)</p>

<a id="usage"></a>

## Usage

### Full launch (recommended)

```bash
python scripts/github_release.py \
  --repo "yourname/your-project" \
  --path ./your-project \
  --title "Your Project" \
  --desc "One-line description in both languages works best" \
  --homepage "https://your-site.example.dev" \
  --topics "python,cli,automation"
```

That single command produces: repo + About + topics + code + README.md/README_zh.md (badge wall) + CHANGELOG + package.json + LICENSE + Release v1.0.0.

### Common variations

```bash
# git push blocked (e.g. CN network)? upload via Contents API instead:
... --api-push

# skip the initial release or scaffolds:
... --no-release
... --no-facade-files

# Japanese README too:
... --readme-langs en,zh,ja

# promote on Xiaohongshu as a draft:
... --publish-xhs --xhs-cover ./cover.jpg
```

### All parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--repo` | Yes | — | Target repository (`owner/repo-name`) |
| `--path` | No | `.` | Local project path |
| `--token` | Yes* | auto | GitHub PAT (or `GITHUB_TOKEN`, or `gh auth token`) |
| `--title` | Yes | — | Repository title / README heading |
| `--desc` | No | `""` | Description → About + READMEs |
| `--private` | No | `false` | Create private repository |
| `--homepage` | No | `""` | Website URL → About field + website badge |
| `--topics` | No | `""` | Comma-separated topics (lowercase, max 20) |
| `--version` | No | `1.0.0` | Initial release version |
| `--author` | No | owner | Author name for LICENSE/package.json |
| `--readme-langs` | No | `en,zh` | README languages |
| `--skip-privacy-check` | No | `false` | Skip privacy scan (not recommended) |
| `--no-release` | No | `false` | Skip creating the Release |
| `--no-facade-files` | No | `false` | Skip CHANGELOG/package.json/LICENSE |
| `--api-push` | No | `false` | Push via Contents API instead of git |
| `--publish-xhs` | No | `false` | Publish promo draft to Xiaohongshu |
| `--xhs-cover` | No | auto | Cover image path |

<p align="right">(<a href="#usage">back to top</a>)</p>

### Privacy Scan

Before anything is uploaded:

| Type | Detection Pattern | Example |
|------|---------|---------|
| GitHub Token | `ghp_`, `gho_`, `github_pat_` | `ghp_xxxx…` |
| OpenAI/Anthropic Key | `sk-…` | `sk-proj-…` |
| API Key | `api_key: "…"` | any 16+ char value |
| Password / Secret | `password=`, `secret=` | — |
| Private Key File | `.pem`, `.key`, `.p12`, `.id_rsa` | — |
| WeChat Credential | `wx…`, `app_secret` | — |

`.git/`, `node_modules/`, build dirs are skipped automatically. Findings are listed and require explicit confirmation.

### Use as a Claude Code skill

Copy this folder into `.claude/skills/github-auto-release/`. The agent reads `SKILL.md` and drives the script for you — just say "开源这个项目到 GitHub".

<p align="right">(<a href="#usage">back to top</a>)</p>

<a id="roadmap"></a>

## Roadmap

- [ ] Social preview image upload (when GitHub API supports it)
- [ ] Trendshift badge auto-append once an ID exists
- [ ] `--update` mode: re-run facade steps on an existing repo without touching code

See [CHANGELOG.md](CHANGELOG.md) for shipped changes.

<p align="right">(<a href="#roadmap">back to top</a>)</p>

<a id="contributing"></a>

## Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request

### Contributors

<a href="https://github.com/kuangketongxue/github-auto-release/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=kuangketongxue/github-auto-release" alt="contributors" />
</a>

<p align="right">(<a href="#contributing">back to top</a>)</p>

<a id="license"></a>

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE).

<p align="right">(<a href="#license">back to top</a>)</p>

<div align="center">
  <b>If this saved you a setup afternoon, a ⭐ is appreciated.</b>
</div>
