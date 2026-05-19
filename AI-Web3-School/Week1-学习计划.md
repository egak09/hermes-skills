# AI-Web3 School · Week 1 学习计划

> **学员**：Paradigme (egak09)  
> **时间预算**：< 5 小时/周  
> **学习风格**：理论 + 实践混合  
> **核心目标**：Agent 架构深度理解 + 加密交易 Agent 项目方向

---

## 📋 个人画像速览

| 维度 | 当前水平 | Week 1 策略 |
|------|---------|-------------|
| LLM 理解 | 懂 prompt/context/token | 深化到 Agent 架构层 |
| Web3 实操 | 测试网部署过合约 | 快速过，重点放安全边界 |
| 编程 | 不会写代码，能读 Python/JS | 以概念理解和配置为主 |
| Agent 工具 | 仅用过 Hermes Agent | 横向对比 3 个主流框架 |
| 目标方向 | 加密二级市场交易 Agent | Week 1 建立 Agent 架构认知 |

---

## 🎯 Week 1 学习目标

1. **能清晰区分** Prompt / Workflow / Agent 三者架构差异和应用边界
2. 理解 LLM 的「能做什么」与「不能做什么」——建立合理的 Agent 预期
3. 扫清 Web3 安全基础：私钥/签名/授权的 Agent 场景下的安全红线
4. 完成一次测试网交互，理解「AI 输出 → 人工确认 → 链上执行」闭环
5. 产出：一份个人概念笔记 + 待探索问题清单

---

## 📖 关键概念解释（深度版）

### 1. LLM 本质

> LLM 是基于上下文进行概率生成——给定文本，预测最合理的下一个 token 序列。

| LLM 擅长 | LLM 不擅长 |
|-----------|------------|
| 语言理解、代码生成、推理 | 精确事实记忆、确定性计算、跨会话状态保持 |
| 解释陌生概念、加速原型 | 代码审查最终决策、架构设计替代 |
| 模式识别、类比迁移 | 全新领域从零推理（无训练数据覆盖） |

**对你的意义**：交易 Agent 中，LLM 适合做「市场分析叙述」「策略解释」「风险提示生成」，不适合做「精确盈亏计算」「高频信号触发」。

### 2. Prompt vs Workflow vs Agent（你的优先方向）

```
Prompt：单次问答，我问你答。无状态，无工具。
  └─ 例：ChatGPT 聊天

Workflow：预定义流程，模型是其中一个节点，路径固定。
  └─ 例：用户输入 → LLM 总结 → 存入 Notion → 发邮件通知

Agent：模型自主规划、动态调用工具、跨轮管理状态。
  └─ 例：你（然然）读取网页 → 分析课程 → 生成计划 → 写入文件
```

| 维度 | Prompt | Workflow | Agent |
|------|--------|----------|-------|
| 状态管理 | 无 | 流程中传递 | 跨轮持续记忆 |
| 工具调用 | 无 | 固定节点 | 动态选择 |
| 决策权 | 用户 | 预设规则 | 模型自主 |
| 适用场景 | 问答、翻译 | 数据管道、审批流 | 研究、开发、交易辅助 |
| 失控风险 | 低 | 中 | 高（需 guardrails） |
| 可调试性 | 高 | 中 | 低（需 tracing） |

**对你的意义**：交易 Agent 是一个典型的 Agent 场景——目标开放式（寻找机会）、中间结果决定下一步、需要跨会话记忆持仓/策略、涉及高风险动作（交易执行需人工确认）。

### 3. Agent 安全架构（Web3 场景特别重要）

```
Agent 安全红线（不可逾越）：
┌─────────────────────────────────────────┐
│  私钥/助记词 → 永远不让 Agent 接触      │
│  签名授权    → 必须人工确认后再执行      │
│  转账/合约写入 → Agent 只能生成计划，   │
│                人在钱包端确认签名        │
│  Gas/费用    → Agent 可估算，不可自动支付│
└─────────────────────────────────────────┘
```

**关键概念**：
- **签名不是「点确认」**，是在授权一个具体动作
- **地址 ≠ 匿名**：链上行为可追溯
- **授权 ≠ 转账**：approve 操作是 DeFi 中最容易出事的环节

### 4. Agent 关键组件

| 组件 | 作用 | 你的 Hermes 中对应 |
|------|------|-------------------|
| Context Window | 模型能「看到」多少信息 | 当前会话上下文 |
| System Prompt | 身份、语气、边界 | 你的 profile + memory |
| Tool Calling | 模型输出结构化请求，框架执行 | terminal/browser/file |
| Skills | 可复用高层指令集 | skill 系统 |
| Guardrails | 输入输出验证，不合规中止 | 你的 skill 权限规则 |
| Handoff | 子任务移交控制权 | delegate_task |
| Tracing | 可视化执行链 | session_search |
| Error Recovery | 失败重试/回退/人工介入 | 工具执行错误处理 |

---

## ✅ Week 1 待完成 Checklist

> 按优先级排列，标注预计用时。总计约 4-5 小时。

### 🔴 核心（必做）

- [ ] **阅读 LLM 基础**（30 min）
  - [HuggingFace LLM Course Ch1](https://huggingface.co/learn/llm-course/chapter1/1)
  - 重点：理解 token、上下文窗口、生成机制
  - 产出：一段 200 字笔记

- [ ] **理解 Prompt/Workflow/Agent 差异**（45 min）
  - 阅读本文「关键概念解释」第 2 节
  - 用自己的话写 3 个场景分别适合用哪种
  - 产出：一个对比表格（Prompt vs Workflow vs Agent）

- [ ] **Agent 安全认知建立**（30 min）
  - 阅读本文「Agent 安全架构」
  - 列出交易 Agent 场景下不可自动化的 5 个动作
  - 产出：一份个人安全红线清单

- [ ] **创建 GitHub 学习仓库**（30 min）
  - 已完成 ✅（hermes-skills）
  - 在仓库中创建 `AI-Web3-School/Week1/` 目录结构

### 🟡 推荐

- [ ] **Agent 框架快速对比**（45 min）
  - 你已经用了 Hermes Agent
  - 快速浏览 [OpenAI Agents SDK Intro](https://openai.github.io/openai-agents-python/) 
  - 浏览 [LangGraph Overview](https://langchain-ai.github.io/langgraph/)
  - 产出：三个框架的 3 句话对比 + 为什么选 Hermes

- [ ] **测试网交互回顾**（30 min）
  - 如果之前做过：整理之前的交易哈希、合约地址
  - 如果没做过：完成一次 Sepolia 测试网转账
  - 产出：区块浏览器截图/交易哈希记录

- [ ] **行业信息源整理**（30 min）
  - 列出 5 个 AI Agent × Web3 相关的 X/TG 账号或信息源
  - 关注 [@aiweb3school](https://x.com/aiweb3school)

### 🟢 挑战（有余力）

- [ ] **Agent 安全边界实验**（45 min）
  - 用 Hermes 生成一个「假想的交易计划」
  - 标注出哪些步骤可以自动化、哪些必须人工确认
  - 画出「AI 输出 → 人工复核 → 钱包确认 → 链上执行 → 验证记录」的流程图

- [ ] **概念卡片**（30 min）
  - 为 5 个关键概念（Agent/Workflow/Guardrails/Tool Calling/Context Window）各写一张概念卡片
  - 每张卡片：定义 + 你的理解 + 和交易的关联

---

## ❓ 不懂问题清单

> 学习过程中随时补充

1. Agent 的「跨会话记忆」在技术上是怎么实现的？我的 Hermes memory 和 session_search 分别对应什么？
2. 如果我让 Agent 帮我分析市场数据，它怎么获取实时数据？需要哪些工具？
3. Guardrails 在交易场景中具体怎么设计？比如「当 Agent 建议开仓时，要验证什么？」
4. Workflow 和 Agent 的边界是不是模糊的？一个带工具的 Workflow 和 Agent 有什么区别？
5. Hermes Agent 的 skill 系统和 LangGraph 的 graph 有什么区别？

---

## 📚 推荐材料速查

| 类型 | 链接 | 重点看 |
|------|------|--------|
| LLM 入门 | [HuggingFace LLM Course](https://huggingface.co/learn/llm-course/chapter1/1) | Ch1 全部 |
| Agent 概念 | [OpenAI Agents SDK Intro](https://openai.github.io/openai-agents-python/) | 前 3 节 |
| Agent 对比 | [LangGraph Overview](https://langchain-ai.github.io/langgraph/) | Quick Start |
| Hermes 文档 | [Hermes Docs](https://hermes-agent.nousresearch.com/docs/) | Agent 架构部分 |
| AI Agents 入门 | [MS AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) | 00-02 课 |
| Web3 账户 | [Ethereum Accounts](https://ethereum.org/developers/docs/accounts/) | 基础部分 |
| 训练营 Week1 | [Week 1 Notion 页](https://ethpanda.notion.site/Week-1-AI-Web3-354bbd63be878198afc4f155b5c3a69f) | 任务说明 |
| 训练营手册 | [AI-Web3 School Handbook](https://aiweb3.school/zh/handbook/) | 全部 |

---

## 🗺️ 你的学习路径预览（4 周视角）

```
Week 1 ──→ Agent 架构认知 + 安全红线
Week 2 ──→ 交易 Agent 设计（数据源、决策逻辑、执行边界）
Week 3 ──→ 最小可用 Agent 原型（Hermes skill 化交易辅助）
Week 4 ──→ 链上交互闭环（Agent 建议 → 人工确认 → 链上验证）
```

---

*生成时间：2026-05-20 · 然然 (Hermes Agent) · 基于 AI-Web3 School 训练营 Week 1 大纲*
