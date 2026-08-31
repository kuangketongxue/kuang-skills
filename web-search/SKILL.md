---
name: web-search
description: >-
  Web 搜索 via Tavily、Firecrawl（含 Developer Index 开发者索引）、知乎 OpenAPI（站内 + 全网）。
  用于研究主题、找 GitHub 仓库、查文档、核实事实、搜中文/知乎内容、查 bug 的 issue/PR。
  私有/需登录域名优先用这些而非 WebFetch。触发：用户要搜东西、查资料、找仓库/skill、
  核实事实、或需要知乎站内 / 中文全网搜索。
metadata:
  version: "3.1.0"
  category: search
---

# Web Search

五个搜索引擎给 Agent 提供实时网络搜索能力。API key 从 `~/.claude/.secrets/web-search.env` 自动读取，配置好直接可用（本仓不含 key，重置电脑后需自备，见「API KEY 配置」）。每个引擎都已封装为独立 Python 脚本（stdlib only），**不再使用 `curl | python3 -c` 管道**（该写法在 curl 超时/输出非 JSON 时抛 JSONDecodeError，在 GBK 终端打印中文抛 UnicodeEncodeError，是历史报错根源）。

- **Tavily** — 英文/通用深度搜索，返回摘要+URL
- **Firecrawl** — 网页抓取+结构化搜索，适合读页面、抓仓库结构
- **Firecrawl Developer Index** — 开发者专用索引（2026-08-20 上线）：7000 万+一手 artifact（公共仓库 issue/PR/README、官方文档、OpenAPI spec），语义检索，DevDex 基准 recall@10 0.63 同类最高；查 bug/找仓库/查 API 行为首选
- **知乎站内** — 知乎问答/文章，中文知识、高考复习经验首选
- **全网 (Zhihu global_search)** — 中文全网公开内容，中文语境比 Tavily 更准

## 什么时候用

- 用户要搜东西、找 GitHub 仓库、查文档、核实事实
- 当前知识可能过时或不确定
- 需要"装 skill"时先确认仓库和安装方式
- 查某个 bug 的 issue/PR、某库的 API 行为、报错信息 → **Developer Index**
- 中文问题、知乎问答、高考/学习经验 → 走知乎站内或全网

**不用时的情况**：纯代码阅读/编辑/调试、已知事实的常识问答。

## 五个引擎怎么选

| 引擎 | 擅长 | 中文 | 调用方式 |
|---|---|---|---|
| **Tavily** | 通用深度搜索，摘要+URL，查概念/找答案 | 一般 | `python3 scripts/tavily-search.py` |
| **Firecrawl** | 抓页面、读仓库结构，返回结构化内容 | 一般 | `python3 scripts/firecrawl-search.py` |
| **Firecrawl Developer** | 找仓库/查 issue/PR/官方文档 passage，一手来源 | 一般 | `python3 scripts/firecrawl-dev.py` |
| **知乎站内** | 知乎问答/文章，学习/高考复习经验 | 强 | `python3 scripts/zhihu-search.py` |
| **全网** | 中文全网公开内容，新闻/政策/资讯 | 强 | `python3 scripts/global-search.py` |

**路由原则（铁律：默认并行带知乎）**：
- **默认每次搜索都并行带上知乎（全网，必要时加站内）**。用户中文场景占绝大多数，知乎 OpenAPI 稳定、对中文资源（含 GitHub 仓库、网盘、学习资料）命中率高于 Tavily/Firecrawl。**除非查询是纯英文技术文档/英文概念，否则知乎不该缺席**——曾因"找仓库"只走 Tavily+Firecrawl 而漏掉知乎上的中文仓库/数据集资源。
- 知乎问答 / 学习方法 / 高考复习经验 → **知乎站内 + 全网**
- 中文全网新闻、政策、中文概念 → **全网**
- 英文/通用、查文档、找答案 → **Tavily + 知乎全网**（并行，别只留 Tavily）
- 抓具体页面内容、读仓库结构 → **Firecrawl scrape**（见下文 `/v1/scrape`，与搜索端点不同）
- **代码类查询 → Firecrawl Developer 打头**：描述能力找仓库（"a library for incremental PDF parsing"）、bug 定位（"报错信息 + 库名"）、API 合同溯源（"how do I configure retries <库名>"）。DevDex 数据：issue/PR 分辨率 track 0.66 第一，仓库发现 0.76 仅次 Parallel；文档 lookup 偏弱（0.47），纯 how-to 文档查询配 Tavily 并行
- **找 GitHub 仓库 / 开源数据集 → Firecrawl Developer + Tavily + 知乎全网 三路并行**（英文仓库名/能力描述走 Developer，中文仓库、网盘资源知乎更易命中）
- 拿不准 → 知乎全网 + 另一个都试，并行（见下"并行搜索"）

## API KEY 配置（本地，不进仓）

5 个脚本**不含任何硬编码 key**。启动时自动读取 `~/.claude/.secrets/web-search.env`，该文件不存在时回退到同名 shell 环境变量。

| 环境变量 | 用途 |
|---|---|
| `TAVILY_API_KEY` | Tavily 搜索 |
| `FIRECRAWL_API_KEY` | Firecrawl v1 search + Firecrawl Developer Index（共用同一把 key） |
| `ZHIHU_ACCESS_SECRET` | 知乎 OpenAPI（站内 + 全网共用，Bearer） |

首次配置 / 重置电脑后恢复：

```bash
mkdir -p ~/.claude/.secrets
cp ~/.claude/skills/web-search/.env.example ~/.claude/.secrets/web-search.env
# 用真实 key 填好 web-search.env（.env.example 里是占位符，不含真 key）
```

- 取 key 的地方：Tavily `app.tavily.com`、Firecrawl `firecrawl.dev`、知乎 OpenAPI `developer.zhihu.com`
- 脚本输出会自动把 key/secret 替换成 `***`，不会泄露到日志
- 未配置 key 时不抛 traceback，输出 `{"error":"missing TAVILY_API_KEY — set in ~/.claude/.secrets/web-search.env or TAVILY_API_KEY env var","exit_code":1}`

## 调用命令模板（统一）

**所有 5 引擎统一调用方式**：`PYTHONIOENCODING=utf-8 python3 <script> '<JSON>' [--raw]`
- 脚本内部已 `sys.stdout.reconfigure(encoding='utf-8')` 强制 utf-8 输出，命令前缀 `PYTHONIOENCODING=utf-8` 是双保险
- 默认输出**格式化可读文本**（每行一条结果）；`--raw` 输出原始 JSON（向后兼容旧管道用法）
- HTTP 错误/超时/JSON 解析失败 → 输出 `{"error":"具体原因","exit_code":1}` 且 exit 1，**不抛 traceback**
- Tavily/Firecrawl/Firecrawl-dev：45s 超时，失败重试 1 次（间隔 2s）；4xx 不重试（客户端错误重试无意义）
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

五个引擎独立，可并行调用（同一 Bash 命令里分多个 `python3` 子进程，或同一条消息里多个工具调用），加速覆盖。常见组合：
- 中文问题：知乎站内 + 全网 并行
- 通用问题：Tavily + 全网 并行
- 代码类（找仓库 / 查 bug issue/PR / API 行为）：**Firecrawl Developer + Tavily + 知乎全网 三路并行**
- 找仓库 / 数据集：同上三路（英文能力描述 Developer 命中率最高，中文仓库、网盘资源知乎命中率更高，别漏；曾因只走 Tavily+Firecrawl 翻车）

## 返回格式（强制：每次搜索都写明来源）

搜索后给用户结论，不要贴原始 JSON（要看原始数据用 `--raw`）。**来源必须逐条标注，不可只给结论或"网上的说法是…"**：
- **每条结果都带标题 + URL**（知乎/全网结果带作者），不只挑几条列来源
- 结论里的关键说法尽量追溯到某条来源（如"见上条①"或直接内联 URL）
- 列成编号列表，方便用户点开核对
- 末尾给推荐的下一步动作

## 注意事项

- 脚本超时已设（Tavily/Firecrawl/Dev 45s，知乎 5s）；超时会重试 1 次（2s 间隔）或输出 `{"error":...,"exit_code":1}`，不要死等
- 输出可能很长，默认格式化已截断（content/description 200 字符，passages 150 字符）；要看全量用 `--raw`
- Tavily 的 `content` 有时为空，Firecrawl 的 `description` 有时为空，哪个有内容用哪个
- 脚本失败会输出 `{"error":...,"exit_code":1}`；看 error 信息检查参数/认证/网络/频率
