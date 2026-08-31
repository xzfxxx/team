# Claude Code 平台调用方法

> 本文件是「平台检测 + 调用说明」的一部分，**只在本会话第一次进入团队模式时加载一次**。之后沿用会话标记，不再读取。
> 仅包含 Claude 与 DSH 不同的"子代理调用方式"，角色人格模板两个平台完全复用。

## Claude Code 子代理调用

### 单任务
```
Agent(
  description: "开发工程师：实现用户管理模块",
  prompt: "<角色 persona> + 具体任务描述",
  isolation: "worktree"
)
```

### 多任务并行（workflow，推荐）
```javascript
export const meta = {
  name: 'dev-phase',
  description: '开发工程师执行代码实现',
  phases: [ { title: '开发', detail: '代码实现 + 单元测试' } ]
}

phase('开发')
const devResults = await parallel(TASKS.map(task => () =>
  agent(`<角色 persona>\n实现以下功能...`, {
    label: `dev:${task.name}`,
    phase: '开发',
    isolation: 'worktree'
  })
))
return devResults
```

### 验收（workflow）
```javascript
export const meta = {
  name: 'verify-phase',
  description: '质量工程师独立验收',
  phases: [ { title: '验收', detail: '代码质量检查' } ]
}

phase('验收')
const verifyResults = await parallel(TASKS.map(task => () =>
  agent(`<质量工程师 persona>\n检查以下改动...`, {
    label: `verify:${task.name}`,
    phase: '验收',
    isolation: 'worktree'
  })
))
return verifyResults
```

### 询问用户轮数 / 澄清（Claude 的 AskUserQuestion）
```
AskUserQuestion(question: "验收已用完全部轮数，是否再增加10轮？")
```

## 注意
- `isolation: "worktree"` 让每个子代理在独立工作区，避免互相污染。
- 子代理用 toDoWrite 维护进度，主 agent 用 `log()` 汇报状态。
- 能并行就并行（worktree 隔离 + parallel），主 agent 只做调度。
