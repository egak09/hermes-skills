# 01 · AI Agents — 自主智能体框架

> 从零到一构建和运作 AI Agent 系统的完整实操笔记

---

## 📋 本模块文章

| # | 标题 | 核心内容 |
|---|------|---------|
| 1 | **Hermes Agent 核心架构** | Agent Loop、Tool Calling、Context Management |
| 2 | **Skills 系统：Agent 的过程记忆** | SKILL.md 格式、自动加载、curator 生命周期 |
| 3 | **Cron 自动化** | 定时任务、脚本链、内容引擎 |
| 4 | **多 Agent 协作** | delegate_task、子进程、tmux 编排 |

## 🎯 学完你能

- 理解 AI Agent 的核心运行循环（LLM → Tool Call → Result → loop）
- 用 Skills 系统让 Agent 积累领域知识
- 搭建定时自动化管线（数据采集 → LLM 加工 → 推送）
- 并行多个 Agent 协同完成复杂任务

---

### 我的真实环境

- **Agent 框架**: Hermes Agent (Nous Research 开源)
- **模型**: DeepSeek V4 Pro
- **平台**: Telegram Gateway（实时响应 + cron 推送）
- **OS**: Windows 10 + Git Bash (MSYS2)
- **工作目录**: `D:\Hermes file\`

> 所有代码和命令均在此环境中验证通过 ✅
