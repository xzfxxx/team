# dsh-team 平台调用方法（DSH 可选基础设施）

> 仅当你装了 dsh-team 插件（在 DSH web profile）时用本文件；否则回落到 `dsh-platform.md`（subagent/workflow）。
> dsh-team 提供"常驻队友 + 共享任务板 + 邮箱 + 工作区"，本体是传输层，**不含角色库/模板/评审**——那些仍由本 skill（mode）决定。

## 映射：mode 的编排 → dsh-team 工具

| mode 里的动作 | dsh-team 工具 |
|--------------|--------------|
| 派生一个角色队友（开发/质量…） | `team_spawn(name, task, relation, role, persona, model, reasoning_effort)`，persona 用本 skill 的角色模板【Persona】 |
| 共享任务清单（记录各阶段/各任务） | `team_task`（leader 写，建/改/结案；`assignee` 填名字或 id） |
| 派活给某队友 / 交流 | `team_send(to=名字或id或leader, message)`——消息成为对方下一个 turn，投递是 leader 权威 |
| 队友主动汇报 | harness 内置 `report`（走 `subagent-report` 源，被折叠进 leader 日志） |
| 改任务状态 / 派发修复 | `team_task` 更新 + `team_send` 给原开发队友 |
| 看全局进度 | `team_list`（花名册 running/idle/ready、任务、最近邮箱流量） |
| 共享黑板/便笺 | `team_note`（`private:true` 私有便笺）/ `team_board`（读索引或全文） |
| 解雇/解散 | `team_dismiss`（无参=整队解散，transcript 仍可读） |

## 常驻队友的关键

- 一个角色队友**spawn 一次，跨迭代复用**：修复/复审用 `team_send` 发给**同一个**队友，不要为新轮次再 spawn——它保留自己写过的上下文，第二次修更准。
- 队友可独立设 `model` / `reasoning_effort`（各队友不同模型）。
- 约束：`maxTeammates`(默认8)、队友间对话防循环(`maxChainHops`=4, `maxChainRoundTrips`=2)；发给 leader 从不拒绝。

## 使用方式

- 流程、角色、评审规则照常走本 skill；**只把"子代理调用方式"换成 dsh-team 的 team 工具**。
- 队友汇报用 `report`，leader 用 `team_list` 记账；需要队友自己留的东西走共享工作区（`team_note`/`team_board`）。
