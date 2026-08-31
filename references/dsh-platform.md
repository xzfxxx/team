# DSH 平台调用方法

> 本文件是「平台检测 + 调用说明」的一部分，**只在本会话第一次进入团队模式时加载一次**。之后沿用会话标记，不再读取。
> 仅包含 DSH 与 Claude 不同的"子代理调用方式"，角色人格模板两个平台完全复用。

## DSH 子代理调用

### 单任务
```
subagent(
  description: "开发工程师：实现用户管理模块",
  prompt: "<角色 persona> + 具体任务描述",
  run_in_background: false
)
```

### 多任务并行（workflow，推荐）
```javascript
phase('开发')
const devResults = await parallel(TASKS.map(task => () =>
  agent(`<角色 persona>\n实现以下功能...`, {
    label: `dev:${task.name}`,
    phase: '开发'
  })
))
return devResults
```

### 验收（workflow）
```javascript
phase('验收')
const verifyResults = await parallel(TASKS.map(task => () =>
  agent(`<质量工程师 persona>\n检查以下改动...`, {
    label: `verify:${task.name}`,
    phase: '验收'
  })
))
return verifyResults
```

### 询问用户轮数 / 澄清
```
ask_user_question(questions: [{ id: 'rounds', question: '...', header: '确认', options: [...] }])
```

## 注意
- `parallel(...)` / `agent(...)` / `phase(...)` 都是 workflow 脚本内的 hook，不要当作普通函数用。
- 子代理会用 toDoWrite 维护进度，主 agent 用 `log()` 汇报状态。
- 默认把子代理放后台（run_in_background: true）并行推进，能并行就并行，主 agent 只做调度。
