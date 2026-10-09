# coderSkills

面向 **Vue 2 / Vue 3 / React Hooks** 的前端 AI 技能集，采用 Agent Skills 目录格式。三个 skill 分别负责修改、评审和溯源，也能按用户目标衔接执行。

| Skill（中文显示名称） | 交付结果 | 典型请求 |
| --- | --- | --- |
| [修改web代码](修改web代码/SKILL.md) | 完成修改，解释原因，报告实际验证结果 | “帮我修这个”“改了没生效”“改 A 影响 B” |
| [评审web代码](评审web代码/SKILL.md) | 按严重程度排序、有触发条件与证据的问题清单 | “review 一下”“这段能不能合并”“找回归” |
| [溯源web代码](溯源web代码/SKILL.md) | 解释来源、路径、条件与覆盖关系，默认只读 | “这个值从哪来”“为什么不是接口”“怎么实现的” |

共同原则：**按风险选择深度，关键结论能核查，静态推导与运行观察分开报告**。简单问题直接回答或修改；缺少上下文时，先完成能独立确认的部分。

## 本次升级

- **减轻主流程**：常用指令放在 `SKILL.md`，框架陷阱、专项检查和示例放在 `references/` 按需读取。
- **校准评审**：区分变更引入的问题与原有问题，依据实际影响分级。证据不足进入待确认项，不通过降低优先级混进 findings。
- **校准溯源**：从消费点反推来源，按操作和时间段解释结果。无需为单行问题凑三条证据、四类来源或固定图表。
- **补全修复闭环**：检查真实契约、用户已有改动，以及异步成功、失败和 `finally` 的状态归属；验证只报告实际执行结果。
- **减少环境假设**：框架版本以依赖和配置为准，MCP 工具经发现后按需使用；没有特定工具也可以完成任务。
- **可持续验证**：每个 skill 配有包含输入、预期行为和禁止行为的评估用例，仓库提供无第三方 Python 依赖的结构校验工具。
- **统一证据术语**：静态事实、条件结论、运行确认三档命名在三个 skill 中保持一致，便于 tracer 的结论直接交给 modifier 复用。
- **版本可追溯**：每个 `SKILL.md` 带语义化 `version`；校验器提供 `--manifest` 生成文件摘要，`--report` 比对评测记录——内容一改、过期的评测记录即校验失败，不会静默冒充当前版本的结论。

## 目录结构

```text
coderSkills/
├── README.md
├── EVALUATION.md                 # 行为评估方法与记录要求
├── reports/                      # 已执行抽样的输入版本、输出与判定
├── 修改web代码/
│   ├── SKILL.md
│   ├── agents/openai.yaml        # Codex 中文显示名称
│   ├── references/change-checks.md
│   └── evals/evals.json
├── 评审web代码/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/review-checks.md
│   └── evals/evals.json
├── 溯源web代码/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/tracing-checks.md
│   └── evals/evals.json
└── scripts/
    ├── show-skill.sh
    ├── find-symbol.sh
    ├── show-lines.sh
    └── validate-skills.py
```

## 安装与任务衔接

将需要的 **整个 skill 目录** 放入宿主配置的技能目录，保留 `SKILL.md`、`agents/` 与 `references/` 的相对路径。`evals/` 用于维护评估，建议一起保留。三个 skill 可以独立安装，不依赖仓库根目录脚本、其他 skill 或特定 MCP。

三个 skill 的目录名、`SKILL.md` 中的 `name` 和 `agents/openai.yaml` 中的 `interface.display_name` 统一使用中文名称：“修改web代码”“评审web代码”“溯源web代码”。可使用 `$修改web代码`、`$评审web代码`、`$溯源web代码` 显式调用。升级安装时移除旧版英文名称目录，再复制中文名称目录；若界面未刷新，重启 Codex 后查看技能列表。

`SKILL.md` 的 YAML frontmatter 提供 `name` 和 `description`；宿主通常用它判断何时加载正文。实际自动发现路径、是否需重新加载及工具权限由宿主决定。引用资料只在相关任务中读取。

- “解释为什么这样”：tracer，只做分析。
- “定位问题并修复”：modifier，连续完成诊断与实施。
- “review 这次变更”：review，只读检查。
- “review 后把确认的问题修掉”：先 review，再 modifier，复用已核实的上下文。

用户改变任务意图时按最新授权衔接；不要求重复确认，也不因另一个 skill 未安装而停止已能完成的工作。

手动取用时，可以打印主流程：

```bash
./scripts/show-skill.sh                       # 列出可用 skill
./scripts/show-skill.sh 评审web代码  # 打印主文件
```

该命令不展开引用文件。粘贴到聊天工具时，按任务补充被引用的相关资料，或让工具可以访问完整 skill 目录。

## 辅助工具

```bash
./scripts/find-symbol.sh 'user.name' src/           # 按字面量、区分大小写搜索
./scripts/find-symbol.sh --regex 'user(Name|Id)' src/
./scripts/find-symbol.sh -- '-deprecated' src/      # 搜索以 - 开头的文本
./scripts/show-lines.sh src/UserList.vue 40 52      # 输出带行号的指定范围
./scripts/show-lines.sh src/UserList.vue 40         # 从第 40 行到末尾
python3 scripts/validate-skills.py                            # 校验整个仓库的 skill
python3 scripts/validate-skills.py 评审web代码       # 校验单个 skill
python3 scripts/validate-skills.py --manifest                 # 输出各文件摘要，供评测记录版本
python3 scripts/validate-skills.py --report reports/xxx.json  # 校验评测报告并比对版本摘要
```

Shell 脚本使用 Bash；`show-skill.sh` 使用 Python 3 校验中文名称；搜索优先使用 `rg`，不可用时回退 `grep`。`find-symbol.sh` 的退出码是：`0` 找到匹配，`1` 没有匹配，`2` 参数或检索错误。与旧版相比，默认搜索改为字面量且不再吞掉错误；需要正则的调用应增加 `--regex`。

结构校验器检查仓库约定的 frontmatter 子集（含 `version` 语义化版本）、名称、正文长度、skill 内相对文件链接及评估数据格式。`--manifest` 以稳定顺序输出各 skill 文件的 SHA-256，供评测报告记录所测版本；`--report` 反过来校验报告，并重新计算摘要——skill 内容一变、报告记录的版本即告失效，需要重跑或显式标注过期。

它不是通用 YAML 解析器，不验证 Markdown 标题锚点，也不能证明模型行为正确。摘要一致只说明报告指向当前内容，不代表评估结论仍然成立。

## 维护与评估

修改后先运行结构校验，再按 [行为评估说明](EVALUATION.md) 检查相关用例。重点看误报、漏报、越界修改、无证据结论和不必要的流程开销。

改动 skill 行为时同步递增其 `version`；若该 skill 有已执行的评测记录，重跑受影响场景并按 `--manifest` 更新摘要。无法重跑时保留原记录并标注过期，不要用新哈希替换旧结论。

用例采用仓库自定义 JSON 格式，可供人工或宿主评估器读取；不依赖某个模型 API。新增或修改用例不等于执行了评测，结构校验通过也不等于行为评估通过。

## 许可

内部使用。
