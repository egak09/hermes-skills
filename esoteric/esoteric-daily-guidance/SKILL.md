---
name: esoteric-daily-guidance
description: "东西方玄学每日行动指南 — 八字+紫微斗数+西方星盘三合一推演，为 Paradigme 生成结构化每日建议"
version: 1.0.0
category: esoteric
python: ">=3.11"
---

# 玄学每日行动指南 (Esoteric Daily Guidance)

> 八字 + 紫微斗数 + 西方星盘 三系统综合推演。命盘数据存储在本地 `references/birth_data.json`（已 gitignore），不上传 GitHub。

## 触发条件

- 用户要求"今日运势""玄学建议""命盘分析"
- 每天 cron 定时推送
- 用户问及交易决策辅助时

## 快速使用

```bash
# 在 Hermes session 中加载此 skill 后，直接用 terminal 运行：
python "D:/Hermes file/skills/esoteric/esoteric-daily-guidance/scripts/daily_synthesis.py"
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

## 命盘数据

个人信息存储在本地 `references/birth_data.json`（已 gitignore），包含：
- 出生时间及地点
- 八字四柱
- 紫微十二宫及四化
- 西方星盘行星位置

所有命盘解读由 `daily_synthesis.py` 在本地完成，不依赖外部 API。

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

```
cronjob action=create name="玄学日报" schedule="0 10 * * *" skills=["esoteric-daily-guidance"] prompt="运行 python D:/Hermes file/skills/esoteric/esoteric-daily-guidance/scripts/daily_synthesis.py 生成今日玄学行动指南，输出结果"
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

### Python 可执行文件路径 (Windows)

在 Windows 上，git-bash 的 `python3`（MSYS2 ucrt64，`/c/msys64/ucrt64/bin/python3`）**不包含**通过 pip 安装的包（lunardate、skyfield）。必须使用系统 Python：

```bash
# ✅ 正确
"/c/Users/dairch/AppData/Local/Programs/Python/Python314/python" -B "D:/Hermes file/skills/esoteric/esoteric-daily-guidance/scripts/daily_synthesis.py"

# ❌ 错误 — ModuleNotFoundError: No module named 'lunardate'
python3 "D:/Hermes file/skills/esoteric/esoteric-daily-guidance/scripts/daily_synthesis.py"
```

使用 `-B` 标志跳过 `.pyc` 缓存，确保代码修改后立即生效。

## 架构说明

三个系统各自独立计算，由 `daily_synthesis.py` 聚合输出：
- **八字**：四柱推算 + 流日冲合 + 十神分析
- **紫微**：十二宫安星 + 14 主星 + 四化飞星
- **星盘**：行星位置 + 行运 + 相位（skyfield 精确计算或近似算法）
