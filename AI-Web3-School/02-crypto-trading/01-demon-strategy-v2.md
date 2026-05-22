# 妖币合约策略 v2.2 完整解析

> **妖币定义**: 不是 PEPE/BONK/DOGE 等 meme 币，  
> 而是 SKYAI、RAVE、M 这类**极小市值 + 高波动 + 低流动性**的币，  
> 24h 成交量仅几十万到百万美元级别，特征是短时暴涨暴跌。

---

## 1. 策略核心：68分阈值 + 1K线确认

### 为什么需要确认机制？

回测对比了三轮阈值方案：

| 方案 | 总交易 | 最佳 | 最差 | 假信号 |
|------|--------|------|------|--------|
| 78 无确认 | 4 笔 | +0.5% | -4.8% | 1 笔 |
| 68 无确认 | 11 笔 | +13.3% | -9.4% | 7 笔 |
| **68+确认 ✅** | **4 笔** | **+9.4%** | **-0.5%** | **0 笔** |

**结论: 68 + 确认 在同等交易量下，最佳收益提升 18 倍，最差亏损缩小 10 倍。**

### 确认机制流程

```
信号触发（K线 N 时刻）
    ↓
等待 K线 N+1 走完
    ├─ N+1 Close > N Close AND N+1 是阳线 → ✅ 确认开仓
    └─ 否则 → ❌ 丢弃信号
```

---

## 2. 评分架构

```
总分 = 形态分 + OI/Vol组合分 + 指标加分
触发条件 = ≥68分 AND ≥2种形态 AND 下一K线确认
```

### 四种 K 线形态

| 形态 | 分值 | 核心条件 |
|------|------|---------|
| 🚀 **火箭起飞** | 45 | 实体>8% + 量≥5线均值4x + 破20线高 + RSI<78 |
| 📈 **放量突破** | 35 | 破10线高 + 量≥20线均值3.5x + 阳线 + 连续≥2放量阳 |
| 🚩 **旗形突破** | 25 | 15-30线收敛 + 破上轨 + 量>2.5x + 不回破 |
| 🔄 **底背离反转** | 20 | RSI 底背离 + 量≥3x + 大阳确认 |

### 指标加分

| 指标 | 分值 |
|------|------|
| EMA7 ↑ EMA21 | +10 |
| MACD 金叉 | +8 |

### OI + Volume 组合评分

```
OI 1h ≥45% + OI > MA10×1.25 → 最高 70 分
Volume ≥3.8x → 40 分 / ≥2.8x → 25 分
Combo = OI×0.6 + Vol×0.4，≥55且价格突破 → 计入总分
```

---

## 3. 妖币回测结果（68+确认, 30天, 5分钟K线）

| 币种 | 交易数 | 收益 | 确认 | 拒绝 | 判定 |
|------|--------|------|------|------|------|
| FIGHT | 1 | +9.4% | 1 | 1 | ✅ |
| PLAY | 1 | +0.6% | 1 | 0 | ✅ |
| FIDA | 2 | -0.5% | 2 | 1 | ⚠️ 微亏 |
| SKYAI | 0 | — | 0 | 2 | ✅ 假信号过滤 |
| BANANAS31 | 0 | — | 0 | 1 | ✅ 假信号过滤 |
| SYS | 0 | — | 0 | 2 | ✅ 假信号过滤 |
| BROCCOLIF3B | 0 | — | 0 | 0 | — |
| PROMPT | 0 | — | 0 | 0 | — |

**8 个币中 5 个产生过信号，确认机制过滤掉了所有假信号。**

---

## 4. 代码模块

```python
signals.py   # ⭐ 形态识别 + OI/Vol + 费率检测
backtest.py  # 🔬 30天回测 + 确认机制
notify.py    # 📢 6种Telegram通知
risk.py      # 🛡️ 风控 + 仓位
executor.py  # ⚡ 分批执行 + 追踪止损
main.py      # 🎯 主控编排
```

### 快速命令

```bash
python signals.py test ARB/USDT       # 单币诊断
python backtest.py SOL/USDT           # 单币回测
python backtest.py quick              # 5币快速回测
python backtest.py batch 20           # 20币批量
```

---

## 5. 踩坑实录

### 坑1: Binance 合约 symbol 格式

```python
# ❌ 错误 — 会漏掉所有合约
sym.endswith('/USDT')

# ✅ 正确 — 合约返回 YB/USDT:USDT（不是 YB/USDT）
sym.endswith('/USDT:USDT') or sym.endswith('/USDT')
```

### 坑2: Python 环境分裂

```bash
# ❌ 错误 — MSYS2 Python 没有 ccxt
python3 main.py  # → ModuleNotFoundError

# ✅ 正确
/c/Users/dairch/AppData/Local/Programs/Python/Python314/python.exe main.py
```

### 坑3: 代理必须显式传入

```python
# ❌ scan_market() 不带config → 所有API超时
scan_market()

# ✅ 带config（含proxy字段）
scan_market(config=config_dict)
```

---

## 6. 策略演进历史

```
v1.0 — 纯形态评分，无确认 → 假信号满天飞
v2.0 — 加入 OI/Vol 组合 + 费率预警 → 过滤率提升
v2.1 — 引入凯利公式 + 风控框架
v2.2 — 1K线确认机制 → 假信号清零 ✅ 定稿
```

---

### 下一步

→ [02 · 凯利公式仓位管理](02-kelly-position.md)
