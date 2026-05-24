# Week 1 学习总结 — AI × Web3 School

> 发布平台：X / Twitter (@sky_dai7334)
> 格式：Thread（推文串）
> 字符限制：每条 ≤280 字符，中文约 140 字

---

## 推文 1/7 — 开场钩子

```
Week 1 @aiweb3school 结束。

我重新理解了三个东西：

1. Agent 不是黑魔法——是 LLM + 工具 + 循环
2. 钱包不是存钱罐——是钥匙
3. AI 和 Web3 之间有一条线，AI 永远不该跨过去

↓
```

---

## 推文 2/7 — AI 概念：Agent

```
🧠 重新理解的 AI 概念：Agent

以前我以为 Agent = 能自己干活的 AI。

现在知道 Agent 本质上是一个循环：
感知状态 → 调用工具 → 拿到结果 → 再决策 → 循环

LLM 只负责"说参数"，真正的执行是外部系统在做。

而且——能写成固定 workflow 的，千万别用 Agent。
Agent 每轮决策都调 LLM，又慢又贵又不确定。

↓
```

---

## 推文 3/7 — Web3 概念：钱包

```
⛓️ 重新理解的 Web3 概念：钱包

"我的 ETH 存在 MetaMask 里"——这话是错的。
钱包只是钥匙，资产始终在链上。

更重要的是：
• 助记词 ≠ 密码（丢了不能重置）
• 签名 ≠ 登录（eth_sign 可以授权任意交易）
• 一旦上链 = 不可撤销（没有客服、没有回滚）

这三句话能防住 90% 的 Web3 新手事故。

↓
```

---

## 推文 4/7 — AI × Web3 交叉问题

```
🔀 最核心的交叉问题：

"Agent 能不能自动帮我发交易？"

答案：绝对不能。原因很简单——

AI 权限 = 读数据 + 计算 + 通知
人类权限 = 签名 + 下单 + 转账

读/写权限永久分离。
即使 AI 被完全入侵，最多推送一条假信号——
假信号在人工复核环节就能被拦截。

↓
```

---

## 推文 5/7 — Proof-of-Work

```
✅ 本周做了 6 个 Proof-of-Work：

1. Web3 基础概念手册（11 个概念）
2. EOA vs Smart vs Multisig 深度对比
3. AI × Web3 安全工作流（交互式流程图）
4. 妖币策略：受限 AI 助手实战案例
5. AI 基础概念手册（10 个概念）
6. 最小可交互学习产物

全部公开：
github.com/egak09/hermes-skills

↓
```

---

## 推文 6/7 — 三个问题与修正

```
⚠️ 本周踩了三个坑：

1. GFW 代理 502 → cron 投递失败
   → 排查链路、更新 memory、标记废弃节点

2. Proof-of-Work 文档定位错误
   → 重写为 @web3careerbuild 平台专用格式

3. Context Window 参数不确定
   → 不确定的数字宁可模糊，不要编造

每次修正都是一次更好的学习。

↓
```

---

## 推文 7/7 — 未解决问题 & Week 2 方向

```
❓ 还没解决的问题：

测试网交易——我理解了概念和流程，但还没实际走通一次完整的
"AI 生成 calldata → 人工复核 → 钱包签名 → 测试网部署 → Etherscan 验证"

Week 2 方向：把这个闭环走通。
从概念变成链上可验证的 tx hash。

@web3careerbuild @ETHPanda_Org @LXDAO_Official
#AIxWeb3School #Web3Career #Week1
```

---

## 发布说明

- **平台**：X/Twitter
- **账号**：[@sky_dai7334](https://x.com/sky_dai7334)
- **Thread 总长**：7 条推文
- **预计阅读时间**：约 2 分钟
- **附图建议**：首推配 [ai-web3-workflow.html](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/ai-web3-workflow.html) 的截图或打开后截屏

### 发布版本（纯文本，方便复制）

---

🧵 **Week 1 @aiweb3school 结束。我重新理解了三个东西：**

1. Agent 不是黑魔法——是 LLM + 工具 + 循环
2. 钱包不是存钱罐——是钥匙
3. AI 和 Web3 之间有一条线，AI 永远不该跨过去

---

🧠 **AI 概念：Agent**

以前我以为 Agent = 能自己干活的 AI。现在知道 Agent 本质是一个循环：感知状态 → 调用工具 → 拿到结果 → 再决策。LLM 只负责"说参数"，真正的执行是外部系统在做。而且——能写成固定 workflow 的，千万别用 Agent。Agent 每轮决策都调 LLM，又慢又贵又不确定。

---

⛓️ **Web3 概念：钱包**

"我的 ETH 存在 MetaMask 里"——这话是错的。钱包只是钥匙，资产始终在链上。更重要的是：助记词 ≠ 密码（丢了不能重置）、签名 ≠ 登录（eth_sign 可以授权任意交易）、一旦上链 = 不可撤销。这三句话能防住 90% 的 Web3 新手事故。

---

🔀 **最核心的交叉问题："Agent 能不能自动帮我发交易？"**

绝对不能。AI 权限 = 读数据 + 计算 + 通知。人类权限 = 签名 + 下单 + 转账。读/写权限永久分离。即使 AI 被完全入侵，最多推送一条假信号——假信号在人工复核环节就能被拦截。

---

✅ **本周 6 个 Proof-of-Work：**

Web3 概念手册、EOA/Smart/Multisig 对比、AI×Web3 交互流程图、妖币策略受限 AI 助手案例、AI 概念手册、最小可交互学习产物。全部公开：github.com/egak09/hermes-skills

---

⚠️ **踩了三个坑：**

GFW 代理 502 导致 cron 失败 → 排查链路、更新配置。Proof-of-Work 文档定位错误 → 重写为 @web3careerbuild 平台格式。Context Window 参数不确定 → 不确定的数字宁可模糊不编造。每次修正都是一次更好的学习。

---

❓ **还没解决：测试网交易**

理解了概念和流程，但还没走通 "AI 生成 calldata → 人工复核 → 签名 → 部署 → Etherscan 验证" 的完整闭环。Week 2 方向：把这个闭环走通，从概念变成链上可验证的 tx hash。

@web3careerbuild @ETHPanda_Org @LXDAO_Official
#AIxWeb3School #Web3Career #Week1
