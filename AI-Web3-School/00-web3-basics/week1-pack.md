# Week 1 Proof-of-Work Pack

> **AI x Web3 School · Web3Career Build**
> 提交者：Paradigme (GitHub: egak09)
> 周期：2026-05-24
> 主题：建立 AI × Web3 共同语言 — 概念、边界、工作流

---

## 📦 快速导航

| 类别 | 产物 | 链接 |
|------|------|------|
| 🧠 AI 概念 | AI 基础概念手册（10 个概念） | [ai-basics.md](ai-basics.md) |
| ⛓️ Web3 概念 | Web3 基础概念手册（11 个概念） | [web3-basics.md](web3-basics.md) |
| 🔐 Web3 安全 | EOA vs Smart vs Multisig 深度对比 | [account-comparison.md](account-comparison.md) |
| 🔀 AI × Web3 | 安全工作流（交互式流程图 + 说明） | [ai-web3-workflow.html](ai-web3-workflow.html) + [.md](ai-web3-workflow.md) |
| 🤖 Agent 实战 | 受限 Web3 助手：妖币策略案例 | [demon-strategy-workflow.md](demon-strategy-workflow.md) |
| ✅ 提交测试 | Proof-of-Work 提交格式验证 | [proof-of-work.md](proof-of-work.md) |
| 🎮 交互产物 | 最小可交互 AI 学习产物说明 | [interactive-demo-submission.md](interactive-demo-submission.md) |

**总入口**：[GitHub Repo](https://github.com/egak09/hermes-skills/tree/master/AI-Web3-School/00-web3-basics/)

---

## 🧠 AI 学习记录

### 概念卡片（10 个）

| 概念 | 一句话 | 实战锚点 |
|------|--------|---------|
| **LLM** | token 预测器，无状态函数 | 然然 (Hermes + DeepSeek V4) 的行为就是 LLM in action |
| **Prompt** | 系统指令 + memory + 技能 + 历史的全部文本 | 然然的 system prompt 包含你的个人信息和约束 |
| **Context Window** | 模型一次能"看到"多少 token 的上限 | memory 被限制在 2,200 chars 就是窗口约束 |
| **Workflow** | 固定步骤管线 A→B→C | 妖币策略扫描 = 标准 workflow |
| **Agent** | LLM + 工具 + 循环决策 | 然然 = Agent，不是 chatbot |
| **Tool Use** | LLM 生成函数调用参数，宿主系统执行 | write_file / terminal / search_files 的原理 |
| **AI Coding** | 理解环境 → 读上下文 → 写代码 → 测试 → 修复 | 妖币策略 Python 脚本开发流程 |
| **Guardrails** | 多层安全限制 | approvals.mode / skill 约束 / 文件路径白名单 |
| **Tracing** | 记录每一步 LLM 调用的输入输出 | 调试 Agent 错误的唯一手段 |
| **HITL** | 关键决策必须人工确认 | 妖币策略：AI 推送信号，人决定开不开仓 |

### 关键认知

> 本周最大的认知转变：**Agent ≠ 全自动**。能写成 workflow 的就别用 Agent。Agent 的价值在于你不知道要做什么的时候，而不是你知道但想偷懒。

---

## ⛓️ Web3 概念卡片

### 概念卡片（11 个）

| 概念 | 核心误区 |
|------|---------|
| **Account** | "合约地址也能转 ETH" → 可以，但可能永久锁死 |
| **Address** | 地址是公开的，分享后任何人都能查你的链上历史 |
| **Wallet** | "我的 ETH 存在 MetaMask 里" → 不是，MetaMask 只是钥匙 |
| **Seed Phrase** | "助记词 = 密码" → 不是，密码可重置，助记词丢了一切皆空 |
| **Private Key** | 泄露 = 不可逆，没有客服、没有冻结、没有回滚 |
| **Signature** | "签名只是登录" → eth_sign 可以授权任意交易 |
| **Transaction** | 上链即不可撤销，没有 7 天无理由退款 |
| **Gas** | "Gas Limit 设大跑得快" → 速度由 Gas Price 决定 |
| **Smart Contract** | "开源 = 安全" → 不，代码公开 ≠ 没有漏洞 |
| **Testnet** | "测试网过了主网就没问题" → 不，不能模拟 MEV/高并发/Gas 波动 |
| **Block Explorer** | "客服帮我追回" → 100% 是骗子，链上数据才是真相 |

### 账户对比核心结论

```
EOA      = 一人一钥，单点故障 → 个人日常钱包
Smart    = 代码即规则，可编程安全 → DeFi 金库/支付协议
Multisig = M-of-N 共管，集体决策 → DAO 国库/团队资金

安全本质的转变：
  EOA:      信任密钥
  Smart:    信任代码 + 开发者
  Multisig: 信任一群人不会同时犯错
```

---

## 🔀 AI × Web3 交叉实验：安全工作流

### 产出

[交互式 SVG 流程图](ai-web3-workflow.html) — 三区六步，颜色编码：

```
🤖 AI 辅助区           🔴 人工确认区           ⛓️ 链上执行区
AI 生成交易指令  →  人工复核审查  →  钱包签名  →  测试网执行  →  链上验证  →  人工最终确认
```

### 核心发现

**AI 和链上操作的边界：**

| AI 可以做 | AI 绝对不能做 |
|----------|-------------|
| 分析链上数据 | 动用私钥签名 |
| 生成 calldata | 执行交易 |
| 估算 Gas | 绕过人工确认 |
| 查询 tx 状态 | 替代人类判断 |

**设计原则：读/写权限永久分离。即使 AI 系统完全被入侵，攻击者最多推送一条假信号——假信号在人工复核环节被拦截。**

---

## 🤖 Agent / Workflow 实践：妖币策略扫描

### 实际运行系统

一个真实的受限 Web3 助手：

- **AI 做**：每 3 分钟扫描 200+ 山寨币 → K 线形态识别 → OI/Vol 分析 → 评分（≥68） → 1K 线确认 → Telegram 通知
- **人做**：看信号 → 看盘 → 决定开不开 → 手动在 Binance 下单 → 报余额
- **AI 永远不碰**：私钥、API Secret、下单接口

### 风控规则

| 规则 | 参数 |
|------|------|
| 凯利仓位 | Half-Kelly（50%） |
| 单笔风险 | ≤5% 本金 |
| 日亏损上限 | 18% → 停交易 |
| 最大持仓 | 3 个 |

---

## ⚠️ 本周问题与人工修正记录

### 问题 1：Proxy 502 → Cron 投递失败

**现象**：玄学日报 cron job 投递报错 `httpx.ProxyError: 502 Bad Gateway`

**排查**：
- Telegram 代理 XiGuaCore (127.0.0.1:7892) 出现间歇性 502
- `.env` 中 `TELEGRAM_PROXY` 仍指向 7892，但服务不稳定

**修正**：
- 用户更换/修复代理后，确认地址仍为 `127.0.0.1:7892`
- 更新 memory：标记旧代理 DriftVPN (127.0.0.1:1081) 已废弃
- 更新 Git clone 模板：从 1081 改为 7892
- 明确 Binance 暂不迁移到新代理（留待后续处理）

**教训**：代理是 GFW 下的单点故障。需要为关键 cron 加失败重试 + 退路方案。

### 问题 2：Proof-of-Work 文档定位错误

**现象**：第一版 proof-of-work.md 过于泛化，只提到 GitHub，未关联 web3career.build 平台

**修正**：
- 访问 https://web3career.build 确认平台结构
- 识别出 AI x Web3 School 课程页（/zh/programs/AI-Web3-School）
- 重写文档为 WCB 平台专用格式：平台入口 + 课程页链接 + 任务提交流程图 + WCB 审核标准

**教训**：提交前确认目标平台的实际结构和审核流程。不要假设"交到 GitHub 就行了"。

### 问题 3：Context Window 参数不确定

**现象**：初稿声称 DeepSeek V4 窗口为 128K tokens，但未验证

**修正**：改为"具体多大取决于版本，主流在 128K tokens 左右"——避免给出未经确认的精确数字

**教训**：不确定的数字宁可模糊，不要编造。在安全教育材料中，一个错误数字可能被当作事实传播。

---

## 🔗 链上验证（Week 2 计划）

本周专注于建立概念基础和工作流理解，未产生测试网交易哈希或合约地址。

**Week 2 计划**：
- 在 Sepolia 测试网部署一个最小合约
- 通过 AI 辅助生成 calldata → 人工复核 → 钱包签名 → Etherscan 验证
- 记录完整的 tx hash 和验证过程
- 走通一次完整的 AI × Web3 最小闭环

---

## 📊 本周产出统计

| 维度 | 数量 | 详情 |
|------|------|------|
| AI 概念 | 10 | LLM / Prompt / Context Window / Workflow / Agent / Tool Use / AI Coding / Guardrails / Tracing / HITL |
| Web3 概念 | 11 | Account / Address / Wallet / Seed Phrase / Private Key / Signature / Transaction / Gas / Smart Contract / Testnet / Block Explorer |
| 账户对比 | 3 类 × 6 维度 | EOA / Smart Account / Multisig |
| 流程图 | 1 个交互式 SVG + 1 篇说明 | ai-web3-workflow.html + .md |
| Agent 实战案例 | 1 个完整 workflow | 妖币策略扫描系统 |
| 问题 & 修正 | 3 条记录 | Proxy 502 / WCB 定位 / Context Window 参数 |
| GitHub commits | 9 | 全部可追溯 |
| 敏感信息 | 0 | 零私钥、零助记词、零 API Key |

---

## 🎯 Week 1 总结

本周建立了 AI 和 Web3 的共同语言基础：

1. **AI 侧**：理解了 LLM 的本质（token 预测器）、Agent 的工作原理（LLM+工具+循环）、以及为什么能写 workflow 就别用 Agent
2. **Web3 侧**：建立了从 Account 到 Block Explorer 的完整概念链，重点理解了私钥/助记词/签名/授权的安全边界
3. **交叉点**：通过交互式流程图明确了 AI 和链上操作的**读写分离原则**——这是贯穿整个 Week 1 的核心设计思想
4. **实战验证**：妖币策略案例证明了"AI 分析 + 人工决策 + 手动执行"的可行性

**Week 2 方向**：把概念变成实践 — 测试网部署合约，走通完整的 AI × Web3 闭环。

---

> ⚠️ 本 Pack 不含任何私钥、助记词、API Key、token、.env 文件或真实资产信息。
> 所有 proof 均通过 GitHub 公开 repo 的 commit 历史可验证。
