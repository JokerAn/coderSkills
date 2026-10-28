# coderSkills

面向 **Vue 2 / Vue 3 / React Hooks** 的前端 AI 技能集，采用 Agent Skills 目录格式。四个 skill 分别负责修改、评审、溯源和可视化，也能按用户目标衔接执行。

| Skill（中文显示名称） | 交付结果 | 典型请求 |
| --- | --- | --- |
| [web-code-modifier](web-code-modifier/SKILL.md) | 完成修改，解释原因，报告实际验证结果 | “帮我修这个”“改了没生效”“改 A 影响 B” |
| [web-code-reviewer](web-code-reviewer/SKILL.md) | 按严重程度排序、有触发条件与证据的问题清单 | “review 一下”“这段能不能合并”“找回归” |
| [web-code-tracer](web-code-tracer/SKILL.md) | 解释来源、路径、条件与覆盖关系，默认只读 | “这个值从哪来”“为什么不是接口”“怎么实现的” |
| [mermaid-diagram](mermaid-diagram/SKILL.md) | 按阅读目标交付清晰、可核查的 Mermaid 图 | “画流程图”“画调用链”“把这段代码画清楚” |

共同原则：**按风险选择深度，关键结论能核查，静态推导与运行观察分开报告**。简单问题直接回答或修改；缺少上下文时，先完成能独立确认的部分。

## 本次升级

- **减轻主流程**：常用指令放在 `SKILL.md`，框架陷阱、专项检查和示例放在 `references/` 按需读取。
- **校准评审**：区分变更引入的问题与原有问题，依据实际影响分级。证据不足进入待确认项，不通过降低优先级混进 findings。
- **校准溯源**：从消费点反推来源，按操作和时间段解释结果。无需为单行问题凑三条证据、四类来源或固定图表。
- **收敛复杂链路**：跨组件或单页多写入时，先辨认状态归属、写入渠道、失效边界和观察时机；`v-model`、缓存、定时器与请求按实际交错追踪，简单问题不套复杂流程。
- **改善读图与评审**：流程图以读者问题和真实落点组织层级；评审核对保护覆盖的写入入口与失效边界，避免把事件、数据和状态归属混成一条线。
- **补全修复闭环**：检查真实契约、用户已有改动，以及异步成功、失败和 `finally` 的状态归属；验证只报告实际执行结果。
- **抑制防御性膨胀**：明确“默认不写什么”——卸载判断、请求序号/取消、转发变量、全量兜底等，只在用户已报告该症状、需求要求或既有机制必须随之调整时才写。
- **顺带发现按级处理**：P0/P1 当次修完；P2（真实但不在目标内、正常使用不一定触发）不写进代码，交付时列一条；P3 默认不提。跨文件改动先决定改共享层还是调用点，不在共享函数里加模式开关。
- **减少环境假设**：框架版本以依赖和配置为准，MCP 工具经发现后按需使用；没有特定工具也可以完成任务。
- **可持续验证**：每个 skill 配有包含输入、预期行为和禁止行为的评估用例，仓库提供无第三方 Python 依赖的结构校验工具。
- **统一证据术语**：静态事实、条件结论、运行确认三档命名在三个前端 skill 中保持一致，便于 tracer 的结论直接交给 modifier 复用。
- **版本可追溯**：每个 `SKILL.md` 带语义化 `version`；校验器提供 `--manifest` 生成文件摘要，`--report` 比对评测记录——内容一改、过期的评测记录即校验失败，不会静默冒充当前版本的结论。

## 目录结构

```text
coderSkills/
├── README.md
├── EVALUATION.md                 # 行为评估方法与记录要求
├── reports/                      # 已执行抽样的输入版本、输出与判定
├── web-code-modifier/
│   ├── SKILL.md
│   ├── agents/openai.yaml        # Codex 中文显示名称
│   ├── references/change-checks.md
│   └── evals/evals.json
├── web-code-reviewer/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/review-checks.md
│   └── evals/evals.json
├── web-code-tracer/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/tracing-checks.md
│   └── evals/evals.json
├── mermaid-diagram/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   └── evals/evals.json
└── scripts/
    ├── show-skill.sh
    ├── find-symbol.sh
    ├── show-lines.sh
    ├── install-dsh-skills.py
    └── validate-skills.py
```

## 安装与任务衔接

将需要的 **整个 skill 目录** 放入宿主配置的技能目录，保留 `SKILL.md`、`agents/` 与 `references/` 的相对路径。`evals/` 用于维护评估，建议一起保留。四个 skill 可以独立安装，不依赖仓库根目录脚本、其他 skill 或特定 MCP。

四个 skill 的目录名、`SKILL.md` 中的 `name` 和 `agents/openai.yaml` 中的 `interface.display_name` 统一使用中文名称：“web-code-modifier”“web-code-reviewer”“web-code-tracer”“mermaid-diagram”。可使用 `$web-code-modifier`、`$web-code-reviewer`、`$web-code-tracer`、`$mermaid-diagram` 显式调用。升级安装时移除旧版英文名称目录，再复制中文名称目录；若界面未刷新，重启 Codex 后查看技能列表。

`SKILL.md` 的 YAML frontmatter 提供 `name` 和 `description`；宿主通常用它判断何时加载正文。实际自动发现路径、是否需重新加载及工具权限由宿主决定。引用资料只在相关任务中读取。

- “解释为什么这样”：tracer，只做分析。
- “定位问题并修复”：modifier，连续完成诊断与实施。
- “review 这次变更”：review，只读检查。
- “review 后把确认的问题修掉”：先 review，再 modifier，复用已核实的上下文。

用户改变任务意图时按最新授权衔接；不要求重复确认，也不因另一个 skill 未安装而停止已能完成的工作。

### DeepSeek Harness

DeepSeek Harness 由 `@deepseek-ai/dsh-skill-filesystem` 提供方发现本地 skill，按优先级扫描 `<projectRoot>/.dsh/skills`、`<projectRoot>/.agents/skills`、`Config.customSkillDirs`、`$DSH_HOME/skills`（默认 `~/.dsh/skills`）与 `~/.agents/skills`，只识别根目录下一层的 `<name>/SKILL.md`。

**Harness 要求 frontmatter 的 `name` 匹配 `^[a-z0-9]+(?:-[a-z0-9]+)*$`**，中文名称会被连同警告静默丢弃。因此安装时用脚本生成一份只改写 `name` 的 `SKILL.md`，其余内容（正文、`agents/`、`references/`、`evals/`）保持原样指向仓库：

```bash
python3 scripts/install-dsh-skills.py              # 安装到 ~/.dsh/skills（子目录符号链接回仓库）
python3 scripts/install-dsh-skills.py --copy       # 改为自包含副本
python3 scripts/install-dsh-skills.py --dry-run    # 只打印将要执行的操作
python3 scripts/install-dsh-skills.py --list       # 查看仓库中文名与 Harness 名称的对应关系
python3 scripts/install-dsh-skills.py --uninstall  # 移除脚本安装的 skill
```

| 仓库目录 | DeepSeek Harness 名称 |
| --- | --- |
| web-code-modifier | `web-code-modifier` |
| web-code-reviewer | `web-code-reviewer` |
| web-code-tracer | `web-code-tracer` |
| mermaid-diagram | `mermaid-diagram` |

名称改写只影响 Harness 侧的调用名（`/web-code-modifier`）；`description` 仍为中文，模型据此判断何时加载。Harness 会监视 skill 根目录，新增、改名或删除在最迟下一个模型步骤生效，无需重启。默认链接模式让正文与引用资料的编辑立即生效；`SKILL.md` 的 `name` 由脚本生成，仓库里改了名称或描述后重跑一次即可。

手动取用时，可以打印主流程：

```bash
./scripts/show-skill.sh                       # 列出可用 skill
./scripts/show-skill.sh web-code-reviewer  # 打印主文件
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
python3 scripts/validate-skills.py web-code-reviewer       # 校验单个 skill
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
