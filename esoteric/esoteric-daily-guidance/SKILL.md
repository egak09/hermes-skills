---
name: esoteric-daily-guidance
description: "东西方玄学每日行动指南 — 八字+紫微斗数+西方星盘三合一推演，为 Paradigme 生成结构化每日建议"
version: 1.0.0
category: esoteric
python: ">=3.11"
---

# 玄学每日行动指南 (Esoteric Daily Guidance)

> 为 Paradigme（2001-04-16 16:50，青海大通，男）定制的每日三系统玄学综合推演。

## 触发条件

- 用户要求"今日运势""玄学建议""命盘分析"
- 每天 cron 定时推送
- 用户问及交易决策辅助时

## 快速使用

```bash
# 在 Hermes session 中加载此 skill 后，直接用 terminal 运行：
python "D:/Hermes file/skills/esoteric-daily-guidance/scripts/daily_synthesis.py"
```

或在 Python 中：

```python
from daily_synthesis import generate_daily_report
print(generate_daily_report())
```

## 模块架构

```
scripts/
├── bazi.py           # 八字计算（四柱、日主、十神、流日冲合）
├── ziwei.py          # 紫微斗数（十二宫、14主星、四化）
├── western_astro.py  # 西方星盘（行星位置、宫位、相位、行运）
├── daily_synthesis.py # 每日综合推演引擎
references/
└── birth_data.json   # Paradigme 命盘数据
```

## 命盘概要

| 系统 | 关键信息 |
|------|---------|
| **八字** | 辛巳 壬辰 己酉 壬申 · 日主己土（阴） |
| **紫微** | 命宫午（空宫）、身宫官禄、金四局 |
| **紫微四化** | 巨门化禄、太阳化权、文曲化科、文昌化忌 |
| **星盘** | 太阳白羊、月亮水瓶、上升白羊 |

## 日主特性

**己土**：田园之土，温和包容，滋养万物。
- 优点：诚信踏实，善于积累，稳定可靠
- 注意：容易犹豫不决，需要外力推动

## 依赖

```bash
pip install lunardate skyfield
```

## 如何在 Hermes 中使用

### 方式一：直接运行

在 Hermes session 中，用 terminal 工具调用：

```
python "D:/Hermes file/skills/esoteric-daily-guidance/scripts/daily_synthesis.py"
```

### 方式二：设置 cron 每日推送

每日早晨 8:00 自动推送到 Telegram：

```
cronjob action=create name="玄学日报" schedule="0 8 * * *" skills=["esoteric-daily-guidance"] prompt="运行 python D:/Hermes file/skills/esoteric-daily-guidance/scripts/daily_synthesis.py 生成今日玄学行动指南，输出结果"
```

### 方式三：手工调用

`/skill esoteric-daily-guidance` 加载后，直接说"今天的玄学建议"即可。

## 注意事项

1. 这个是 **行动参考**，不是预言——最终决策永远在你自己
2. 节气边界（±1天）处月份可能有微小偏差
3. 紫微目前仅含14主星，未含辅星/杂曜（后续迭代）
4. 星盘 ASC/MC 为简化计算，精确度 ±2°
5. 首次运行 `western_astro.py` 会下载 `de421.bsp` 星历文件（~10MB），后续缓存

## 已知陷阱

### 月柱节气跨年边界

`_solar_month()` 中 month 12（小寒 1/5 → 丑月）会错误覆盖同年后4-11月的判定。详见 `references/solar-terms.md`。

**症状**：非冬季出生者月柱显示为 丑月。  
**修复**：将节气月分为「立春前→丑月」和「立春后→遍历1-11月」两个互斥区间。已在 `scripts/bazi.py` 中修正。

## 交易者特别说明

- 日主己土，土主信，交易风格天然倾向于稳健积累
- 申时（15:00-17:00）为日支酉的"劫"，此时段可能有波动
- 月柱壬辰正财透出，理财能力先天较强
- 配合 Polymarket/情绪指标等数据维度使用效果更佳
