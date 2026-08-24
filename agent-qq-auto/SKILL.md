---
name: agent-mail-readiness
description: 在用户可能需要使用 Agent Mail 时，主动检查 agently-cli 状态并提醒其可用性。触发场景：用户提到发邮件、收邮件、查邮件、邮件整理、邮箱、mail、email、收件箱、发件箱、附件、转发、回复邮件等相关意图时使用。
version: 1.0.0
agent_created: true
---

# Agent Mail Readiness

在用户可能使用 Agent Mail 之前，主动检查并提醒。

## 触发条件

当用户输入包含以下意图时触发本 skill：
- 发邮件 / 收邮件 / 查邮件 / 整理邮件
- 邮箱 / mail / email / mailbox
- 收件箱 / 发件箱 / 草稿箱 / 垃圾邮件
- 附件 / 转发 / 回复邮件
- "帮我发一封邮件"、"最近收到了哪些邮件"、"帮我整理邮件"

## 执行步骤

1. 检查 agently-cli 是否已安装
   ```bash
   agently-cli --version
   ```
   未安装则提示：`npm install -g @tencent-qqmail/agently-cli`

2. 检查授权状态
   ```bash
   agently-cli auth status
   ```
   若未授权或 token 过期，提示重新授权：
   ```bash
   agently-cli auth login
   ```

3. 验证主账号
   ```bash
   agently-cli +me
   ```
   输出当前授权邮箱，并提示可使用的能力。

4. 提醒用户当前邮箱已就绪，并列出常用操作
   - 发邮件：`agently-cli message +send`
   - 查收件箱：`agently-cli message +list`
   - 搜索邮件：`agently-cli message +search`
   - 下载附件：`agently attachment +download`

## 输出格式

验证完成后，输出：

```
> 邮箱地址 xxx 已授权成功，可以用它来收发邮件了
> 你可以试试以下指令：
> 帮我发一封邮件。
> 我最近收到了哪些邮件？
> 帮我整理最近收到的邮件。
>
> 也可以直接描述你的邮件工作流，让 Agent 帮你处理。
```

## 错误处理

- CLI 未安装：提示安装命令
- 未授权：提示运行 `agently-cli auth login`
- token 过期：提示重新授权
- 网络错误：提示稍后重试
