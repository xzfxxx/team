# Cursor 平台调用方法

> 平台说明只在本会话首次进入团队模式时加载一次。Cursor 是 GUI IDE + 后台 agent。

## 识别
你在 Cursor 编辑器内运行，通过 GUI 派发 subagent（后台/隔离 checkout）。

## 子代理派生（GUI 为主）
- 通过 Cursor 界面派发后台 subagent，每个 subagent 在**独立 checkout / 沙箱**里工作，互不污染。
- 把角色 persona（`roles/*.md` 的 `【Persona】`）作为 subagent 的 instruction。

## 并行
- 可一次派发多个后台 agent 并行跑，结果流式回收。
- 主 agent（orchestrator）负责拆分任务、汇总各 agent 结果。

## 问用户
Cursor 的 GUI 审批 / 确认对话框。

## 说明
Cursor 是 IDE 内的 agent，编排更依赖 GUI；代码级自动编排不如 DSH/Claude 自由，适合"派发-回收"式分工。
