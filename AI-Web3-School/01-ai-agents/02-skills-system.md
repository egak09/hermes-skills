# Skills 系统：Agent 的过程记忆

> Skills 是 Hermes Agent 最独特的设计——让 Agent 从经验中学习，  
> 将解决问题的过程固化为可复用的"技能文档"。

---

## 1. 什么是 Skill？

Skill 不是一个可执行脚本（虽然可以附带脚本），而是一个 **SKILL.md 文档**，包含：

- **触发条件**：什么情况下应该加载这个 skill
- **操作流程**：分步骤的解决问题方案
- **命令模板**：可以直接复制使用的命令
- **踩坑记录**：已知问题 + 修复方法
- **引用文件**：脚本、配置模板、参考数据

### 示例：binance-trading skill

```markdown
---
name: binance-trading
description: "Binance 加密货币交易助手"
category: trading
---

# Binance 交易助手

## 交易流程
1. check.py 看行情 + 账户
2. kelly.py 算仓位
3. order.py 下单
4. portfolio.py log 记账

## 凯利公式
f* = (p·b - q) / b
```

---

## 2. Skill 的生命周期

```
创建 → 使用 → 发现不足 → 修补(patch) → 积累优化 → 长期保留
  │                            │
  │                            └── curator 管理
  └── 按类别归档（母文件夹）
```

### 创建 Skill

```bash
# 方式 1：对话中自然创建
# Agent 完成复杂任务后，用户同意 → 自动生成 SKILL.md

# 方式 2：CLI 安装
hermes skills install <id>
hermes skills install https://raw.githubusercontent.com/.../SKILL.md
```

### 修补 Skill

当你用 skill 时发现它过时、有错、缺少步骤，立即 patch：

```python
skill_manage(action='patch', name='binance-trading', 
    old_string='旧内容', new_string='新内容')
```

### Curator：Skill 管家

自动后台维护：

```bash
hermes curator status   # 查看状态
hermes curator run      # 手动触发
hermes curator pin <name>    # 锁定（防止误删）
hermes curator archive <name> # 归档
```

---

## 3. Skill 的组织架构

所有 skill 必须按类别归入母文件夹：

```
skills/
├── trading/
│   ├── binance-trading/       # 交易基础设施
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── demon-strategy/        # 妖币策略
│       ├── SKILL.md
│       └── scripts/
├── crypto/
│   └── blockbeats-skill/      # 加密数据
├── devops/
│   └── hermes-windows-admin/  # Windows 运维
├── esoteric/
│   └── esoteric-daily-guidance/ # 玄学
├── software-development/
│   ├── closed-loop-verification/
│   ├── redundant-verification/
│   └── intent-reconstruction/
└── ...
```

**GitHub 同步**: `egak09/hermes-skills`（所有 skill 同步 push）

---

## 4. 为什么 Skills 是关键

| 没有 Skills | 有 Skills |
|-------------|-----------|
| 每次重新探索 | 直接加载已验证方案 |
| 重复犯同样的错 | 踩坑记录防重复 |
| Agent 能力不增长 | 每次解决问题后更强 |
| 命令靠记忆 | 精确命令复制粘贴 |

---

## 5. 实战：我积累了哪些 Skills？

| Skill | 知识点 | 价值 |
|-------|--------|------|
| `binance-trading` | API 连接、订单、凯利公式 | 交易基础设施 |
| `demon-strategy` | K线形态 + OI/Vol + 确认机制 | 策略 v2.2 定稿 |
| `blockbeats-skill` | 1500+ 数据源 API | 加密数据全栈 |
| `hermes-windows-admin` | Junction 磁盘迁移 | 运维救命 |
| `esoteric-daily-guidance` | 三合一玄学推演 | 决策辅助 |
| `closed-loop-verification` | 工程控制论验证 | 质量保证 |
| `redundant-verification` | 高风险操作双检 | 防灾难 |
| `intent-reconstruction` | 歧义消息消歧 | 交互效率 |

---

### 下一步

→ [03 · Cron 自动化](03-cron-automation.md)
