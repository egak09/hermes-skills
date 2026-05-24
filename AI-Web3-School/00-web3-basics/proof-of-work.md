# Web3Career Build — 任务提交测试

> 最小 Proof-of-Work 提交。证明已理解 [Web3Career Build](https://web3career.build) 平台的任务提交流程、证明格式和审核标准。
>
> 平台背景：Web3Career Build（WCB）由 **ETHPanda × LXDAO** 联合发起，当前**AI x Web3 School** 共学计划进行中。
>
> 官方入口：[web3career.build](https://web3career.build) · [AI x Web3 School 课程页](https://web3career.build/zh/programs/AI-Web3-School) · [aiweb3.school](https://aiweb3.school)

---

## 提交入口

- **平台**：[Web3Career Build](https://web3career.build) — 统一报名、任务认领、作品提交、审核追踪
- **课程**：[AI x Web3 School](https://web3career.build/zh/programs/AI-Web3-School) — Bootcamp 共学阶段
- **Proof 存储**：GitHub 公开 repo（作为可验证的任务产出物链接）

---

## Proof 类型

| 类型 | 用途 | 链接 |
|------|------|------|
| **GitHub 公开 repo** | 主要 — 所有任务产出物的永久存储和版本历史 | [egak09/hermes-skills](https://github.com/egak09/hermes-skills) |
| **Commit 历史** | 辅助 — 每个任务独立 commit，证明提交时间线 | [commits](https://github.com/egak09/hermes-skills/commits/master) |
| **WCB 平台** | 提交入口 — 在任务页粘贴 GitHub 链接作为 proof | [课程页](https://web3career.build/zh/programs/AI-Web3-School) |

---

## 已完成任务清单（AI x Web3 School — 共学阶段）

| # | 任务 | Proof（GitHub 公开链接） | Commit |
|---|------|--------------------------|--------|
| 1 | Web3 基础概念手册（11 个概念） | [web3-basics.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/web3-basics.md) | `77e7bc6` |
| 2 | EOA / Smart / Multisig 账户深度对比 | [account-comparison.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/account-comparison.md) | `039ff65` |
| 3 | AI × Web3 安全工作流（流程图 + 说明） | [ai-web3-workflow.html](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/ai-web3-workflow.html) + [.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/ai-web3-workflow.md) | `eec2d27` |
| 4 | 受限 Web3 助手实战（妖币策略案例） | [demon-strategy-workflow.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/demon-strategy-workflow.md) | `e40b535` |
| 5 | AI 基础概念手册（10 个概念） | [ai-basics.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/ai-basics.md) | `8b6013e` |
| 6 | Proof-of-Work 提交测试（本文档） | [proof-of-work.md](https://github.com/egak09/hermes-skills/blob/master/AI-Web3-School/00-web3-basics/proof-of-work.md) | `c55bab9` |

---

## 审核者需要看到的信息

1. **任务完成度** — 每份文档包含：目录、解释、具体例子、误区/风险提示
2. **原创性** — 所有示例来自真实实践环境（Hermes Agent、Binance 妖币策略、代理配置），非泛化 AI 输出
3. **可验证性** — GitHub commit 时间戳证明提交在任务期限内
4. **安全合规** — 全文不含真实私钥、助记词、API Key、token 或 `.env` 敏感信息
5. **双语可读** — 中文为主，关键术语保留英文，面向华语区 Builder

---

## 提交流程理解

```
WCB 平台任务页 → 认领任务 → 本地完成 → 输出到 GitHub
                                              ↓
                              WCB 提交框粘贴 GitHub 链接
                                              ↓
                              审核者打开链接查看内容
                                              ↓
                              验证：内容完整性 + commit 时间 + 原创性 + 安全合规
                                              ↓
                              ✅ 通过 / ❌ 要求修改
```

---

## 提交证明

```
提交者：Paradigme (GitHub: egak09)
平台：Web3Career Build — AI x Web3 School
日期：2026-05-24
Proof 类型：GitHub 公开 repo
Repo：https://github.com/egak09/hermes-skills
路径：AI-Web3-School/00-web3-basics/
WCB 课程页：https://web3career.build/zh/programs/AI-Web3-School

验证步骤：
  1. 在 WCB 平台任务提交框粘贴 GitHub 文档链接
  2. 审核者打开链接，查看内容质量
  3. 审核者查看 commit 历史确认提交时间
  4. 审核者确认无敏感信息泄露
```

---

> ⚠️ 本文仅供任务提交流程验证，不含任何私钥、助记词、API Key 或真实资产信息。
