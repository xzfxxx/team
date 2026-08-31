# Roo Code 平台调用方法

> 平台说明只在本会话首次进入团队模式时加载一次。Roo Code 是 VS Code 插件，用 modes + 异步 subagent。

## 识别
你在 VS Code 的 Roo Code 插件内，使用自定义 mode 作为 orchestrator，配合 subagent。

## 子代理派生（配置式 + mode）
- 用 **modes** 定义角色（Architect / Code / QA…），角色 persona 写在对应 mode 的 system prompt 里（取自 `roles/*.md`）。
- 用 `[subagent]` 异步子代理：orchestrator mode 派生 subagent，异步跑完回收结果。

## 并行
- 可派生多个异步 subagent 并行，orchestrator 汇总。

## 问用户
Roo 的 GUI 审批。

## 说明
Roo 的架构和团队模式天然契合（Architect mode 派活给 Code mode 就是"主 agent 调度"），但操作在 GUI 里发生。
