# crazy-wechat-auto

WeChat公式アカウントの記事検索、作成、草稿箱への自動公開を一体化したツール。

## 機能

- WeChat公式アカウントの記事検索
- 劉潤スタイルの深掘り記事作成
- APIを介してWeChat公式アカウントの草稿箱に自動公開
- 固定テンプレートの自動適用：著者署名、要約画像プレースホルダー、固定エンドコピー

## クイックスタート

```bash
# 記事検索
node scripts/search_wechat.js "キーワード" -n 10

# 草稿箱に公開
python scripts/wechat_publish.py \
  --title "記事タイトル" \
  --content-file path/to/article.md \
  --cover path/to/cover.jpg \
  --author "狂客同学"
```

## 設定

`.env.example` を `.env` にコピーし、公式アカウントの認証情報を入力：

```bash
cp .env.example .env
```

```env
WECHAT_MP_APP_ID=あなたのAppID
WECHAT_MP_APP_SECRET=あなたのAppSecret
```

## 注意事項

- 公式アカウントのバックエンドで実行環境のIPをホワイトリストに追加
- カバー画像：900x500px、2MB以下推奨
- WeChatエディターは一部HTMLスタイルをフィルタリングします。公開後にタイトルの色とフォントを手動で調整してください

## ライセンス

MIT
