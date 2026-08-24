# Adversarial Debate（对抗性辩论审查）

<p align="center">
  <a href="https://github.com/kuangketongxue/adversarial-debate/releases"><img src="https://img.shields.io/github/v/release/kuangketongxue/adversarial-debate?label=release&color=blue" alt="release"></a>
  <a href="https://github.com/kuangketongxue/adversarial-debate/stargazers"><img src="https://img.shields.io/github/stars/kuangketongxue/adversarial-debate?style=flat&logo=github&color=yellow" alt="stars"></a>
  <a href="https://github.com/kuangketongxue/adversarial-debate/forks"><img src="https://img.shields.io/github/forks/kuangketongxue/adversarial-debate?style=flat&logo=github" alt="forks"></a>
  <a href="https://github.com/kuangketongxue/adversarial-debate/issues"><img src="https://img.shields.io/github/issues/kuangketongxue/adversarial-debate?style=flat&logo=github" alt="issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
</p>

<p align="center"><em>Claude Code skill · 对抗性辩论审查</em></p>


> 对抗性审查 + 第一性原理的多角色辩论：正方构建最强支持论证，反方专职攻击，裁判只按客观规律裁决。回答一个问题——**你的目标到底能不能达成？**

## 为什么需要

问 AI「我这个计划可行吗」，最常见的两种废答：

1. **谄媚式**：「这是个很棒的想法！当然可以！」——零信息量
2. **和稀泥式**：「双方都有道理，要辩证看待」——等于没说

本 skill 强制 AI 分饰三角，把模糊的直觉之争变成可裁决的结构化辩论：

| 角色 | 职责 | 约束 |
|---|---|---|
| ✅ 正方 | 构建最强支持论证 | 只能从事实底座推导，须自曝最薄弱处 |
| ❌ 反方 | 专职推翻 | 必须攻击最强版本（steelman），标注杀伤力 |
| ⚖️ 裁判 | 客观裁决 | 禁止和稀泥；判定三选一 + 置信度 + 关键变量 |

## 三条铁律

1. **第一性原理** — 每个论点落到可验证的事实、数字、因果链。「大家都这么做」「专家说」出现即无效。
2. **对抗性** — 反方攻击的是论点的最强版本；被有效驳倒的论点双方不得复用。
3. **客观裁决** — 结论只能是「能 / 不能 / 有条件能」，附置信度与决定成败的关键变量（≤3 个）。

## 用法

在 Claude Code 里：

```
辩一下：我高三最后一年想从 500 分提到 650，现实吗？
```

或明确触发：

```
用 adversarial-debate 审查这个目标：……
```

输出结构：🎯 既定目标 → 📋 事实底座 → ✅ 正方立论 → ❌ 反方攻击 → 🔁 交锋 → ⚖️ 裁决（固定格式，含置信度与下一步验证动作）。

## 安装

```bash
# Claude Code
git clone https://github.com/kuangketongxue/adversarial-debate.git
cp -r adversarial-debate/skills/adversarial-debate ~/.claude/skills/
```

或手动复制 `skills/adversarial-debate/SKILL.md` 到 `~/.claude/skills/adversarial-debate/SKILL.md`。

## 设计取舍

- **裁判可以判用户输。** 辩论的意义是让你在现实碰壁前先撞见真相，所以禁止情绪化鼓励。
- **事实底座先行。** 没有共享事实的辩论必然沦为各说各话；所有论证只能引用底座 + 公认规律。
- **待验证 ≠ 已确立。** 交锋中出现的新争议事实必须标注「待验证」，不得当论据使用。
- **裁决必须回指论点。** 不接受「综合来看」这种无法证伪的措辞。

## License

MIT
