# DSH 平台调用方法

> 本会话只读一次。只写"怎么派活、怎么回收"，角色与流程见 `SKILL.md`。

## 可用原语

| 原语 | 用途 | 关键约束 |
|------|------|---------|
| `subagent(description, prompt, cwd?, run_in_background?)` | 派一个子代理；立即返回子代理 id | 本地 spawn 子代理有**持久会话**，可用 `send_message` 续聊 |
| `subagent_fork(description, prompt, cwd?)` | 派一个"继承本会话已完成轮次"的子代理 | 适合需要上下文的复审/续作；同样可续 |
| `send_message(agent_id, message)` | 给已有子代理追加任务 / 修复清单 | 运行中在下一个 step 边界收到；空闲时开启新一轮 |
| `list_agents(scope)` | 看子代理状态（children / descendants） | 只返回 id、标签、状态，不返回内容 |
| `interrupt_agent(agent_id)` | 让子代理停止当前工作 | 不会删除它；之后仍可 `send_message` |
| `workflow(meta, script, args?)` | 脚本化扇出 | **前台阻塞到全部结束**；子代理**一次性**，不可续 |
| `job_output` / `job_kill` | 回收 / 终止后台任务 | 只对后台 job，不是子代理本身 |
| `todo_write` | 维护主 agent 的任务清单 | 名字是 `todo_write`，不是 `toDoWrite` |
| `ask_user_question` | 让用户拍板 | 只在真要决策时用，别为确认而确认 |

`log()` 是 **workflow 脚本内**的宿主函数，**子代理没有这个工具**。子代理要报进度就用 `send_message` 给主 agent，或在最终回复里写清楚。

## 单任务

```
subagent(
  description: "开发工程师：订单查询分页",
  prompt: "<开发工程师 persona>\n\n任务：……\n产物：……\n写域：src/main/java/.../order/**\n汇报：结论+证据+未决项",
  run_in_background: false
)
```

- `run_in_background: true` 会立刻拿到 id，完成时收到通知；适合并行多路。
- 修复轮次：`send_message(agent_id, "问题清单……")`，**不要**新开子代理重述全部背景。

## 并行

```javascript
// workflow 脚本内（这里的 agent 是一次性的）
phase('开发')
const results = await parallel(TASKS.map(t => () =>
  agent(PROMPT(t), { label: `dev:${t.name}`, phase: '开发' })
))
return results
```

- `parallel` 是**屏障**：等全部完成才返回；`pipeline` 无屏障，按条目独立走多阶段。
- `agent()` 子代理失败返回 `null`，脚本自己决定怎么办；但 **hook 用错**（参数错、选项未知、超限）会直接杀掉整个脚本。
- provider / 并发上限 / 结果截断是**部署配置**，不是单次调用参数；`provider`/`model` 覆盖仅在会话允许时生效。

## 模型选择

- 默认**继承父级**。
- 仅当会话开启"子代理模型选择"时，才可传 `provider` + `model`（必须同时给，且路由在白名单内），可选 `reasoning_effort`。
- 没开启时硬写模型名会报错或被忽略；**不要编造模型 id**。

## 隔离与并发（重要）

- 普通子代理**共享同一工作区**，没有 worktree。两个子代理同时改同一文件会互相覆盖。
- 只有装了 `dsh-experimental-tool-worktree` 才有隔离工作区；没有就按写域串行，或拆文件。
- 子代理默认 `maxDepth=1`：**它不能再派子代理**，团队是扁平结构（主 agent + 若干角色）。
- 并发上限 `maxActiveSubagents` 默认 8；超了报 `ACTIVATION_LIMIT_REACHED`，不会排队。

## 进度与回收

- 主 agent 用 `todo_write` 维护自己的清单，用 `list_agents` 看谁在跑。
- 子代理返回的是**最终文本**；中间消息不回流（workflow 更看不到中间过程）。
- 需要"边跑边看"就别用 workflow，用 `subagent(run_in_background: true)` + 完成通知。
