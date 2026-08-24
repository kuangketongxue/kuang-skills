# 微信公众号草稿 API 参考

## 1. 获取 Access Token

```
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET
```

返回：
```json
{"access_token":"ACCESS_TOKEN","expires_in":7200}
```

- `expires_in` 为 7200 秒，有效期内重复获取会导致旧 token 失效

## 2. 上传永久素材（封面图必须用此接口）

```
POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=ACCESS_TOKEN&type=image
Content-Type: multipart/form-data
```

表单字段：`media` (二进制文件)

返回：
```json
{"media_id":"PERMANENT_MEDIA_ID","url":"http://mmbiz.qpic.cn/..."}
```

**关键：draft/add 的 thumb_media_id 必须使用此接口返回的永久 media_id。**

## 3. 上传临时素材（正文内图片）

```
POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=ACCESS_TOKEN
Content-Type: multipart/form-data
```

表单字段：`media` (二进制文件)

返回：
```json
{"url":"http://mmbiz.qpic.cn/..."}
```

此 URL 可直接用于文章正文中的 `<img src="...">`。

## 4. 创建草稿

```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN
Content-Type: application/json
```

请求体：
```json
{
  "articles": [
    {
      "title": "文章标题",
      "author": "作者名",
      "digest": "文章摘要（可选）",
      "content": "<p>正文 HTML</p>",
      "content_source_url": "原文链接（可选）",
      "thumb_media_id": "PERMANENT_MEDIA_ID",
      "need_open_comment": 1,
      "only_fans_can_comment": 0,
      "show_cover_pic": 1
    }
  ]
}
```

返回：
```json
{"media_id":"DRAFT_MEDIA_ID","item":[]}
```

## 5. 标准文章模板结构

脚本会自动应用以下模板：

```
文:@作者名
[正文内容]
[总结图（可选）]
[固定结尾文案]
```

## 6. Markdown 转 HTML 规则

- `# 标题` → `<h1>`（一级标题）
- `## 标题` → `<h2>`（二级标题）
- `### 标题` → `<h3>`（三级标题）
- `- 列表项` → `<li>`
- `**重点内容**` → `<strong><span style="color: #576b95;">重点内容</span></strong>`（蓝色粗体）
- `[链接:url]` → `<a href="url" style="text-decoration: underline;">url</a>`（带下划线链接）
- 普通段落 → `<p>段落内容</p>`
- 代码块 → `<pre><code>...</code></pre>`

## 7. 支持的 HTML 标签

微信编辑器支持的 HTML 子集有限：

- 段落：`p`
- 标题：`h1`, `h2`, `h3`
- 粗体：`strong`, `b`
- 斜体：`em`
- 列表：`ul`, `ol`, `li`
- 图片：`img`（src 必须是微信素材库 URL）
- 链接：`a`（href 会被过滤或替换）
- 分隔线：`hr`
- 换行：`br`

**不支持的标签：** `div`, `span`, `table`, `style`, `script`, `iframe` 等。内联样式（`style` 属性）也会被过滤。

## 8. 图片规格要求

- 封面图：建议 900 x 500 像素，大小不超过 2MB
- 正文图片：宽度不超过 1080px，大小不超过 2MB
- 格式：支持 jpg、png、gif

## 9. 权限限制

- 订阅号（未认证）：通常无法使用 draft/add 接口（返回权限错误）
- 订阅号（已认证）、服务号：可以使用 draft/add
- 若返回 48001，表示当前账号无此接口权限

## 10. 错误码速查

| 错误码 | 说明 |
|--------|------|
| 40001 | access_token 过期或无效 |
| 40002 | grant_type 错误 |
| 40003 | 非法的 openid |
| 40007 | media_id 不合法（通常是因为用了临时素材） |
| 40008 | 消息类型错误 |
| 40164 | IP 不在白名单 |
| 45009 | 接口调用超过频率限制 |
| 48001 | 接口未授权（账号类型不支持） |
| 50002 | 用户受限 |
| 45106 | 接口已废弃（如 material/add_news） |
