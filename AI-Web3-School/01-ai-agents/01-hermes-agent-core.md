# Hermes Agent 核心架构

> Hermes Agent 是一个开源的 AI Agent 框架，由 Nous Research 开发。  
> 它可以在终端、Telegram、Discord 等平台上运行，支持任意 LLM 提供商。

---

## 1. Agent Loop：AI Agent 的心脏

每个 AI Agent 本质上都是一个无限循环：

```
┌─────────────────────────────────────┐
│  1. 构建 System Prompt              │
│     ↓                               │
│  2. 调用 LLM（带 Tools Schema）     │
│     ↓                               │
│  3. LLM 返回:                       │
│     ├─ Tool Calls → 执行 → 追加结果 │
│     │                  ↓            │
│     │            回到步骤 2         │
│     └─ Text → 返回给用户（结束）    │
└─────────────────────────────────────┘
```

### 关键参数

```yaml
agent:
  max_turns: 90        # 最大循环次数，防止无限循环
  tool_use_enforcement: true  # 强制执行工具调用
```

### 每轮的数据结构

```python
messages = [
    {"role": "system", "content": "..."},    # 系统提示
    {"role": "user", "content": "..."},      # 用户消息
    {"role": "assistant", "content": None, "tool_calls": [...]},  # LLM 返回的工具调用
    {"role": "tool", "tool_call_id": "...", "content": "..."},    # 工具执行结果
    # ... 循环
]
```

---

## 2. Tool Calling：Agent 的行动能力

Agent 不是"聊天机器人"——它能真正做事，靠的就是**工具调用**。

### Hermes 的工具分类

| Toolset | 能力 | 使用场景 |
|---------|------|---------|
| `terminal` | Shell 命令 | 代码、脚本、git、安装 |
| `file` | 文件读写搜索 | 知识管理、数据处理 |
| `web` | 网络搜索提取 | 研究、资讯 |
| `browser` | 浏览器自动化 | 网页交互 |
| `delegation` | 子 Agent 委派 | 并行任务 |
| `cronjob` | 定时任务 | 自动化管线 |
| `memory` | 持久记忆 | 跨会话知识 |
| `skills` | 技能系统 | 过程知识复用 |

### 如何注册自定义工具

```python
from tools.registry import registry

def my_tool(param: str) -> str:
    return json.dumps({"result": f"处理了: {param}"})

registry.register(
    name="my_tool",
    toolset="custom",
    schema={
        "name": "my_tool",
        "description": "我的自定义工具",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "输入参数"}
            },
            "required": ["param"]
        }
    },
    handler=lambda args, **kw: my_tool(param=args.get("param", "")),
)
```

---

## 3. Context Management：上下文的艺术

### 上下文压缩

当对话太长时，Agent 自动压缩：

```yaml
compression:
  enabled: true
  threshold: 0.50     # 达到 token 上限的 50% 时触发
  target_ratio: 0.20  # 压缩到 20%
```

压缩原理：用辅助 LLM 总结早期对话，把冗长工具输出压缩成摘要。

### Prompt Caching

Agent 会尽量保持 system prompt 和 tool schema 不变，以利用 LLM 的 prompt caching 节省成本。

**重要规则**：不要在对话中途改变 tools 或 system prompt——会破坏缓存。

---

## 4. 我的 Hermes 配置要点

### Gateway 多平台

Hermes 可以通过 Telegram 接收消息，同时保留完整工具访问权（不是只能聊天）。

```bash
# 启动 gateway
hermes gateway run

# 后台运行  
hermes gateway start

# 查看状态
hermes gateway status
```

### 我的 Telegram 配置

- 代理：`TELEGRAM_PROXY=http://127.0.0.1:1081`（GFW 必需）
- 依赖：`pip install aiohttp-socks`

### Provider 切换

Hermes 支持 20+ 提供商，一键切换：

```bash
hermes model           # 交互式选择
hermes chat -m deepseek/deepseek-chat  # 直接指定
```

---

## 5. 核心优势总结

| 特性 | 说明 |
|------|------|
| **Skills 系统** | Agent 的过程记忆，越用越聪明 |
| **Persistent Memory** | 跨会话记住你是谁、你的偏好 |
| **Provider 无关** | 换模型不换代码 |
| **多平台** | Telegram / Discord / CLI 同一 Agent |
| **Profiles** | 多个独立实例，隔离配置 |
| **全栈工具** | 终端 + 文件 + 网络 + 浏览器 |

---

### 下一步

→ [02 · Skills 系统：Agent 的过程记忆](02-skills-system.md)
