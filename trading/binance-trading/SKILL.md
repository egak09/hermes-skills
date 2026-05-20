---
name: binance-trading
description: "Binance 加密货币交易助手 — 行情数据、账户管理、下单交易、组合追踪，通过 CCXT 统一 API 访问"
version: 1.0.0
category: trading
python: ">=3.11"
dependencies:
  - ccxt
---

# Binance 交易助手

> 为 Paradigme 定制的加密货币交易工具集。提供实时行情、账户管理、下单执行、盈亏追踪。

## ⚠️ 安全警告

- API 密钥存储在 `references/config.json`（**已 gitignore，不会上传**）
- 默认使用 **Binance Testnet**（`testnet: true`）
- 实盘交易前务必确认 `testnet: false`
- **永远不要泄露 `config.json` 中的密钥**

## 快速使用

```bash
# 行情总览
python scripts/market.py overview BTC/USDT ETH/USDT SOL/USDT

# 查询价格
python scripts/market.py price ETH/USDT

# K线数据
python scripts/market.py klines BTC/USDT 1h

# 账户状态
python scripts/account.py status

# 查看挂单
python scripts/order.py open

# 记录交易
python scripts/portfolio.py log ETH/USDT buy 0.5 3500 "技术突破买入"
```

## 模块

| 模块 | 功能 | API 权限 |
|------|------|---------|
| `market.py` | 价格/K线/深度/资金费率/市场总览 | 仅读取 |
| `account.py` | 余额/持仓/交易历史 | 读取 |
| `order.py` | 市价单/限价单/撤单 | **交易** |
| `portfolio.py` | 手动记账/盈亏/胜率统计 | 本地 |

## 配置

编辑 `references/config.json`：

```json
{
  "api_key": "你的Binance API Key",
  "secret_key": "你的Binance Secret Key",
  "testnet": true
}
```

获取 API Key：Binance → API Management → 创建 → 勾选"现货交易"+"读取"

## 在 Hermes 中使用

加载此 skill 后，可直接让 Hermes 通过 terminal 调用脚本获取数据：

```
"查一下ETH/BTC/SOL的当前价格"
→ python D:/Hermes file/skills/trading/binance-trading/scripts/market.py overview ETH/USDT BTC/USDT SOL/USDT
```

## 注意事项

1. Testnet API 与实盘独立，需分别创建
2. IP 白名单：当前 IP `111.44.232.56`
3. CCXT 自动处理速率限制，无需额外 throttling
4. 大额交易前建议先查 orderbook 深度
