# EXTEND.md — 你的个性化配置

> 复制这个文件，去掉注释，填入你的配置。不需要的模块直接删掉对应段落。

## 特质追踪（可选）

```markdown
## 特质追踪
- 特质文件：`memory/user_traits.md`
- 编号规则：T1, T2, T3...（按出现顺序递增，从 T1 开始）
- 写入格式：`- **Txx**：特质描述（日期）`
- 统计表：文件末尾按类别汇总
```

## 经验沉淀（可选）

```markdown
## 经验沉淀
- 经验文件：`notes/experience.md`
- 写入章节：`## 可复用经验（YYYY-MM-DD 补充）`
- 写入格式：`- **标题**：经验内容`
```

## 额外同步检查（可选）

```markdown
## 额外同步步骤
- 对话结束前扫描 `personal-site/index.html` 是否有新内容需要更新
- 对话前读取 `notes/interview-summary.md` 获取用户背景
```

## GitHub 配置（可选）

```markdown
## GitHub
- 用户名：your-github-username
- 重点关注的 topics：ai, agent, cli, productivity
```

## 飞书 Base 配置（可选）

> 如果你使用飞书多维表格存储数据，配置此项后 neat-freak 会自动检查 Base 健康状态。

```markdown
## 飞书 Base
- 工具：lark-cli（必须已安装并认证）
- 同步规则：references/feishu-sync.md
- Base 列表：
  - Base1（wiki）: TnTpb4IpzaA1xxsH48ucdYW7nDc — 阅读/赚钱
    - wiki映射：前哨战.md→浪前前哨战，AI术方法论.md/赚100万.md→赚钱
  - Base2（wiki）: DcJzbLadCaGbGws2ZekchGHhnVe — 高考
    - wiki映射：高考上清华.md→【新】每日追踪
  - Base3（base）: LN8zbJJujajX7js9zNmcEk3sncg — 健康
  - Base4（base）: ShnWbRi11a7Ge4sCMEEcGoaRnuz — 财务/自由
- 健康检查重点：
  - 公式字段是否报错（已知问题：COUNT/FILTER嵌套→COUNTIF+SUMIF）
  - 视图字段顺序是否合理
  - wiki修改是否已同步到Base
  - Base重大变化是否已回写wiki
```
