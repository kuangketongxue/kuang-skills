# crazy-wechat-auto

<p align="center">
  <a href="https://github.com/kuangketongxue/crazy-wechat-auto/releases"><img src="https://img.shields.io/github/v/release/kuangketongxue/crazy-wechat-auto?label=release&color=blue" alt="release"></a>
  <a href="https://github.com/kuangketongxue/crazy-wechat-auto/stargazers"><img src="https://img.shields.io/github/stars/kuangketongxue/crazy-wechat-auto?style=flat&logo=github&color=yellow" alt="stars"></a>
  <a href="https://github.com/kuangketongxue/crazy-wechat-auto/forks"><img src="https://img.shields.io/github/forks/kuangketongxue/crazy-wechat-auto?style=flat&logo=github" alt="forks"></a>
  <a href="https://github.com/kuangketongxue/crazy-wechat-auto/issues"><img src="https://img.shields.io/github/issues/kuangketongxue/crazy-wechat-auto?style=flat&logo=github" alt="issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
</p>

<p align="center"><em>WeChat Official Account automation</em></p>


All-in-one tool for searching, writing, and auto-publishing WeChat Official Account articles to your drafts.

## Features

- Search WeChat Official Account articles
- Write in-depth articles in Liu Run's style
- Auto-publish to WeChat Official Account drafts via API
- Auto-apply fixed template: author byline, summary image placeholder, fixed ending copy

## Quick Start

```bash
# Search articles
node scripts/search_wechat.js "keyword" -n 10

# Publish article to drafts
python scripts/wechat_publish.py \
  --title "Article Title" \
  --content-file path/to/article.md \
  --cover path/to/cover.jpg \
  --author "Kuanglee"
```

## Configuration

Copy `.env.example` to `.env` and fill in your Official Account credentials:

```bash
cp .env.example .env
```

```env
WECHAT_MP_APP_ID=your_app_id
WECHAT_MP_APP_SECRET=your_app_secret
```

## Notes

- Add your environment's outbound IP to the Official Account IP whitelist
- Cover image recommended: 900x500px, under 2MB
- WeChat editor filters some HTML styles; manually adjust title colors and fonts after publishing

## License

MIT
