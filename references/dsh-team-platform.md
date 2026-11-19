# DSH + agent-team 平台调用方法（实验特性）

> 仅当会话里同时出现 `spawn_teammate` 与 `team_task_create` 时用本文件；否则回落 `dsh-platform.md`。
> 这是 `@deepseek-ai/dsh-experimental-agent-team` + `@deepseek-ai/dsh-experimental-tool-agent-team`，**实验特性、无稳定性保证**。
> 它只提供"常驻队友 + 邮箱 + 共享任务板"这层基础设施，**不含角色库 / 模板 / 评审规则**——那些仍由本 skill 决定。

## 前置条件

- 组合里必须有持久会话存储（如 `dsh-session-persistence-jsonl`），否则队友重启后无法冷恢复。
- 所有成员**共享同一个工作目录**，没有独立 worktree——写域规则（SKILL §5.3）照样适用，且更关键。
- 它与旧子代理控制工具**同名冲突**（都叫 `send_message`/`list_agents`/`interrupt_agent`），组合里只能启用一套。

## 九个工具的真实名字

| 能力 | 工具 | 说明 |
|------|------|------|
| 造队友 | `spawn_teammate(name, description, task)` | **只有 Lead 能调**；名字永久占用（失败也不复用）；默认 fresh，也可 fork（继承 Lead 已完成轮次） |
| 派活/追问 | `send_message(target, message)` | 任意成员可发给任意成员；对运行中成员在 step 边界插入，对 inactive 成员会冷恢复；返回 `{sent:true}` 只代表收件成功 |
| 看名册 | `list_agents` | 返回 target、角色（lead/teammate）、状态：`running` / `inactive` / `provisioning` / `failed` |
| 等进展 | `wait_agent` | 等下一次团队变化（状态/消息/任务）；没有人在跑时立刻返回 `noProgress` |
| 打断 | `interrupt_agent(target)` | **只有 Lead 能调**；停当前 turn，不清空排队消息 |
| 任务板 | `team_task_create` / `team_task_list` / `team_task_get` / `team_task_update` | 共享 DAG：可设依赖、可声明将触碰的文件；认领/完成/释放/重开；**revision 不匹配会被拒绝** |

**没有** `team_spawn` / `team_send` / `team_list` / `team_note` / `team_board` / `team_dismiss`——这些名字不存在，别调用。也没有"解散"的模型工具：队友干完进入 `inactive` 即停，名册随会话生命周期回收。

## 默认上限（部署可改）

| 项 | 默认 |
|----|------|
| `maxMembers` | 16 |
| `maxTasks` | 256 |
| `maxMessageBytes` | 64 KiB |

仍然建议按 SKILL §8 控制：**角色实例 ≤7、并发 ≤8**。上限是硬墙，不是目标。

## 怎么映射到本 skill

| 编排动作 | 用哪个 |
|---------|--------|
| 按角色建常驻队友 | `spawn_teammate(name="dev-order", description="开发工程师", task=<persona+任务+写域+产物>)` |
| 修复轮次 | `send_message(target, 问题清单)` —— 发给**原来那个队友**，不要重新 spawn |
| 进度看板 | `team_task_create` 建任务（带依赖/文件提示）→ 队友认领 → `team_task_list` 看全局 |
| 等某个队友 | `wait_agent`，拿到变化后**重新 `list_agents` 读状态**（wait 只告诉你"有变化"） |
| 队友跑偏/卡死 | `interrupt_agent`，对齐目标后 `send_message` 重派 |
| 验收 | spawn 一个隔离的 QA 队友（fresh，不 fork），不让它看开发队友的对话 |

## 队友的汇报

- 队友没有对用户说话的通道，**必须用 `send_message` 回报 Lead**；只写自己的最终文本不保证 Lead 能看到。
- 让它按"结论 / 证据 / 未决项"三段报，正文 ≤200 字（消息有 64 KiB 上限，但长文会挤爆 Lead 上下文）。
- 不要指望 `report` 之类的工具存在——本插件没有提供。

## 已知限制

- 没有自动释放任务归属：队友死了任务仍挂在它名下，要 Lead 手动 `team_task_update`。
- 消息不重试、不跨重启补投；`send_message` 成功 ≠ 对方处理成功。
- 文件提示只是"重叠警告"，**不会阻塞**两个任务改同一文件——写域仍要靠人（主 agent）把关。
