---
name: crazy-wechat-auto
agent_created: true
description: 微信公众号文章搜索、撰写与草稿箱自动发布一体化工具。当用户需要搜索公众号文章、撰写符合固定模板的文章并自动发布到微信公众号草稿箱时使用此技能。内置文章格式规范、搜索、Markdown 转 HTML、封面上传、草稿推送全流程。
---

# crazy-wechat-auto：微信公众号文章搜索 + 草稿箱自动发布

## 核心能力

1. **文章搜索**：通过微信搜索获取文章列表，覆盖科技/AI、社会热点、财经、教育、职场等各类中文资讯
2. **文章撰写**：参考刘润公众号风格，撰写3000-5000字深度文章
3. **草稿自动发布**：通过 `draft/add` API 将文章直接推送到微信公众号草稿箱，无需手动操作后台
4. **标准模板应用**：自动应用用户固定的公众号文章模板，包括作者署名、固定结尾文案等

## 使用前提

1. 公众号已开通开发者模式，且拥有 AppID 和 AppSecret
2. 当前运行环境的外网 IP 已添加到公众号后台的 API IP 白名单
3. 必须提供封面图片（`draft/add` 的 `thumb_media_id` 为实际必填项）
4. 若使用 AI 配图功能，需要用户已登录微信公众号后台（mp.weixin.qq.com）

## 能力 1：搜索微信公众号文章

### 前置依赖

```bash
npm install -g cheerio
```

### 脚本位置

`scripts/search_wechat.js`

### 用法

```bash
# 基本搜索
node scripts/search_wechat.js "关键词"

# 限制返回数量
node scripts/search_wechat.js "关键词" -n 15

# 保存结果到文件
node scripts/search_wechat.js "关键词" -n 20 -o result.json

# 尝试解析真实链接
node scripts/search_wechat.js "关键词" -n 5 -r
```

### 参数说明

- `query`：搜索关键词（必填）
- `-n, --num`：返回数量（默认 10，最大 50）
- `-o, --output`：输出 JSON 文件路径（可选）
- `-r, --resolve-url`：尝试把中间链接解析成微信文章真实链接（会额外请求每条结果）

### 输出字段

文章标题、文章地址、文章概要、发布时间、来源公众号名称

## 能力 2：撰写刘润风格深度文章

### 写作风格参考：刘润公众号

#### 刘润写作特点
1. **开篇切入**：从一个具体的商业案例、故事或现象切入
2. **引入洞察**：引出一个独特的商业观点或洞察
3. **案例论证**：用2-3个真实商业案例来论证观点
4. **数据支撑**：适当引用数据和事实
5. **结论建议**：最后给出明确的结论和行动建议
6. **语言风格**：
   - 语言简洁有力，不啰嗦
   - 逻辑清晰，层层递进
   - 很少使用emoji
   - 段落较短，每段一个观点
   - 善用小标题分隔章节
   - 观点鲜明，敢于下结论

#### 文章结构建议
```
一. 开篇（200-300字）
- 描述一个商业现象/事件
- 引发思考

二. 正文（2500-4000字）
- 3-4个小标题
- 每个小标题下：案例 + 分析 + 结论
- 案例要有细节，数据要准确

三. 总结（200-300字）
- 核心观点一句话概括
- 行动建议
```

#### 禁止事项
- ❌ 文章末尾禁止加任何话题标签（如 #xxx）
- ❌ 禁止使用大量emoji
- ❌ 禁止用"欢迎在评论区分享"这类话结尾

## 能力 3：发布文章到草稿箱

### 调用流程

1. 获取 access_token：`GET https://api.weixin.qq.com/cgi-bin/token`
2. 上传封面图为永久素材：`POST https://api.weixin.qq.com/cgi-bin/material/add_material?type=image`
3. 创建草稿：`POST https://api.weixin.qq.com/cgi-bin/draft/add`

### 脚本位置

`scripts/wechat_publish.py`

### 用法

```bash
python scripts/wechat_publish.py \
  --title "文章标题" \
  --content-file path/to/article.md \
  --cover path/to/cover.jpg \
  --author "狂客同学" \
  --summary-image "https://example.com/summary.jpg"
```

### 参数说明

- `--title`：文章标题（必填）
- `--content-file`：Markdown 内容文件路径（与 `--content` 二选一）
- `--content`：直接传入 HTML 内容（优先于 `--content-file`）
- `--cover`：封面图片路径（必填）
- `--author`：作者名（默认：狂客同学）
- `--digest`：文章摘要（可选）
- `--summary-image`：总结图 URL（可选）

## 标准公众号文章模板

用户固定使用以下结构发布公众号文章，脚本会自动应用此模板：

1. 作者署名行：`文:@狂客同学`
2. 正文内容（Markdown 格式，支持一、二、X 等序号）
3. AI 生成的总结图（可选）
4. 固定结尾文案（含引导互动、联系方式、推特链接）

## 排版规范

### 标题
- 一级标题：`一.` `二.` `X.写在最后` 自动识别为 `<h1>`（微信编辑器内手动设为橙色最大字体）
- 二级标题：`## 标题` 自动识别为 `<h2>`（微信编辑器内手动设为橙色 18 号字体）
- 正文中的序号（一、二、X）使用加粗强调

### 强调与链接
- **微信限制说明**：微信公众号编辑器会过滤 `style` 属性。以下"自动转换"在草稿箱中**可能显示为默认样式**，建议在微信编辑器内手动微调：
  - 重点内容：Markdown `**文本**` → HTML `<strong>` + 蓝色（微信编辑器内手动设色）
  - 链接：URL/邮箱 → HTML `<a>` 标签（微信编辑器内手动加下划线）
- 作者署名：自动插入 `文:@<strong>{author}</strong>`

### 结尾固定文案

```
看到这里，说明你和我的频道很合拍！如果喜欢我的内容，愿请你点赞、点"推荐"，并分享给更多志同道合的朋友。为防走散，记得将公众号设为星标🌟。期待与你共同成长，下篇文章再见！

🔗参考资料见"阅读原文"
🗣️合作/建议:kuangketongxue@gmail.com
🌍本文英文版已经发到我的推特：kuangketongxue
```

### 总结图
- 通过 `--summary-image` 参数传入图片 URL
- 在文章末尾插入，样式 `width: 100%`

## 关键注意事项

### thumb_media_id 必须是永久素材

`draft/add` 接口文档中 `thumb_media_id` 标注为"可选"，但实际是必填。且必须使用永久素材的 media_id（通过 `material/add_material` 上传），不能使用临时素材（`media/upload`）。

若使用临时素材的 media_id，会返回 40007 invalid media_id 错误。

### 微信样式过滤限制

微信公众号编辑器对 HTML `style` 属性支持有限：
- 内联样式会被过滤或忽略
- 颜色/字号/下划线等需要在微信编辑器内手动设置
- 脚本生成的 HTML 仅提供语义结构（`<h1>`/`<h2>`/`<strong>`/`<a>`），视觉样式需在微信后台手动调整

### 正文内容限制

- 微信只支持特定 HTML 子集（`p`, `h1`-`h3`, `strong`, `b`, `ul`, `ol`, `li`, `img`, `a`, `hr`, `br` 等）
- 使用 `media/uploadimg` 上传正文中的图片，返回的 URL 可用于 `<img src="...">`

## 常见错误码

| 错误码 | 含义 | 排查方向 |
|--------|------|----------|
| 40001 | access_token 无效或过期 | 重新获取 token |
| 40007 | media_id 无效 | 确认 thumb_media_id 是永久素材（material/add_material）而非临时素材 |
| 40164 | IP 不在白名单 | 将当前环境 IP 加入公众号后台 IP 白名单 |
| 45106 | 接口已废弃 | 不要使用 material/add_news，使用 draft/add |

## 资源引用

- 详细 API 参数和限制见 references/api_reference.md
- 搜索脚本源码见 scripts/search_wechat.js
- 发布脚本源码见 scripts/wechat_publish.py
