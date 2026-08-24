# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- `--update` mode: re-run facade steps on an existing repo without touching code
- Social preview image upload (when GitHub API supports it)
- Trendshift badge auto-append once an ID exists

## [2.0.0] - 2026-08-24

### Added

- Repo facade automation: About description + homepage + topics via API
- Bilingual badge-wall READMEs: EN (`README.md`) + 中文 (`README_zh.md`) with language switch links, release/stars/forks/issues/license/changelog/website badges, contributors chart, Star History; optional Japanese
- CHANGELOG.md scaffold (Keep a Changelog format)
- package.json scaffold (name/version/description/repository/bugs/keywords)
- MIT LICENSE scaffold
- Initial Release creation with tag + notes
- `--api-push` mode: file-by-file Contents API upload when git push is blocked (CN network)
- `--homepage`, `--topics`, `--version`, `--author`, `--no-release`, `--no-facade-files` parameters
- Token resolution chain: `--token` → `GITHUB_TOKEN` → `gh auth token`
- New sensitive-data patterns: `sk-` keys (OpenAI/Anthropic); `.git/`, `node_modules/`, build dirs skipped in scan

### Changed

- README templates fully rewritten around a complete repo-launch structure (About / Getting Started / Usage / Roadmap / Contributing / License / Acknowledgments / Star History)
- README naming convention: `README_zh.md` (underscore) instead of `README.zh.md`

### Fixed

- Step counter mismatch in v1 output ([2/4] … [5/5])

## [1.0.0] - 2026-08-20

### Added

- Privacy-first scanner (GitHub tokens, API keys, passwords, private keys, WeChat credentials)
- Repo creation via GitHub API, git init + push
- Multi-language README generation from Jinja-style templates (en/zh/ja)
- Xiaohongshu long-form draft promotion via opencli

[Unreleased]: https://github.com/kuangketongxue/github-auto-release/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/kuangketongxue/github-auto-release/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/kuangketongxue/github-auto-release/releases/tag/v1.0.0
