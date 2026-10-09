# coderSkills

前端开发 AI 技能集（Agent Skills 格式）。面向 **Vue 2 / Vue 3 / React Hooks** 项目，覆盖三件事：

| 技能 | 用途 | 典型触发 |
| --- | --- | --- |
| [`frontend-code-modifier`](./frontend-code-modifier/SKILL.md) | 改代码 —— 修 bug、改逻辑、调试 | "帮我修这个"、"改了没生效"、"改 A 影响 B" |
| [`frontend-code-review`](./frontend-code-review/SKILL.md) | 代码评审 —— 带证据的行动清单 | "review 一下"、"这段能不能合并"、"找问题" |
| [`frontend-code-tracer`](./frontend-code-tracer/SKILL.md) | 溯源分析 —— 只分析不改码 | "这个值从哪来"、"为什么不是接口"、"怎么实现的" |

三者共享同一套原则：**先取证再下结论、无代码证据不输出、按风险决定深度**。

## 目录结构

```
coderSkills/
├── README.md
├── frontend-code-modifier/
│   └── SKILL.md          # 前端编程助手（v5 · 风险驱动精简版）
├── frontend-code-review/
│   └── SKILL.md          # 代码评审框架（v6 · 反幻觉强化版）
├── frontend-code-tracer/
│   └── SKILL.md          # 代码溯源分析（v3 · 分级取证与排他闭环版）
└── scripts/
    ├── show-skill.sh     # 打印某个 SKILL.md
    ├── find-symbol.sh    # 搜符号/文本全部出现位置（rg 优先）
    └── show-lines.sh     # 打印文件带行号内容（评审引用证据用）
```

## 格式说明

每个技能目录下是一个标准 `SKILL.md`，YAML frontmatter 含 `name` + `description`（模型据此判断何时加载），正文是工作流指令。可被支持 AgentSkills 的宿主（如 Anthropic Claude Skills、OpenClaw 等）直接加载。

## 安装 / 使用

**方式一 · 作为 Agent 技能目录**
把某个技能目录（如 `frontend-code-modifier/`）放进宿主的技能目录即可。

**方式二 · 手动取用**
```bash
./scripts/show-skill.sh frontend-code-review > review.md
```
直接把内容贴进任意支持长提示词的 AI 编程工具。

## 辅助脚本

```bash
./scripts/find-symbol.sh userName src/       # 搜 userName 的所有出现
./scripts/show-lines.sh src/UserList.vue 40 52   # 打印 40-52 行（带行号）
```

## 许可

内部使用。
