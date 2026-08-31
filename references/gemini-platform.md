# Gemini CLI 平台调用方法

> 平台说明只在本会话首次进入团队模式时加载一次。仅包含 Gemini CLI 区别于 DSH/Claude 的"子代理调用方式"。

## 识别
你的环境里有 `gemini` CLI，子代理在 `AGENTS.md` 里用 `[subagent]` 声明。

## 子代理定义（配置式）
在仓库根 `AGENTS.md` 里声明（支持 tools / model / prompt）：
```
[subagent name="dev"]
description: 开发工程师：实现代码+单测
prompt: "<开发工程师 persona> ..."
tools: [...]
```

## 派生与并行
- 主 agent 按名字派生 subagent，可**并行**运行多个 subagent。
- 每个 subagent 拿到独立的 prompt + 上下文。

## 问用户
交互式确认；需要拍板的地方直接输出确认清单。
