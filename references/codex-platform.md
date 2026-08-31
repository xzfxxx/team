# Codex 平台调用方法

> 平台说明只在本会话首次进入团队模式时加载一次。仅包含 Codex 区别于 DSH/Claude 的"子代理调用方式"。

## 识别
你的环境里有 `codex` CLI，且**子代理是配置式**的（在仓库根 `AGENTS.md` 里预先声明），主 agent 按名字派活，而不是运行时临时 spawn。

## 子代理定义（配置式）
把团队角色写进 `AGENTS.md` 的 subagent 段（把 `roles/*.md` 的 `【Persona】` 作为 prompt）。示例：
```
[subagent name="dev" description="开发工程师：实现代码+单测"]
prompt = "<开发工程师 persona> ..."
[subagent name="qa" description="质量工程师：独立验收"]
prompt = "<质量工程师 persona> ..."
```

## 派生与并行
- **单任务**：`codex exec --full-auto "<subagent name> + 任务描述"`
- **多任务并行**：先 `git worktree add` 给每个 worker 一份**独立工作区**，再并发跑多个 `codex exec`（或用 multi-agent / Loom 编排）。
- **orchestrator（工头）模式**：一个主 agent 管理多个 worker，接收结果、决定下一步。

## 隔离（重要）
Codex 默认**共享同一个仓库**，并行 worker 会互相污染。并行前必须用 git worktree 隔离，否则别并行。

## 问用户
用 `codex exec` 的审批流程 / GUI 交互，或直接输出确认清单让用户拍板。
