---
name: binance-trading
description: "Binance 加密货币交易助手 — 行情、账户、下单、盈亏追踪、凯利仓位计算，主用合约交易"
version: 1.1.0
category: trading
python: ">=3.11"
dependencies:
  - ccxt
---

# Binance 交易助手

> Paradigme 专属加密货币交易工具集。主用**合约交易**，所有交易前须过**凯利公式**计算仓位。

## ⚠️ 安全

- 密钥仅存本地 `references/config.json`（**已 gitignore**）
- IP 白名单：`172.235.214.193`
- 不走代理无法访问 Binance API

## 模块

| 模块 | 功能 | 
|------|------|
| `market.py` | 价格/K线/深度/资金费率/市场总览 |
| `account.py` | 余额/持仓/交易历史 |
| `order.py` | 市价单/限价单/撤单 |
| `portfolio.py` | 手动记账/盈亏/胜率统计 |
| `kelly.py` | **凯利公式仓位计算**（交易前必用） |
| `check.py` | 一键综合检测 |

## 快速使用

```bash
# 综合检测
python scripts/check.py

# 行情总览
python scripts/market.py overview

# 凯利计算 (资金 胜率 盈额 亏额)
python scripts/kelly.py 1000 0.55 200 100
```

## 交易流程

1. `check.py` 看行情 + 账户
2. `kelly.py` 算仓位（必须）
3. `order.py` 下单
4. `portfolio.py log` 记账

## 凯利公式

**f* = (p·b - q) / b**

- p = 胜率 · b = 盈亏比 · q = 1-p
- 默认 Half-Kelly (50%)，上限 25% 本金
- 胜率 < 35% 或期望为负 → 不交易
