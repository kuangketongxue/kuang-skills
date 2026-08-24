# crazy-wechat-auto

微信公众号文章搜索、撰写与草稿箱自动发布一体化工具。

## 功能

- 搜索微信公众号文章
- 撰写刘润风格深度文章
- 自动发布到微信公众号草稿箱
- 自动应用固定模板：作者署名、总结图占位、固定结尾文案

## 快速开始

```bash
# 搜索文章
node scripts/search_wechat.js "关键词" -n 10

# 发布文章到草稿箱
python scripts/wechat_publish.py \
  --title "文章标题" \
  --content-file path/to/article.md \
  --cover path/to/cover.jpg \
  --author "狂客同学"
```

## 配置

复制 `.env.example` 为 `.env`，并填入你的公众号凭证：

```bash
cp .env.example .env
```

```env
WECHAT_MP_APP_ID=你的AppID
WECHAT_MP_APP_SECRET=你的AppSecret
```

## 注意事项

- 公众号后台需将运行环境 IP 加入白名单
- 封面图建议 900x500，不超过 2MB
- 微信编辑器会过滤部分 HTML 样式，建议发布后手动微调标题颜色和字体

## License

MIT
