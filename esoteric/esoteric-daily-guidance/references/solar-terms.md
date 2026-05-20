# 八字月柱节气边界陷阱

## 问题

`_solar_month()` 函数在计算月柱时，month 12（小寒/丑月，1月5日起）的判定会错误覆盖同年后4-11月的月份。

### 根因

节气年循环中，丑月（month 12）始于1月5日（小寒），结束于2月4日（立春）。对于2月4日之后的日期，丑月属于**上一个**节气年周期，不应匹配。

原实现遍历 month 1→12，检查 "birth_date >= month_start"，导致 4/16 这样的日期先匹配到 month 3（清明→立夏），后被 month 12（小寒 1/5）覆盖。

### 修复方案

将节气月分为两个互斥区间：
1. **立春（2/4）之前** → 直接返回 month 12（丑月）
2. **立春之后** → 用 "出生日期 < 下一月节气开始日" 的判定逻辑，只遍历 month 1→11

```python
def _solar_month(birth_month: int, birth_day: int) -> int:
    # 立春前 → 丑月
    if birth_month < 2 or (birth_month == 2 and birth_day < 4):
        return 12

    # 立春后 → 按 "before next term" 判定
    month_bounds = [
        (1, 3, 5),    # 寅月: 立春 2/4 → 惊蛰 3/5
        (2, 4, 5),    # 卯月
        (3, 5, 5),    # 辰月
        # ... etc
    ]
    for m, next_m, next_d in month_bounds:
        if birth_month < next_m or (birth_month == next_m and birth_day < next_d):
            return m
    return 12
```

### 验证

- 2001-04-16 → 辰月（month 3）✅ 月柱 壬辰
- 2001-01-15 → 丑月（month 12）✅ 因在立春前
- 2001-02-20 → 寅月（month 1）✅ 因在立春后、惊蛰前

## 注意事项

- 节气日期每年有 ±1天 浮动（取决于太阳黄经精确计算），当前使用固定日期表适用于 2001 年
- 如需跨年精度，应使用 ephemeris 库（如 skyfield）精确计算节气时刻
