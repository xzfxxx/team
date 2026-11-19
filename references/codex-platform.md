# Codex CLI 平台调用方法

> 本会话只读一次。**本文件的能力未经实测**，标记「待验证」的条目在确认前不得当作可用。

## 已确认可用

- `codex exec "<prompt>"`：非交互执行一次性任务（headless）。
- 仓库根 `AGENTS.md`：放**指令**（编码约定、角色行为要求、验收口径），会被主 agent 当作上下文读。

## 待验证（不要假设）

- ❌ 没有证据表明 `AGENTS.md` 支持 `[subagent name=...]` 这种**配置式子代理声明**。旧版本文档里写过这个用法，属于**臆测**；如果你的 Codex 版本确实支持，请实测后回来改本文件，否则按下面的降级方案做。
- ❌ 是否有内建并行子代理编排（orchestrator/worker）取决于版本；不确定时按"没有"处理。

## 降级方案（默认走这个）

1. **角色 = 提示词**：把 `roles/<角色>.md` 的 Persona 拼进 `codex exec` 的 prompt，一次一个角色，串行。
2. **并行 = 多进程 + worktree**：
   ```
   git worktree add ../wt-dev1 -b dev1
   cd ../wt-dev1 && codex exec "<开发工程师 persona + 任务>"
   ```
   没有 worktree 就别并行——共享仓库会互相覆盖。
3. **修复轮次**：每次都是新进程，**必须**把上一轮结论、问题清单、改动位置完整附上。
4. **用户确认**：`codex exec` 没有交互式提问通道，需要拍板的地方由主 agent 汇总成清单问用户，再把答案写进下一条 prompt。

## 汇报

- 主 agent 只能拿到 `codex exec` 的 stdout；要求它在输出里用固定三段：结论 / 证据 / 未决项，方便解析。
- 没有 `send_message`、没有续聊、没有 `log()`。
