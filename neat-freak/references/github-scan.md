# 全平台内容扫描参考（Data Sources Scanning）

Neat-Freak 不只扫描 GitHub。它能扫描你所有平台的内容沉淀，与当前对话主题交叉比对。

## 工具链安装与检查

### GitHub CLI (gh)

**检查是否已安装：**

```bash
gh auth status 2>/dev/null
```

**未安装时自动安装：**

| 平台 | 安装命令 |
|------|---------|
| macOS | `brew install gh` |
| Linux (apt) | `sudo apt install gh` |
| Linux (yum) | `sudo yum install gh` |
| Windows | `winget install GitHub.cli` |

安装后认证：`gh auth login`

**如果 gh 不可用 → 跳过 GitHub，不影响其他数据源扫描。**

### 其他工具

所有非 GitHub 数据源只需要 `cat`、`find` 等系统内置命令，无需额外安装。

---

## GitHub 数据采集

### 第一路：我的仓库 + 我的 star

```bash
# 全量自有仓库
gh repo list --limit 100 --json name,description,updatedAt,stargazersCount,primaryLanguage,url

# 全量 star（带 topics 标签）
gh api --paginate user/starred -q '.[] | "\(.full_name) | stars:\(.stargazers_count) | \(.language // "N/A") | \(.topics // []) | \(.description // "N/A")"'
```

### 第二路：GitHub 全站搜索（按 star 排序）

gh api search/repositories -f q="关键词1 关键词2" -f sort="stars" -f per_page=5 --jq '.items[] | "\(.full_name) | stars:\(.stargazers_count) | \(.description[0:60] // "N/A")"'
```

或者用 `gh search repos`（更简洁）：

```bash
gh search repos "关键词1 关键词2" --sort stars --limit 5 --json fullName,description,stargazersCount --jq '.[] | "\(.full_name) | ⭐\(.stargazers_count) | \(.description[0:60] // "N/A")"'
```

---

## 非 GitHub 内容源（静默兜底）

这些源不需要额外安装任何工具，直接读本地文件。如果文件不存在，静默跳过。

| 数据源 | 读取方式 | 提取内容 |
|--------|---------|---------|
| 小红书收藏 JSON | `cat <path> \| jq '.items[] \| {title, desc, tags}'` | 标题、描述、标签 |
| B站收藏 JSON | `cat <path> \| jq '.data[] \| {title, desc, tag}'` | 标题、描述、标签 |
| YouTube 收藏 JSON | `cat <path> \| jq '.. \| .title?'` | 标题 |
| Twitter 收藏 JSON | `cat <path> \| jq '.[] \| {full_text, created_at}'` | 正文、时间 |
| 浏览器书签 HTML | 解析 `DT` / `A` 标签提取 `text` 和 `href` | 标题、URL |
| 飞书 Markdown 目录 | `find <dir> -name "*.md"` 逐文件读首段 | 文件名、前 200 字 |

> 如果 `jq` 未安装，JSON 源可改用 Python 解析（`python3 -c "import json,sys; json.load(sys.stdin)"`），或直接跳过。

---

## 关键词提取规则

从本次对话主题中提取 2-3 个核心关键词：
- 主概念（如 `gaokao`、`agent`、`react`）
- 辅助限定（如 `python`、`cli`、`tutorial`）
- 避免太宽泛的词（如 `ai`、`web`、`app`）
- 中英文都试，优先用英文（GitHub 上英文匹配更准）

## 交叉比对逻辑

```
所有数据源提取关键词 → 去重合并 → 与对话主题计算语义匹配
    ├─ 高度相关 → 输出到"全平台内容关联"章节
    ├─ 中度相关 → 在摘要中"值得注意"
    └─ 无关 → 静默丢弃
```

## 数据用途

采集后仅与**本次对话主题**交叉比对，判断哪些内容对当前对话有帮助。不持久化、不存储。