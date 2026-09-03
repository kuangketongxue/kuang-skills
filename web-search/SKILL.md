---
name: web-search
description: >-
  Web 搜索 via Tavily、Firecrawl（含 Developer Index 开发者索引）、知乎 OpenAPI（站内 + 全网）、Exa（深度研究 + 结构化合成）。
  用于研究主题、找 GitHub 仓库、查文档、核实事实、搜中文/知乎内容、查 bug 的 issue/PR、深度多源对比、结构化数据提取。
  私有/需登录域名优先用这些而非 WebFetch。触发：用户要搜东西、查资料、找仓库/skill、核实事实、
  需要知乎站内 / 中文全网搜索、需要深度研究或结构化合成输出。
metadata:
  version: "3.3.1"
  category: search
---

# Web Search

六个搜索引擎给 Agent 提供实时网络搜索能力。API key 从 `~/.claude/.secrets/web-search.env` 自动读取，配置好直接可用（本仓不含 key，重置电脑后需自备，见「API KEY 配置」）。每个引擎都已封装为独立 Python 脚本（stdlib only，**不装第三方 SDK**），**不再使用 `curl | python3 -c` 管道**（该写法在 curl 超时/输出非 JSON 时抛 JSONDecodeError，在 GBK 终端打印中文抛 UnicodeEncodeError，是历史报错根源）。

- **Tavily** — 英文/通用深度搜索，返回摘要+URL
- **Firecrawl** — 网页抓取+结构化搜索，适合读页面、抓仓库结构
- **Firecrawl Developer Index** — 开发者专用索引（2026-08-20 上线）：7000 万+一手 artifact（公共仓库 issue/PR/README、官方文档、OpenAPI spec），语义检索，DevDex 基准 recall@10 0.63 同类最高；查 bug/找仓库/查 API 行为首选
- **知乎站内** — 知乎问答/文章，中文知识、高考复习经验首选
- **全网 (Zhihu global_search)** — 中文全网公开内容，中文语境比 Tavily 更准
- **Exa** — 语义检索 + **深度多步研究（`deep`/`deep-reasoning`）** + **结构化合成（`outputSchema` + 字段级 grounding 引用）**。后两个是现有五引擎都没有的能力：需要跨多源推理对比、或要"列出所有 X / 抽取字段"这种结构化结论时用。Exa API 用 `x-api-key` header，REST 端点 `POST https://api.exa.ai/search`，无需装 `exa-py`

## 什么时候用

- 用户要搜东西、找 GitHub 仓库、查文档、核实事实
- 当前知识可能过时或不确定
- 需要"装 skill"时先确认仓库和安装方式
- 查某个 bug 的 issue/PR、某库的 API 行为、报错信息 → **Developer Index**
- 中文问题、知乎问答、高考/学习经验 → 走知乎站内或全网
- 需要跨多个来源做深度对比/研究、多步推理 → **Exa `deep`/`deep-reasoning`**
- 需要把搜索结果合成结构化数据（"列出所有提到的公司""抽取每个产品的价格"）→ **Exa + `outputSchema`**
- 需要快速查询（聊天/自动补全，要 <1s）→ **Exa `fast`/`instant`**

**不用时的情况**：纯代码阅读/编辑/调试、已知事实的常识问答。

## 六个引擎怎么选

| 引擎 | 擅长 | 中文 | 调用方式 |
|---|---|---|---|
| **Tavily** | 通用深度搜索，摘要+URL，查概念/找答案 | 一般 | `python3 scripts/tavily-search.py` |
| **Firecrawl** | 抓页面、读仓库结构，返回结构化内容 | 一般 | `python3 scripts/firecrawl-search.py` |
| **Firecrawl Developer** | 找仓库/查 issue/PR/官方文档 passage，一手来源 | 一般 | `python3 scripts/firecrawl-dev.py` |
| **知乎站内** | 知乎问答/文章，学习/高考复习经验 | 强 | `python3 scripts/zhihu-search.py` |
| **全网** | 中文全网公开内容，新闻/政策/资讯 | 强 | `python3 scripts/global-search.py` |
| **Exa** | 语义检索 + 深度多源研究 + 结构化合成输出 | 已验证可用（09-03 实测返回相关中文结果）；深度中文经验仍主力知乎 | `python3 scripts/exa-search.py` |

**路由原则（铁律：默认并行带知乎）**：
- **默认每次搜索都并行带上知乎（全网，必要时加站内）**。用户中文场景占绝大多数，知乎 OpenAPI 稳定、对中文资源（含 GitHub 仓库、网盘、学习资料）命中率高于 Tavily/Firecrawl。**除非查询是纯英文技术文档/英文概念，否则知乎不该缺席**——曾因"找仓库"只走 Tavily+Firecrawl 而漏掉知乎上的中文仓库/数据集资源。
- 知乎问答 / 学习方法 / 高考复习经验 → **知乎站内 + 全网**
- 中文全网新闻、政策、中文概念 → **全网**
- 英文/通用、查文档、找答案 → **Tavily + Exa + 知乎全网 三路并行**（Exa 补语义召回盲区，`publishedDate` 可判时效；别只留 Tavily）
- 抓具体页面内容、读仓库结构 → **Firecrawl scrape**（见下文 `/v1/scrape`，与搜索端点不同）
- **代码类查询 → Firecrawl Developer 打头**：描述能力找仓库（"a library for incremental PDF parsing"）、bug 定位（"报错信息 + 库名"）、API 合同溯源（"how do I configure retries <库名>"）。DevDex 数据：issue/PR 分辨率 track 0.66 第一，仓库发现 0.76 仅次 Parallel；文档 lookup 偏弱（0.47），纯 how-to 文档查询配 Tavily 并行
- **找 GitHub 仓库 / 开源数据集 → Firecrawl Developer + Tavily + 知乎全网 三路并行**（英文仓库名/能力描述走 Developer，中文仓库、网盘资源知乎更易命中）
- **需要深度研究/跨源对比/多步推理 → Exa `deep` 或 `deep-reasoning`**（Tavily/Firecrawl 只返回结果不合成，Developer 不做推理；这是 Exa 的独门场景）
- **需要结构化提取（列出所有 X、抽字段）→ Exa + `outputSchema`**，脚本默认把 `output.content` 追加在 results 之后打印
- 单点快速核实（某版本号/某事实/某 changelog 条目）→ **Exa `instant`/`fast`**（本机实测 ~5s 端到端出结果，常直击一手文档）；时效敏感查询（新版本/新闻/公告）→ Exa `maxAgeHours:24` + 知乎全网 `realtime` 并行
- 拿不准 → 知乎全网 + 另一个都试，并行（见下"并行搜索"）

## API KEY 配置（本地，不进仓）

6 个脚本**不含任何硬编码 key**。启动时自动读取 `~/.claude/.secrets/web-search.env`，该文件不存在时回退到同名 shell 环境变量。

| 环境变量 | 用途 |
|---|---|
| `TAVILY_API_KEY` | Tavily 搜索（单 key 兼容；设了 `TAVILY_API_KEYS` 时被后者覆盖） |
| `TAVILY_API_KEYS` | Tavily 多 key（逗号分隔，主用在前）；主 key 额度耗尽自动切下一个 |
| `FIRECRAWL_API_KEY` | Firecrawl v1 search + Firecrawl Developer Index（共用，单 key 兼容） |
| `FIRECRAWL_API_KEYS` | Firecrawl 多 key（逗号分隔）；两个 Firecrawl 脚本共用同一组，额度耗尽自动切 |
| `ZHIHU_ACCESS_SECRET` | 知乎 OpenAPI（站内 + 全网共用，Bearer） |
| `EXA_API_KEY` | Exa `/search`（`x-api-key` header 发送，不是 Bearer、不放 body） |

**多 key 额度 fallback**（Tavily / Firecrawl，v3.3.0 新增）：`*_API_KEYS` 逗号分隔，主用在前、备用在后。脚本遇 `402`/`429`（或 `403` 且响应体含 quota/limit/rate/usage/exceeded 关键词）即认定当前 key 额度耗尽，**自动切下一个 key 重试**；`401`/`400` 等其他 4xx 不误判为额度耗尽，直接报错。所有 key 都耗尽才报 `all N keys exhausted`。key 在错误输出里全部脱敏（`***`）。

首次配置 / 重置电脑后恢复：

```bash
mkdir -p ~/.claude/.secrets
cp ~/.claude/skills/web-search/.env.example ~/.claude/.secrets/web-search.env
# 用真实 key 填好 web-search.env（.env.example 里是占位符，不含真 key）
```

- 取 key 的地方：Tavily `app.tavily.com`、Firecrawl `firecrawl.dev`、知乎 OpenAPI `developer.zhihu.com`、Exa `dashboard.exa.ai`
- 脚本输出会自动把 key/secret 替换成 `***`，不会泄露到日志
- 未配置 key 时不抛 traceback，输出 `{"error":"missing TAVILY_API_KEY — set in ~/.claude/.secrets/web-search.env or TAVILY_API_KEY env var","exit_code":1}`（Exa 同理，报 `missing EXA_API_KEY`）

## 调用命令模板（统一）

**所有 6 引擎统一调用方式**：`PYTHONIOENCODING=utf-8 python3 <script> '<JSON>' [--raw]`
- 脚本内部已 `sys.stdout.reconfigure(encoding='utf-8')` 强制 utf-8 输出，命令前缀 `PYTHONIOENCODING=utf-8` 是双保险
- 默认输出**格式化可读文本**（每行一条结果）；`--raw` 输出原始 JSON（向后兼容旧管道用法）
- HTTP 错误/超时/JSON 解析失败 → 输出 `{"error":"具体原因","exit_code":1}` 且 exit 1，**不抛 traceback**
- Tavily/Firecrawl/Firecrawl-dev：45s 超时，网络错误/5xx 重试 1 次（间隔 2s）；4xx 中 `402`/`429`（额度耗尽）自动切下一个备用 key（需配 `*_API_KEYS`），其他 4xx 直接报错
- Exa：超时时长按 `type` 动态（`instant` 15s / `fast` 30s / `auto` 45s / `deep-lite` 60s / `deep` 90s / `deep-reasoning` 120s），4xx 直接报错、其他失败重试 1 次
- key/secret 在错误输出里脱敏（`***`）

路径说明：`~/.claude/skills/web-search/scripts/xxx.py` 在 Git Bash 里 = `C:\Users\kuang\.claude\skills\web-search\scripts\xxx.py`。若 `~` 不展开用绝对路径。

### Tavily

```bash
# 默认格式化输出（每行：title | url | content[:200]）
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/tavily-search.py \
  '{"query":"Claude Code update","max_results":5,"search_depth":"basic"}'

# 原始 JSON
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/tavily-search.py \
  '{"query":"Claude Code update","max_results":5,"search_depth":"advanced"}' --raw
```

- 参数：`query`（必填）、`max_results`（默认 5，1–10）、`search_depth`（`basic` 默认 / `advanced` 深但慢）
- 返回字段：`results[].title/url/content/score`

### Firecrawl（v1 search）

```bash
# 默认格式化输出（每行：title | url | description[:200]）
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/firecrawl-search.py \
  '{"query":"Claude Code","limit":5}'

# 原始 JSON
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/firecrawl-search.py \
  '{"query":"Claude Code","limit":5}' --raw
```

- 参数：`query`（必填）、`limit`（默认 5）
- 返回字段：`data[].title/url/description`

### Firecrawl Developer Index（开发者索引，/v2/search/developer）

```bash
# 默认格式化输出（每行：id | url | (title or '(no title)') | passages首段[:150]）
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/firecrawl-dev.py \
  '{"query":"claude code update failed npm registry"}'

# 原始 JSON
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/firecrawl-dev.py \
  '{"query":"claude code update failed npm registry","k":10}' --raw
```

- 参数：`query`（必填，英文最佳）、`k`（默认 10）
- **注意是 `/v2/` 路径**（与 Firecrawl v1 不同）；需要 `FIRECRAWL_API_KEY`（与 Firecrawl v1 共用同一把），未配置时输出明确错误提示
- 计费：每 10 条结果 2 credits（向上取整）
- 返回字段：`results[].id`（前缀即类型：`doc:` / `issue:` / `pull_request:` / `readme:`，如 `issue:owner/repo#123`）、`url`、`passages[]`（markdown 匹配片段，含代码块）、`title`（doc 类型常缺，脚本用 `(no title)` 兜底）。脚本兼容 `results` 与 `data` 两种键名
- passages 兼容：可能是 `list[{"text":...}]`、`str` 或 `None`，脚本统一取首段
- 数组过滤器用 POST 同路径：`{"query":"...","k":10,"types":["issue","pull_request"]}`
- 可选过滤（仅 API）：`types`、`repos`、`sources`、`language`、`topic`、`license`、`min_stars`、`archived`、`fork`；`skills:"only"` 只搜 agent skill 文件
- 坑：`language/topic/license/min_stars` 等仓库属性过滤会排除 doc 结果（这些过滤器描述的是代码仓库）；带仓库属性过滤时别指望返回官方文档
- 混合网页结果用 `POST /v2/search` + `"categories":["developer"]`（不能与其他 category 组合），但该形态没有 passages——要匹配片段就用本端点

### 知乎站内（zhihu_search）

```bash
# 默认格式化输出（每行：Title | Url | AuthorName | VoteUpCount | ContentText[:200]）
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/zhihu-search.py \
  '{"query":"高三如何提高成绩","count":5}'

# 原始 JSON
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/zhihu-search.py \
  '{"query":"高三如何提高成绩","count":5}' --raw
```

- `query` 必填；`count` 默认 10，范围 1–10。
- 响应：`Code`（0=成功）、`Message`、`Data.HasMore`、`Data.SearchHashId`、`Data.Items[]`。
- 每项含 `Title`、`ContentType`、`ContentID`、`ContentText`、`Url`、`VoteUpCount`、`AuthorName`、`EditTime`、`RankingScore`。

### 全网（global_search）

```bash
# 默认格式化输出（每行：Title | Url | ContentText[:200]）
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/global-search.py \
  '{"query":"2026 高考新政","count":8,"search_db":"all"}'

# 原始 JSON
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/global-search.py \
  '{"query":"2026 高考新政","count":8,"search_db":"all"}' --raw
```

- `query` 必填；`count` 默认 10，范围 1–20。
- `filter` 可选，高级筛选表达式（如 `host=="example.com"`）。
- `search_db` 支持 `all`（默认）、`realtime`（实时）、`static`（静态）。
- 响应结构同知乎站内。

### Exa（/search，含深度研究 + 结构化合成）

```bash
# 默认格式化输出（每行：title | url | highlights首段[:200]）
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/exa-search.py \
  '{"query":"recent AI safety papers","numResults":5}'

# 深度研究（多步推理，4-15s）+ 原始 JSON
PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/exa-search.py \
  '{"query":"compare Rust vs Go for CLI tools","type":"deep","numResults":8}' --raw
```

- 参数：`query`（必填）、`type`（默认 `auto`）、`numResults`（默认 5，1–10）
- `type` 选项：`instant`(~250ms) / `fast`(~450ms) / `auto`(~1s，默认) / `deep-lite`(~4s) / `deep`(4-15s) / `deep-reasoning`(12-40s)。需要多步推理/复杂综合才上 `deep`+，简单查询用 `auto` 就够
- 返回字段：`results[].id/title/url/highlights[]`（highlights 是字符串数组，脚本取首段）；请求 `contents.text` 时还有 `text`；`publishedDate` 常带
- **内容模式 `contents`**（默认 `{"highlights": true}`）：
  - `{"highlights": true}` — 查询相关摘录，token 高效，**默认**
  - `{"text": {"maxCharacters": 20000}}` — 全文抽取（RAG/需要页面全貌时），务必带 `maxCharacters` 控 token
  - `{"summary": true}` — 每条结果的 LLM 摘要（`{"summary": {"query": "..."}}` 可偏焦特定问题）
  - 三者通常**只选一个**，混用是反模式
- **域名过滤**：`includeDomains: ["arxiv.org","github.com"]`、`excludeDomains: ["pinterest.com"]`，可一起用（包含大域排除子域）
- **内容新鲜度** `maxAgeHours`：`24`=缓存不足 24h 才 livecrawl、`1`=近实时、`0`=总是 livecrawl、`-1`=纯缓存、省略=默认（无缓存才 livecrawl）。历史/教育内容别强制 livecrawl
- **结构化合成** `systemPrompt` + `outputSchema`（任意 `type` 都支持，`deep` 变体质量更高）：传 JSON schema，Exa 在 `output.content` 返回合成结构化数据、`output.grounding` 返回字段级引用。schema 嵌套深度≤2、总属性≤10，**不要加 citation/confidence 字段**（grounding 自动返回）。脚本默认把 `output.content` 追加在 results 之后打印，`--raw` 看完整含 grounding
  ```bash
  PYTHONIOENCODING=utf-8 python3 ~/.claude/skills/web-search/scripts/exa-search.py \
    '{"query":"companies building AI coding agents","type":"deep-lite",
      "systemPrompt":"Prefer official sources, keep output grounded.",
      "outputSchema":{"type":"object","properties":{"companies":{"type":"array","items":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}}},"required":["companies"]}}'
  ```
  > 嵌套 JSON 在 shell 单引号里易被破坏（`json.loads` 报 Invalid JSON payload）；复杂 payload 先 Write 到临时文件再用 `"$PAYLOAD"` 传参，跑完清理
- 与 Developer Index 的分工：查 issue/PR/README 一手 artifact 仍走 Developer（DevDex 命中率高）；Exa 的价值在**跨源推理**和**结构化合成**，两者互补
- 中文已实测可用（2026-09-03：高考复习中文查询返回相关中文站点；但深度经验内容弱于知乎一手答案）——中文场景 Exa 作补充引擎，主力仍知乎

### Firecrawl 抓页面（/v1/scrape，不是搜索，保留 curl）

```bash
# 抓单个页面内容，返回 markdown。失败重试 1 次。
# curl 不像 Python 脚本会自动加载 key——先 source（set -a 让赋值自动 export 给子进程）：
set -a; source ~/.claude/.secrets/web-search.env; set +a
curl -s --ssl-no-revoke --max-time 60 -X POST "https://api.firecrawl.dev/v1/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -d '{"url":"https://example.com","formats":["markdown"]}'
```

- 这是**抓页面**不是搜索，与上面的 `firecrawl-search.py`（v1 search 端点）是两件事。看链接内容（给个 URL 要读页面）走这条，不走搜索脚本。
- `--ssl-no-revoke` 在中国网络下绕过证书吊销检查失败；scrape 失败重试 1 次。

## 关键坑：Windows GBK 编码

**脚本已内部强制 utf-8 输出**（`sys.stdout.reconfigure(encoding='utf-8', errors='replace')`），中文/emoji 不会再 `UnicodeEncodeError: 'gbk' codec`。命令前缀 `PYTHONIOENCODING=utf-8` 是双保险，仍建议带上。详见 CLAUDE.md「GBK 编码坑」。

历史教训：旧写法 `curl ... | python3 -c "json.load(sys.stdin)..."` 有两个致命点——curl 超时/失败/输出非 JSON 时 `json.load` 抛 `JSONDecodeError`（如 "Expecting ',' delimiter"）；`python3 -c` 过滤在 GBK 终端打印中文抛 `UnicodeEncodeError`。现统一改用独立脚本，两个问题一并消除。

## 网络慢的处理

GitHub 直连经常超时。搜索 API 是可靠的替代路径：
1. 先搜目标 → 拿到 URL 和摘要
2. 拿到 URL 后用 `gh api repos/owner/repo/contents/...` 拉具体文件（gh 已登录）
3. 或用 Firecrawl `/v1/scrape` 直接抓页面内容

## 并行搜索

六个引擎独立，可并行调用（同一 Bash 命令里分多个 `python3` 子进程，或同一条消息里多个工具调用），加速覆盖。常见组合：
- 中文问题：知乎站内 + 全网 并行
- 通用问题：Tavily + Exa + 全网 三路并行
- 代码类（找仓库 / 查 bug issue/PR / API 行为）：**Firecrawl Developer + Tavily + 知乎全网 三路并行**
- 找仓库 / 数据集：同上三路（英文能力描述 Developer 命中率最高，中文仓库、网盘资源知乎命中率更高，别漏；曾因只走 Tavily+Firecrawl 翻车）
- 深度研究 / 跨源对比：Exa `deep`（+ Tavily 交叉验证），别只靠单引擎
- 结构化提取（列清单/抽字段）：Exa `auto`/`deep-lite` + `outputSchema`，单引擎即可

## 返回格式（强制：每次搜索都写明来源）

搜索后给用户结论，不要贴原始 JSON（要看原始数据用 `--raw`）。**来源必须逐条标注，不可只给结论或"网上的说法是…"**：
- **每条结果都带标题 + URL**（知乎/全网结果带作者），不只挑几条列来源
- 结论里的关键说法尽量追溯到某条来源（如"见上条①"或直接内联 URL）
- 列成编号列表，方便用户点开核对
- 末尾给推荐的下一步动作

## 注意事项

- 脚本超时已设（Tavily/Firecrawl/Dev 45s，知乎 5s，Exa 按 `type` 15–120s）；超时会重试 1 次（2s 间隔）或输出 `{"error":...,"exit_code":1}`，不要死等
- 输出可能很长，默认格式化已截断（content/description 200 字符，passages 150 字符，Exa highlights/text 200 字符）；要看全量用 `--raw`
- Tavily 的 `content` 有时为空，Firecrawl 的 `description` 有时为空，Exa 的 `highlights` 有时为空（脚本会回退到 `text`），哪个有内容用哪个
- 脚本失败会输出 `{"error":...,"exit_code":1}`；看 error 信息检查参数/认证/网络/频率
