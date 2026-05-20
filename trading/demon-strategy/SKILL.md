---
name: demon-strategy
description: "妖币合约策略 v2.1 — K线形态 + OI/Volume精确评分 + 资金费率，≥78分自动触发"
version: 2.1.0
category: trading
python: ">=3.11"
dependencies:
  - ccxt
  - numpy
  - pandas
  - ta  # see references/ta-library-notes.md for setup quirks
---

# 妖币合约策略 v2.1 (Demon Strategy)

> 4 种 K 线形态精确识别 × OI+Volume 组合强度 × 资金费率预警。每 3 分钟扫描 Top 200 山寨币，≥78 分自动触发。

## 评分架构

```
总分 = 形态分 + OI/Vol组合分(条件) + 指标加分
       ───────   ──────────────────  ─────────
       0~125     0~58 (≥55+突破)     0~18
```

### 一、K 线形态识别（条件：≥2 种命中）

| 形态 | 分值 | 核心条件 |
|------|------|---------|
| 🚀 火箭起飞 | **45** | 实体>8% + 量≥5线均值4x + 破20线高 + RSI<78 |
| 📈 放量突破 | **35** | 破10线高 + 量≥20线均值3.5x + 阳线 + 连续≥2放量阳 |
| 🚩 旗形突破 | **25** | 15-30线收敛 + 破上轨 + 量>2.5x + 不回破 |
| 🔄 底背离反转 | **20** | RSI底背离(价新低RSI新高) + 量≥3x + 大阳确认 |

### 二、OI + Volume 组合强度

**OI 暴增公式：**
```
oi_change_1h = (oi_current - oi_1h_ago) / oi_1h_ago × 100
oi_ma10 = average of last 10 OI readings

IF oi_change_1h ≥ 45% AND oi_current > oi_ma10 × 1.25:
    oi_score = 40 + min((oi_change_1h - 45) × 0.8, 30)  → 最高 70
```

**Volume 暴增公式：**
```
vol_ratio = vol_current / vol_ma20
IF vol_ratio ≥ 3.8: vol_score = 40
ELIF vol_ratio ≥ 2.8: vol_score = 25
ELSE: vol_score = 0
```

**组合评分：**
```
combo = oi_score × 0.6 + vol_score × 0.4
IF combo ≥ 55 AND has_price_breakout:
    总分 += combo
```

推荐阈值：OI 1h 增幅 ≥ 45% + Volume ≥ 3.5x → 最高优先级

### 三、指标加分

| 指标 | 分值 |
|------|------|
| EMA7↑EMA21 金叉 | +10 |
| MACD 金叉 | +8 |

### 四、否决/预警

| 条件 | 动作 |
|------|------|
| 资金费率 \|rate\| > 0.1% | 跳过 |
| 资金费率 \|rate\| > 0.075% | 预警（多头/空头拥挤） |
| BTC/ETH | 黑名单 |
| 形态 < 2 种 | 不触发 |

## 风控系统

| 规则 | 参数 |
|------|------|
| 单笔风险 | ≤5% 本金 |
| 日亏损上限 | ≥18% → 停交易 |
| 最大持仓 | 3 个 |
| 杠杆 | 动态 1-20x |
| 冷却 | 止损后 30 分钟 |

## 模块

| 模块 | 功能 |
|------|------|
| `signals.py` | 形态识别 + OI/Vol 组合 + 费率检测 ⭐ |
| `risk.py` | 风控 + 仓位计算 🛡️ |
| `executor.py` | 分批执行 + 追踪止损 ⚡ |
| `notify.py` | 6种Telegram通知模板 + Bot API发送 📢 |
| `main.py` | 主控编排 🎯 |

## 通知系统 (notify.py)

6 种通知模板，通过 Telegram Bot API 发送：

| 模板 | 触发时机 |
|------|---------|
| 🚀 开仓 | 全自动开仓时 |
| ➕ 加仓 | 追加仓位时 |
| ✅ 止盈 | 部分/全部止盈时 |
| 🛑 止损 | 止损/全平时 |
| 📊 日报 | 每日定时总结 |
| 🚨 报警 | 异常立即推送 |

**首次配置：**
```bash
# 设置通知 (只需一次)
python notify.py setup <bot_token> <chat_id>

# 测试
python notify.py test

# 查看状态
python notify.py status
```

配置文件 `references/notify_config.json`（已 gitignore，不上传 GitHub）。

## 快速使用

```bash
# 单币完整诊断
python signals.py test ARB/USDT

# 单币全 JSON
python signals.py diagnose ARB/USDT

# 全市场扫描 (30 个币)
python signals.py scan 30

# 查看风控
python main.py risk
```

## 待完成

- [ ] 30 天历史回测
- [ ] WebSocket 实时监控
- [ ] 自动开仓（需确认）
- [ ] 每日 cron 推送
