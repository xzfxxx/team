# team-mode — 多平台便携的团队开发模式

> 一个**文件夹、多文件**的 Agent Skill。让主 agent 作为**项目经理**，从**角色模板库**派生开发/测试/架构/质量等角色独立协作，把简单任务裁成单人、复杂任务编成团队。
> 同时支持 **DSH、Claude Code、Codex、Gemini CLI、Cursor、Roo Code** 多平台，角色与流程跨平台复用，仅"子代理调用方式"按平台切换。

---

## 为什么用它

- **主 agent 只调度**，不自己写码、不自己验收；编码和验收都由独立子 agent 执行，降低"自己写自己审"的盲区。
- **按任务复杂度自适应**：简单任务主动降级/拒绝（不硬开团队）；复杂任务即使没显式说 `/团队` 也被建议启用。
- **角色库可扩展**：8 个内置角色 + 随时造**临时角色**，用完后可沉淀为永久角色。
- **流程模板驱动**：按任务类型选/生成工作流（标准开发 / 数据+MyBatis / 修bug / 前端 / 调研 / 紧急），覆盖不了就由架构师**新规划一条工作流**。
- **评审正确率**：质量工程师 11 维验收 + 高风险任务**交叉评审**（两个质量师互相挑错）。
- **常驻队友**：每个角色队友 spawn 一次、跨轮次复用，保留上下文，修复迭代更准。

---

## 目录结构

```
team-mode/
  ├── SKILL.md                     # 主编排：复杂度门 + 平台检测 + 角色库 + 模板库 + 通用底座 + 流程编排
  ├── README.md                    # 本文件
  ├── roles/                       # 角色人格模板（跨平台复用）
  │     ├── 产品经理.md
  │     ├── 架构师.md
  │     ├── 开发工程师.md
  │     ├── 测试工程师.md
  │     ├── 数据库工程师.md
  │     ├── 前端工程师.md
  │     ├── 质量工程师.md
  │     └── 文档工程师.md
  ├── templates/                   # 工作流模板（决定用哪些角色、走什么阶段）
  │     ├── standard-dev.md        #  标准功能开发
  │     ├── data-mapper.md         #  数据 / MySQL+MyBatis 生成
  │     ├── bugfix-refactor.md     #  修 bug / 重构
  │     ├── frontend-page.md       #  前端页面 / 组件 / 交互
  │     ├── research-query.md      #  纯查询 / 分析 / 调研
  │     └── quick-task.md          #  紧急小任务
  └── references/                  # 各平台的"子代理调用方法"（首次进入时才加载一次）
        ├── dsh-platform.md        #  DSH（subagent / workflow）
        ├── dsh-team-platform.md   #  DSH + dsh-team 插件（可选，常驻队友/共享看板/邮箱）
        ├── claude-platform.md     #  Claude Code（Agent + worktree）
        ├── codex-platform.md      #  Codex（AGENTS.md subagent + orchestrator）
        ├── gemini-platform.md     #  Gemini CLI（AGENTS.md [subagent]）
        ├── cursor-platform.md     #  Cursor（GUI 后台 agent）
        └── roo-platform.md        #  Roo Code（modes + 异步 subagent）
```

- **角色文件（roles/）** 是纯 prompt 人格模板，所有平台复用。
- **模板文件（templates/）** 定义"用哪些角色、按什么阶段走"，由架构师在 Phase 2 读取选择。
- **平台文件（references/）** 是一次性的"调用方法说明"，首次检测到平台时读一次（**本会话只加载一次**）。

---

## 怎么用

### DSH
```text
在一个挂载了本 skill 的会话里说：
  /团队            # 手动触发
或直接贴一个复杂需求          # 复杂度门会自动判断并建议 / 团队 / 降级
```

### Claude Code
```bash
mkdir -p ~/.claude/skills/team-mode
cp -r roles templates references SKILL.md ~/.claude/skills/team-mode/
# Claude 识别为 directory skill，触发 /团队；平台自动检测到 Claude Code
```

### Codex / Gemini CLI
把角色 persona 写进项目根 `AGENTS.md` 的 subagent 段（见 `references/codex-platform.md`），主 agent 按名字派活。

> **移植注意**：`SKILL.md` 里不必手写资源路径——DSH 渲染时会按 skill 所在目录**自动生成**资源提示（`Base directory for this skill`），所以证书里不留任何机器相关路径，**直接整包搬运即可**（Claude Code 也不依赖它）。

---

## 工作流（六个 Phase）

```
复杂度门 → 需求澄清 → 流程规划(选/生成模板) → 执行(角色) → 验收 → 修复循环 → 报告+沉淀
```

1. **复杂度门**：先判值不值得开团队；简单降级 `quick-task`，复杂进团队。
2. **平台检测**（本会话只加载一次）：检测运行环境，读一次对应 `references/<platform>.md`。
3. **角色模板库**：需要角色 → 读 `roles/<角色>.md` → 注入【Persona】。
4. **流程规划**：架构师选/生成**工作流模板**，给用户确认。
5. **执行**：主 agent 只调度；每个角色独立子代理干活；高风险任务**交叉评审**。
6. **修复循环 + 最终报告**：修复复用**同一队友**；报告由主 agent 总结，结论沉淀到记忆。

---

## 关键机制速览

| 机制 | 说明 |
|------|------|
| **复杂度门** | 简单→拒绝/降级；复杂→主动建议 /团队。用 `ask_user_question` 让用户拍板 |
| **平台 load-once** | 检测结果写会话标记 `[团队模式] 平台 = X`，本会话后续复用，不重复检测/加载说明 |
| **临时角色** | 库外角色临时造（写 persona 注入，不建文件）；完成后问是否永久加入 roles/ |
| **新规划工作流** | 模板不覆盖则架构师现编阶段序列（角色+任务），只须含「验收」+「报告」 |
| **交叉评审** | 高风险任务第二个质量师独立挑错，两份清单合并去重 |
| **常驻队友** | 队友 spawn 一次、跨修复轮次复用（`send_message`/dsh-team `team_send`） |
| **知识反馈** | 若"新规划"场景重复出现，架构师沉淀成新模板写入 templates/ |

---

## 配置与触发

- 触发词：`/团队`、`/team`、`/dev`；但**复杂度门**会主动建议/降级，不只靠触发词。
- 验收默认 **10 轮**，用完询问是否 +10；用户拒绝才标记失败。
- 默认模型选择（DSH）：简单 CRUD `mimo-v2.5` / 复杂业务 `mimo-v2.5-pro` / 架构级 `deepseek-v4-pro`；其他平台用其默认。

---

## 限制与注意事项

- **`gen-mapper` 工具是 HANA 专属**：对 MySQL 等其它数据库，数据库工程师改用 `SHOW CREATE TABLE` / `DESCRIBE` / `INFORMATION_SCHEMA` 读元数据，不依赖该工具。
- **`dsh-team` 是可选插件（DSH-only）**：给常驻队友加共享看板/邮箱/协作室 UI；不装则回落到 DSH 原生 `subagent`（continuable，同样支持常驻复用）。安装需 web profile 插件挂载，且其构建目标为 `@deepseek-ai/dsh@0.1.1-rc.2`。
- **`toolFilter` 是预设级硬限制**：角色主要靠 persona + 工具导向约束，无法在单次调用时切换工具白名单。
- **角色模板里的"禁止"是软约束**：靠 personas 提示，不是强隔离。
- **跨平台差异**：Codex/Gemini 是配置式子代理（AGENTS.md），不是运行时 spawn；Cursor/Roo 是 GUI 内 agent，少代码级自动编排。

---

## 适用场景 vs 不适用

- ✅ 多模块、跨角色、高风险、需独立验收、改数据层的后端/全栈任务。
- ❌ 单行常量修改、纯聊天、已明确是单点的紧急小改（这些会被复杂度门降级）。
