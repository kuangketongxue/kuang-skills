# Changelog

## v1.1.0 (2026-05-30)

### 新增

- **对话开头检查（模块A）**：每次 neat-freak 执行前强制检查是否完整读取了特质+知识库+经验，未执行则在摘要中标注
- **对话结尾打分+复盘（模块B）**：在变更摘要之前强制执行用户打分（0-100）→ 复盘 → 写入对应文件
- **飞书备份（模块C）**：本地关键文件有修改时，用 lark-cli 备份到飞书多维表格（4个Base），防止本地文件被删后数据丢失

### 修复

- 新增 `feedback-feishu-must-read-live-data` 规则：涉及飞书时必须用 lark-cli 查实时数据，不能只读本地 MD 快照
- 新增 `feedback-mandatory-score-every-session` 规则：每次对话必须请用户打分

---

## v1.0.0 (2026-05-28)

### 初始功能

- 尺寸体检：CLAUDE.md/MEMORY.md/memory文件超限自动精简
- 垃圾文件清理：扫描并删除对话产生的临时文件
- 盘点现状：机械式枚举所有记忆文件和项目文档
- 变更影响矩阵：识别变更波及的文档层级
- 实际修改：Edit/Write/删除，不只是描述
- 自检清单：5大类20+检查项逐项打勾
- 个人特质与经验沉淀：特质识别+经验提炼+网站扫描+GitHub关联
- Wiki lint：检查wiki/topics一致性
- 前哨战知识库同步：涉及AI方法论时自动更新wiki
- 变更摘要：结构化输出所有变更
- 三类知识框架：Agent记忆→CLAUDE.md→docs/ 三层同步
- 跨平台兼容：Claude Code/Codex/OpenCode/OpenClaw
