# 最小可交互 AI 学习产物 — AI × Web3 安全工作流

> 从 Web3Career Build · AI x Web3 School 共学阶段已完成的 6 个任务产物中，选择最符合"可交互学习工具"定义的一件提交。

---

## 选择的产物

**[ai-web3-workflow.html](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/ai-web3-workflow.html)** — 暗色主题交互式 SVG 流程图

**GitHub 链接**：[https://github.com/egak09/hermes-skills/tree/master/AI-Web3-School/00-web3-basics/](https://github.com/egak09/hermes-skills/tree/master/AI-Web3-School/00-web3-basics/)

**配套说明**：[ai-web3-workflow.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/ai-web3-workflow.md)

---

## 1. 它解决什么学习问题

**问题**：AI Agent 能帮你分析链上数据、生成交易 calldata、构造合约调用——但它**不能替你签名、不能替你承担风险、也不能替你验证结果**。新手 Builder 最常见的困惑是："AI 到底能帮我做到哪一步？我应该在什么时候接手？"

**解决方案**：这个交互式流程图把 AI × Web3 的协作边界**可视化**——三种颜色区域（🤖 AI 辅助区 / 🔴 人工确认区 / ⛓️ 链上执行区）+ 六步流程 + 风险标记，让学习者一目了然地看到：

- 哪些步骤 AI 可以做
- 哪两步**必须人工确认**（红色高亮 + 发光强调）
- 每一步之间传递什么数据
- 每个环节有什么风险（⚠️ 黄色标记）

---

## 2. 用户如何与它交互

```
用户操作：在浏览器打开 ai-web3-workflow.html
         ↓
交互方式：
  ├─ 视觉扫描：三区颜色编码（青=AI / 玫红=人工 / 绿=链上）
  ├─ 流程追踪：从左到右跟踪箭头和数据标签
  ├─ 风险识别：黄色 ⚠ 标记指出每个过渡点的风险
  ├─ 决策理解：底部"关键决策点"面板展示 通过/拒绝 分支
  ├─ 图例对照：左下角 Legend 帮助理解颜色和线条含义
  └─ 深入学习：三张 Info Card 总结 AI 辅助 / 人工确认 / 风险清单
```

不需要安装、不需要服务器、不需要任何依赖——就是一个 `.html` 文件，任何浏览器打开即用。

---

## 3. 输入示例和输出示例

### 用户输入（心智层面）

用户带着这个问题看流程图：

> "我想让 AI 帮我部署一个合约到测试网。它说可以全自动——我应该让它全自动吗？"

### 流程图输出（用户看到的答案）

扫描流程图后，用户能自己得出答案：

| 步骤 | 谁做 | 我学到的 |
|------|------|---------|
| 生成部署指令 | 🤖 AI | OK，AI 可以帮我生成 calldata |
| 人工复核 | 🔴 **我必须看** | 金额对吗？地址对吗？合约对吗？ |
| 钱包签名 | 🔴 **我必须点 Confirm** | 私钥永远不离开我的钱包 |
| 测试网执行 | ⛓️ 链上自动 | 广播后不可撤销 |
| 链上验证 | 🔎 AI 辅助 | AI 帮我查 tx status |
| 最终确认 | 🔴 **我必须对比** | 浏览器上的状态 ≠ 我以为的状态？→ 回溯 |

**结论**：不能全自动。三道人工关卡不可绕过。

---

## 4. AI 生成 vs 人工修改 / 验证

| 组成部分 | AI 做了什么 | 我做了什么 |
|---------|-----------|-----------|
| HTML/CSS 结构 | 基于 architecture-diagram skill 模板生成 | — |
| 配色方案 | 从 skill 规定的 semantic color palette 选用 | 确保三个区域的颜色对比度足够区分 |
| 流程逻辑（6 步） | AI 根据 Agent→Review→Sign→Execute→Verify→Confirm 的自然顺序编排 | 验证每一步的输入/输出是否对应真实的 Hermes Agent 行为 |
| 组件命名和标签 | AI 生成（"AI Agent · 生成交易指令"等） | 核实每个标签是否准确反映该步骤的实际操作 |
| 风险标记文本 | AI 生成（"AI 幻觉 / 错误 calldata"等） | 确认每个风险点对应真实的踩坑经历（盲签、钓鱼地址、Gas 不足） |
| 底部 Info Cards | AI 生成三条总结 | 改写为中文 + 去掉泛化表述，加入具体场景 |
| 反馈回路箭头 | AI 画了"不通过→回溯"的虚线 | 确认这是实际工作流（妖币策略如果信号被拒就是回到 Step 1 重新扫） |
| 整体审核 | — | 全文过一遍：无 AI 腔、无虚假示例、所有链接可访问 |

### 关键修改举例

**AI 初稿**：`"Human Review — validate transaction parameters"`  
**我改成**：`"🔍 人工复核 — 审查金额·地址·逻辑"` + 红色底框 + `"⚠️ 不通过即终止"`

这样学习者不需要理解"validate transaction parameters"是什么意思——看到红色 + 终止两个字就知道：这一步不能跳过。

---

## 5. 限制与下一步改进

### 当前限制

- **无实际用户输入**：目前是"看"的交互，不是"输入-输出"式交互。不能输入一个地址让流程图动态验证
- **静态数据**：风险标记是写死的，不能根据实际链上数据动态变化
- **仅教育目的**：不是一个可执行的工作流引擎，不能实际发起交易
- **单语言**：仅中文，未做 i18n

### 下一步改进方向

| 优先级 | 改进 | 效果 |
|--------|------|------|
| 🔴 高 | 加入交互式 checkpoints：用户点击每一步时弹出"你同意吗？"确认框 | 变成真正的"输入→确认→通过"交互 |
| 🟡 中 | 加入输入框：用户粘贴一个 tx hash，流程自动查询 Etherscan 并展示验证结果 | 从"看图"变成"实操" |
| 🟡 中 | 加入 quiz 模式：随机隐去某一步，让用户选择谁是执行者（AI or Human） | 自测学习效果 |
| 🟢 低 | 响应式适配移动端 | 手机也能看 |
| 🟢 低 | 英文版 + 多链配色（Solana 紫色 / Polygon 紫色） | 覆盖更多学习者和链 |

---

## 提交证明

```
产物：ai-web3-workflow.html（交互式 SVG 流程图）
平台：Web3Career Build — AI x Web3 School
提交者：Paradigme (GitHub: egak09)
日期：2026-05-24
Proof 类型：GitHub 公开 repo
链接：https://github.com/egak09/hermes-skills/tree/master/AI-Web3-School/00-web3-basics/

AI 辅助范围：HTML 结构、SVG 组件坐标、配色、流程标签初稿
人工验证范围：流程逻辑、标签准确性、风险点对应、中文化、去 AI 腔
```
