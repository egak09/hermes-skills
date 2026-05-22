# 多 Agent 协作：并行智能体集群

> 一个 Agent 是助手，多个 Agent 是团队。  
> Hermes 支持三种多 Agent 模式，逐级增强。

---

## 1. 三种并行模式

| 模式 | 机制 | 适用场景 | 持久性 |
|------|------|---------|--------|
| **delegate_task** | 同步子 Agent | 快速并行子任务（分钟级） | ❌ 非持久 |
| **tmux 独立进程** | 独立 Hermes 实例 | 长时自治任务（小时/天级） | ✅ 持久 |
| **Kanban 工作队列** | SQLite 任务板 | 多 profile 协同 | ✅ 持久 |

---

## 2. delegate_task：快速子任务委派

### 单任务模式

```python
delegate_task(
    goal="检查 src/utils.py 中的所有函数是否都有类型注解",
    context="项目在 /home/project/，Python 3.11，用 mypy",
    toolsets=['terminal', 'file']
)
```

### 并行批处理（最多 3 个）

```python
delegate_task(tasks=[
    {"goal": "审计 auth.py 安全问题", "toolsets": ['terminal', 'file']},
    {"goal": "检查 api.py 性能瓶颈", "toolsets": ['terminal', 'file']},
    {"goal": "审查 models.py DB schema", "toolsets": ['terminal', 'file']},
])
```

### delegate_task vs 直接工具调用

| | delegate_task | 直接工具调用 |
|-|-------------|-----------|
| 上下文 | 隔离（不污染主对话） | 共享（会填满上下文窗口） |
| 并行 | 天然支持 | 需手动编排 |
| 工具 | 受限（无 clarify/memory 等） | 完全访问 |
| 持久性 | 父会话中断即取消 | N/A |

### 核心规则

- 子 Agent **无记忆**——把上下文写进 `context` 参数
- 子 Agent **不能 ask 用户**——不能 clarify
- 子 Agent 总结是**自报**不是事实——关键操作要自己验证

---

## 3. tmux 独立进程：长时自治 Agent

适合需要运行数小时甚至数天的任务。

### 启动

```bash
# 创建隔离 session
tmux new-session -d -s agent1 -x 120 -y 40 'hermes -w'

# 发送任务
tmux send-keys -t agent1 '审查整个项目代码并写一份安全审计报告' Enter

# 查看进度
tmux capture-pane -t agent1 -p | tail -20
```

### 多 Agent 协同示例

```bash
# Agent A: 后端
tmux new-session -d -s backend 'hermes -w'
tmux send-keys -t backend '用 FastAPI 构建用户管理系统的 REST API' Enter

# Agent B: 前端  
tmux new-session -d -s frontend 'hermes -w'
tmux send-keys -t frontend '根据后端 API 构建 React Dashboard' Enter

# 查看 Backend 进度，提取 API 契约
tmux capture-pane -t backend -p | grep "route" > api_spec.txt

# 传递给 Frontend Agent
tmux send-keys -t frontend "这是后端 API 规格: $(cat api_spec.txt)" Enter
```

### `-w` flag 的重要性

`--worktree` 模式为每个 Agent 创建独立的 git worktree，防止代码冲突。

---

## 4. 选择指南

```
需要做完就忘的快速任务？
  → delegate_task

需要跑很久（>10分钟）？
  → tmux 独立进程

需要多步骤、跨越多天的？
  → Cron Job 定时触发

需要多个 profile 协同？
  → Kanban 工作队列
```

---

### 我的真实多 Agent 场景

| 场景 | 模式 | 效果 |
|------|------|------|
| 链上热点分析 + 发帖生成 | Cron 链式 | 自动化 |
| 代码审查并行多个文件 | delegate_task batch | 3 个文件同时审 |
| 长期交易监控 | 独立 Python 脚本 + Cron | 7×24 运行 |

---

### 回到总览

→ [README.md](../README.md)
