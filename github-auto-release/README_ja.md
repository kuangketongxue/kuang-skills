# GitHub Auto Release v2（日本語）

<div align="center">
  <p><strong>ワンコマンドで：ローカルプロジェクト → 完全装備の公開 GitHub リポジトリ。</strong></p>
</div>

<p align="center">
  <a href="https://github.com/kuangketongxue/github-auto-release/releases"><img src="https://img.shields.io/github/v/release/kuangketongxue/github-auto-release?label=release&color=blue" alt="release"></a>
  <a href="https://github.com/kuangketongxue/github-auto-release/stargazers"><img src="https://img.shields.io/github/stars/kuangketongxue/github-auto-release?style=flat&logo=github&color=yellow" alt="stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/changelog-Keep%20a%20Changelog-orange" alt="changelog"></a>
</p>

<p align="center">🌐 <a href="README.md">English</a> · <a href="README_zh.md">中文</a></p>

## 概要

ほとんどのリポジトリは「半裸」で push されます：コードだけ、説明なし、README 一行、リリースなし。**GitHub Auto Release** は逆のワークフローです——ワンコマンドでローカルプロジェクトを**完全装備**で公開します：

```
ローカルプロジェクト
  → プライバシースキャン（トークン / 鍵 / パスワードをアップロード前に遮断）
  → GitHub API でリポジトリ作成
  → About 説明 + ホームページ + topics を設定
  → コード push（git。ブロック時は Contents API で逐次アップロード）
  → README.md（英語）+ README_zh.md（中国語）+ README_ja.md（日本語）、フルバッジウォール付き
  → CHANGELOG.md + package.json + LICENSE 自動生成
  → Release v1.0.0 公開（リリースノート付き）
  → （任意）小红书プロモーション下書き
```

**Claude Code skill**（`SKILL.md` 同梱）としても、スタンドアロン CLI としても使えます。

## 主な機能

- **プライバシー優先スキャナー** — GitHub トークン、`sk-` API キー、パスワード、秘密鍵、WeChat 認証情報を遮断
- **リポジトリ外装** — About・ホームページ・最大 20 の topics
- **多言語バッジウォール README** — release / stars / forks / issues / license / changelog / website バッジ、言語切替リンク、貢献者チャート、Star History
- **スキャフォールド** — Keep a Changelog 形式、package.json、MIT LICENSE
- **リリース自動化** — 初回公開時にタグ + ノート
- **中国ネットワーク対応** — `--api-push` で Contents API 経由のアップロード
- **小红書プロモーション** — opencli 長文ドラフト（任意）

## 使い方

```bash
python scripts/github_release.py \
  --repo "yourname/your-project" \
  --path ./your-project \
  --title "プロジェクト名" \
  --desc "一言説明" \
  --homepage "https://your-site.example.dev" \
  --topics "python,cli,automation"
```

詳細なパラメータは [README.md](README.md) を参照してください。

Python 3.9+、標準ライブラリのみ——pip 依存ゼロ。

## ライセンス

MIT — 詳細は [`LICENSE`](LICENSE)。
