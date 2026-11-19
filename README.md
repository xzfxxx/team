# team-mode — 多平台团队开发模式（v2）

> 一个目录形态的 Agent Skill：主 agent 当调度，按角色模板派独立子代理做编码/测试/验收；按任务类型选工作流模板；带复杂度与成本门、独立验收、预算与退出阀。
> 支持 DSH、Claude Code、Codex/Gemini CLI、Cursor、Roo Code；角色与流程跨平台复用，只有"派活方式"按平台切换。

**v2 的重点不是加功能，而是把"说得漂亮但做不到"的部分删掉或改成能做的。**

---

## 怎么用

### DSH
```
/团队            # 手动触发
或直接提一个复杂需求   # 复杂度门会建议，但不强行推销
```

### Claude Code
```bash
mkdir -p ~/.claude/skills/team-mode
cp -r roles templates references prompts scripts SKILL.md ~/.claude/skills/team-mode/
```
角色与流程复用；调用方式按 `references/claude-platform.md`（子代理一次性，不能续聊）。

### Codex / Gemini CLI
没有可靠的配置式子代理声明，**默认走降级方案**（角色当提示词 + 串行 / worktree 并行），见对应 `references/*-platform.md`。

---

## 目录

```
team-mode/
├── SKILL.md                     # 主文件：加载边界、门槛、平台检测、角色/模板索引、执行协议、验收、预算
├── README.md
├── roles/                       # 8 个角色人格（跨平台复用）
│   ├── 产品经理.md  架构师.md  开发工程师.md  测试工程师.md
│   ├── 数据库工程师.md  前端工程师.md  质量工程师.md  文档工程师.md
├── templates/                   # 7 个工作流模板（决定角色与步骤）
│   ├── standard-dev.md          # 标准功能开发
│   ├── data-mapper.md           # HANA + gen-mapper（只读，禁改表）
│   ├── mysql-mapper.md          # MySQL 建表 + 手写映射（与 data-mapper 互斥）
│   ├── bugfix-refactor.md       # 修 bug / 重构（行为不变）
│   ├── frontend-page.md         # 页面 / 组件 / 交互
│   ├── research-query.md        # 只查不改 / 调研
│   └── quick-task.md            # 单点小改（主 agent 直接改的例外）
├── prompts/                     # 盲审的两个隔离模板（互相看不到对方结论）
│   ├── blind-qa-a.md            # QA-A：需求覆盖 + 变更安全
│   └── blind-qa-b.md            # QA-B：健壮性 + 安全 + 数据/性能
├── scripts/
│   ├── check-skill.py           # 自检：结构 / 引用 / 登记 / 禁用词 / 表格
│   └── test-check-skill.sh      # 自检脚本的回归测试（16 个故障注入用例）
└── references/
    ├── orchestration.md         # 阶段细则、进度表、汇报格式、补充逻辑、哨兵、DoD、报告模板
    ├── dsh-platform.md          # DSH：subagent / workflow / 续聊 / 并发上限
    ├── dsh-team-platform.md     # DSH + agent-team 插件（实验）：九个真实工具
    ├── claude-platform.md       # Claude Code：一次性子代理 + worktree
    ├── codex-platform.md        # Codex CLI（能力标注待验证）
    ├── gemini-platform.md       # Gemini CLI（能力标注待验证）
    ├── cursor-platform.md       # Cursor：GUI 派发，半自动
    └── roo-platform.md          # Roo Code：modes，半自动
```

加载策略：**SKILL.md 一次 + 一个平台文件一次**；角色/模板/orchestration/盲审模板 **用到才读**。子代理只拿角色 Persona + 任务，不拿 SKILL.md 全文。

## 改完先自检

```bash
python3 scripts/check-skill.py          # 全量：错误 + 警告
python3 scripts/check-skill.py --quiet  # 只看错误
bash    scripts/test-check-skill.sh     # 自检脚本自身的回归测试（16 个用例）
```

**错误级（退出码 1）**，共 6 类：

1. **frontmatter**：缺失、缺 `name` 或 `description`
2. **引用**：文中提到的 `roles/…`、`templates/…`、`references/…`、`prompts/…`、`scripts/…` 不存在；含大小写不符、`..` 穿越、指向仓库外的符号链接
3. **登记**：`roles/`、`templates/`、`references/`、`prompts/` 缺失或为空；文件没在 SKILL.md 登记；SKILL 表格里写了不存在的文件
4. **禁用词**：`toDoWrite`、`team_spawn`、`mimo-v2` 等已确认不存在的能力名（否定语境除外），以及未加否定的 `log()`
5. **Markdown**：表格列数不一致、代码围栏未闭合
6. **结构**：角色缺【汇报方式】/`send_message` 降级说明；模板缺「适用 / 步骤序列 / DoD」；SKILL 缺关键小节

**警告级**（不影响退出码）：`description` 偏短、文件过长、盲审 prompt 缺占位符。
**提示**（不影响结果）：`name` 与目录名不一致——仓库克隆或改名安装时正常。
**退出码 2**：参数错误（只接受 `--quiet`）。

改动这个 skill 后跑一遍；接 CI / pre-commit 直接调用 `--quiet` 即可。

---

## 关键机制（细节在 SKILL.md）

| 机制 | 一句话 |
|------|--------|
| 复杂度+成本门 | 6 条可验证判据，≥3 条才建议开团队；团队约 10–20× token，先算账 |
| 平台检测 | 顺序固定，agent-team 优先于裸 DSH；标「待验证」的能力不许假设存在 |
| 常驻 vs 一次性 | 多轮修复/追问 → `subagent`（可续）；一次性并行 → `workflow`（不可续）；外部 provider 每次都新开 |
| 写域表 | 并行前必须列"谁能写哪些路径"；共享工作区下并行改同一文件必冲突 |
| 分层验收 | A 通用 / B 后端数据 / C 前端 / D 变更安全，按栈取用，不再全局套 MyBatis 清单 |
| 证据要求 | 每条发现要 `path:line` + 验证方式；无法验证进「待核实」，禁止编造测试结果 |
| 通过线 | 1 条 🔴 即不通过；🟡 可带条件通过 |
| 修复循环 | 默认 3 轮、上限 5 轮；发给同一个开发子代理 |
| 盲审交叉评审 | 只给高风险任务；QA-B 不看 QA-A 的结论；冲突按可复现性裁决，不按自报置信度 |
| 预算与退出阀 | 角色 ≤7、并发 ≤8、轮次 ≤5、墙钟 90 分钟；超限三选一，用户不答则由主 agent 收尾并声明退出 |
| 结构化交接 | 子代理最终回复自包含；主 agent 对结论近原文转述，只对内部协调做浓缩 |

---

## 与 v1 的差异（修了什么）

**硬矛盾（P0）**

1. 平台检测顺序：agent-team 现在排在 DSH 前面，不再被第一分支短路。
2. 常驻队友与 workflow 互斥：明确"要续聊就别用 workflow"，并给出分两段的用法。
3. 数据库工程师的写权限：从"禁止 write"改为"可写 Entity/Mapper/XML，DDL 需授权"，`mysql-mapper` 不再自相矛盾。
4. 主 agent 边界：保留"不写业务代码/不出验收结论"，把 `quick-task`、`research-query` 明确列为**必须声明的例外**。

**事实错误（P0）**

5. 模型表：删掉不存在的 `mimo-v2.5` / `mimo-v2.5-pro`；改为"默认继承父级，仅在会话允许时按白名单指定"。
6. dsh-team 工具名：`team_spawn/team_send/team_list/team_note/team_board/team_dismiss/team_task` 全部不存在，改为真实的九个工具（`spawn_teammate`、`send_message`、`list_agents`、`wait_agent`、`interrupt_agent`、`team_task_*`），并补上限与限制。
7. Codex/Gemini 的 `AGENTS.md [subagent]` 配置：标注「待验证」，不再当既成事实；补降级方案。
8. `toDoWrite` / 子代理 `log()`：改为 `todo_write` / `send_message`，`log()` 只在 workflow 脚本内可用。
9. 人数表：改为"角色实例"口径，并受 DSH `maxActiveSubagents=8` 约束。

**设计缺陷（P1）**

10. 验收从"11 维全局套用"改为分层清单（A/B/C/D），加证据要求与 🔴/🟡/🟢 通过线。
11. 交叉评审从"按置信度加权"改为盲审 + 可复现性裁决 + 重合率触发第三审。
12. 轮数从默认 10 改为默认 3 / 上限 5，并加墙钟、角色数、重开次数预算与退出阀。
13. "直通给用户"不可实现（子代理没有用户通道）→ 改为结构化交接。
14. 模板登记补上 `mysql-mapper`，并把 HANA/MySQL 的路由规则提到选模板那一层。
15. Phase 编号连续（1–7），模板内改用"步骤"，避免两套编号混淆。

**维护性（P2）**

16. SKILL.md 从 222 行压到 169 行（约 -24%），运行细则下沉到 `references/orchestration.md` 按需加载。
17. 平台文件去掉互相抄写的重复内容；不确定的能力统一标注「待验证」。
18. 加 DoD、结束检查清单、`.team-mode/` 共享状态约定、报告里"下次值不值得开团队"的判断。
19. 盲审做成**隔离模板**：`prompts/blind-qa-a.md` / `prompts/blind-qa-b.md`，B 的模板里没有放 A 清单的占位符；输入里若真出现对方结论，B 必须打 `LEAK:` 行，该轮盲审作废。
20. 加 `scripts/check-skill.py`：6 类错误 + 4 类警告的结构检查，已用它跑出并修掉 6 处不一致（含漏登记的 prompts）。
21. 加 `scripts/test-check-skill.sh`：16 个故障注入用例，保证"自检不会永远通过"；两次盲审冒烟测试实际抓到自检脚本的 5 个缺陷（删除 `templates/` 仍通过、`--quiet` 不静默、BOM 误报、安装命令漏拷、文档口径不符），均已修复并补了回归用例。

---

## 已知限制（别当成 bug）

- **`maxDepth=1`**：DSH 子代理不能再派子代理，团队只能是扁平结构，不要设计三层。
- **无 token 精确计量**：预算是量级判断 + 计数（角色/轮次/墙钟），不是精确账单。
- **角色工具边界是软约束**：persona 说"禁止 write"不等于技术上隔离；真正的隔离靠平台/插件。
- **agent-team 是实验特性**：无稳定性保证，工具名可能再变；变了解析前先 `list_agents` 确认。
- **GUI 平台（Cursor/Roo）**：agent 无法自动派发，只能出"派发卡"由用户点，属于半自动。
- **自检只覆盖结构与元数据**：`check-skill.py` 不验证规则内容是否合理、也不验证 agent 是否照做；行为只能靠 `test-check-skill.sh`（针对脚本）和真实任务（尚未做）。

## 不适用

- 单行常量修改、纯聊天、已经明确是单点的紧急小改（复杂度门会降级）。
- 需要真实隔离的对抗性安全审计（本 skill 只做代码评审级检查）。
