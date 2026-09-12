#!/usr/bin/env python3
"""稳定币资金流可视化 — 三张图（2020-2026 分阶段）"""
import json, datetime, csv, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import numpy as np

# 中文字体
font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 130

OUT = '/home/ubuntu/hermes-skills/mexc/charts'
os.makedirs(OUT, exist_ok=True)

# ---- 读数据 ----
rows = []
with open('/home/ubuntu/hermes-skills/mexc/data/stablecoin-marketcap-daily-2017-2026.csv') as f:
    for r in csv.DictReader(f):
        d = datetime.date.fromisoformat(r['date'])
        rows.append((d, float(r['total_stablecoin_usd'])))
rows.sort()

dates = [r[0] for r in rows]
vals = np.array([r[1] for r in rows]) / 1e9  # B USD

DARK = '#0f1419'
GREEN = '#16c784'
RED = '#ea3943'
GOLD = '#f0b90b'
BLUE = '#3861fb'
plt.style.use('dark_background')

# ============ 图 1：稳定币总市值长期曲线 ============
fig, ax = plt.subplots(figsize=(14, 7), facecolor=DARK)
ax.set_facecolor(DARK)
ax.plot(dates, vals, color=GOLD, linewidth=2.2, label='稳定币总市值')
ax.fill_between(dates, vals, alpha=0.13, color=GOLD)

peak_date, peak_val = max(zip(dates, vals), key=lambda x: x[1])
ax.axhline(peak_val, color=BLUE, linestyle='--', linewidth=1, alpha=0.7)
ax.annotate(f'历史峰值\n{peak_date}\n${peak_val:.1f}B', xy=(peak_date, peak_val),
            xytext=(-150, -70), textcoords='offset points', color=BLUE, fontsize=9,
            arrowprops=dict(arrowstyle='->', color=BLUE, lw=1))

events = [
    ('2022-05-12', 'LUNA崩盘\n单日-15.96B', RED, 40),
    ('2022-11-10', 'FTX暴雷', RED, -60),
    ('2024-01-11', 'BTC现货ETF通过', GREEN, 55),
    ('2024-11-06', '特朗普当选', GREEN, 90),
    ('2025-10-11', '1011崩盘', RED, 60),
    ('2026-05-17', '峰值322B', GOLD, 30),
]
for ds, label, color, offset in events:
    dt = datetime.date.fromisoformat(ds)
    if dt < dates[0] or dt > dates[-1]:
        continue
    y = vals[dates.index(min(dates, key=lambda x: abs((x - dt).days)))]
    ax.annotate(label, xy=(dt, y), xytext=(0, offset), textcoords='offset points',
                color=color, fontsize=8.5, ha='center',
                arrowprops=dict(arrowstyle='-', color=color, lw=0.8, alpha=0.6))

ax.set_title('稳定币总市值走势 2017-2026（资金面总闸门）', fontsize=15, color='white', pad=15)
ax.set_ylabel('市值（十亿美元）', fontsize=11)
ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.grid(alpha=0.15, linestyle=':')
ax.legend(loc='upper left', fontsize=10, facecolor=DARK, edgecolor='#333')
plt.tight_layout()
p1 = f'{OUT}/01-stablecoin-marketcap-2017-2026.png'
plt.savefig(p1, facecolor=DARK, bbox_inches='tight')
plt.close()
print('✅', p1)

# ============ 图 2：30日滚动日均净流入 + 四档阈值 ============
# 只取 2020 以后
idx2020 = next(i for i, d in enumerate(dates) if d.year >= 2020)
d2 = dates[idx2020:]
v2 = vals[idx2020:]
daily = np.diff(v2) * 1000  # M USD
# 30日滚动平均
win = 30
roll = np.convolve(daily, np.ones(win) / win, mode='valid')
roll_dates = d2[win:]

fig, ax = plt.subplots(figsize=(14, 7), facecolor=DARK)
ax.set_facecolor(DARK)
ax.plot(roll_dates, roll, color=GOLD, linewidth=2, label='30日滚动日均净流入')
ax.fill_between(roll_dates, roll, 0, where=(roll >= 0), color=GREEN, alpha=0.25, interpolate=True)
ax.fill_between(roll_dates, roll, 0, where=(roll < 0), color=RED, alpha=0.3, interpolate=True)

# 阈值线
for lvl, name, color in [(400, 'S级 >400M（主预算开包）', GREEN),
                          (200, 'A级 200-400M', '#5ac18e'),
                          (80, 'B级 80-200M', GOLD),
                          (0, 'C级 0-80M / D级 <0', RED)]:
    ax.axhline(lvl, color=color, linestyle='--', linewidth=1, alpha=0.65)
    ax.text(roll_dates[3], lvl + 12, name, color=color, fontsize=8.5,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=DARK, edgecolor='none', alpha=0.75))

# 当前值标注
cur = roll[-1]
ax.scatter([roll_dates[-1]], [cur], color=GOLD, s=90, zorder=5, edgecolors='white', linewidths=1.2)
ax.annotate(f'当前 {cur:+.0f}M/天\n（C级·观察档）', xy=(roll_dates[-1], cur),
            xytext=(-190, 30), textcoords='offset points', color=GOLD, fontsize=10,
            arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.2))

ax.set_title('稳定币日均净流入（30日滚动）与 MEXC 活动开包阈值 2020-2026',
             fontsize=14.5, color='white', pad=15)
ax.set_ylabel('日均净流入（百万美元）', fontsize=11)
ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.grid(alpha=0.15, linestyle=':')
ax.legend(loc='lower left', fontsize=10, facecolor=DARK, edgecolor='#333')
plt.tight_layout()
p2 = f'{OUT}/02-rolling-inflow-thresholds.png'
plt.savefig(p2, facecolor=DARK, bbox_inches='tight')
plt.close()
print('✅', p2)

# ============ 图 3：分阶段日均净流入柱状图 ============
phases = [
    ("2020.03\n疫情崩盘", "2020-03-01", "2020-03-31"),
    ("2020.04-10\n牛初", "2020-04-01", "2020-10-31"),
    ("2020.11-21.04\n主升浪", "2020-11-01", "2021-04-30"),
    ("2021.05-07\n中继(519)", "2021-05-01", "2021-07-31"),
    ("2021.08-11\n牛末", "2021-08-01", "2021-11-30"),
    ("2021.12-22.06\n熊初", "2021-12-01", "2022-06-30"),
    ("2022.07-11\n熊中继FTX", "2022-07-01", "2022-11-30"),
    ("2022.12-23.09\n熊末", "2022-12-01", "2023-09-30"),
    ("2023.10-24.03\n牛初ETF", "2023-10-01", "2024-03-31"),
    ("2024.04-10\n牛中期", "2024-04-01", "2024-10-31"),
    ("2024.11-25.01\n主升", "2024-11-01", "2025-01-31"),
    ("2025.02-10\n高位/1011", "2025-02-01", "2025-10-31"),
    ("2025.11-\n当前", "2025-11-01", "2026-09-12"),
]

def val_on(target, rows):
    best = None
    for dt, v in rows:
        if dt <= target:
            best = (dt, v)
        else:
            break
    return best

labels, avg = [], []
for name, s, e in phases:
    sd, ed = datetime.date.fromisoformat(s), datetime.date.fromisoformat(e)
    a, b = val_on(sd, rows), val_on(ed, rows)
    if not a or not b:
        continue
    days = (b[0] - a[0]).days or 1
    labels.append(name)
    avg.append((b[1] - a[1]) / days / 1e6)

colors = [GREEN if x >= 200 else (GOLD if x >= 80 else (BLUE if x >= 0 else RED)) for x in avg]

fig, ax = plt.subplots(figsize=(15, 7.5), facecolor=DARK)
ax.set_facecolor(DARK)
bars = ax.bar(range(len(labels)), avg, color=colors, alpha=0.85, width=0.68)
for i, (b, v) in enumerate(zip(bars, avg)):
    ax.text(b.get_x() + b.get_width() / 2, v + (14 if v >= 0 else -32),
            f'{v:+.0f}', ha='center', color='white', fontsize=9.5, fontweight='bold')

ax.axhline(0, color='white', linewidth=1, alpha=0.5)
ax.axhline(400, color=GREEN, linestyle='--', linewidth=1, alpha=0.5)
ax.axhline(-80, color=RED, linestyle='--', linewidth=1, alpha=0.5)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_title('各市场阶段稳定币日均净流入（百万美元/天）— 2020-2026',
             fontsize=14.5, color='white', pad=15)
ax.set_ylabel('日均净流入（百万美元）', fontsize=11)
ax.grid(alpha=0.12, axis='y', linestyle=':')
ax.text(len(labels) - 1, 420, 'S级线 +400M', color=GREEN, fontsize=8.5, ha='right')
ax.text(len(labels) - 1, -105, 'D级线（净流出）', color=RED, fontsize=8.5, ha='right')
plt.tight_layout()
p3 = f'{OUT}/03-phase-inflow-bars.png'
plt.savefig(p3, facecolor=DARK, bbox_inches='tight')
plt.close()
print('✅', p3)

# ============ 图 4：组合图（季度热力/双轴） ============
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), facecolor=DARK,
                                gridspec_kw={'height_ratios': [1.35, 1]})
for a in (ax1, ax2):
    a.set_facecolor(DARK)

ax1.plot(dates[idx2020:], v2, color=GOLD, linewidth=2)
ax1.fill_between(dates[idx2020:], v2, alpha=0.12, color=GOLD)
ax1.set_title('稳定币总市值 vs 日均净流入（2020-2026）', fontsize=14, color='white', pad=12)
ax1.set_ylabel('市值（十亿美元）', fontsize=10.5)
ax1.grid(alpha=0.13, linestyle=':')

ax2.plot(roll_dates, roll, color=BLUE, linewidth=1.6)
ax2.fill_between(roll_dates, roll, 0, where=(roll >= 0), color=GREEN, alpha=0.3, interpolate=True)
ax2.fill_between(roll_dates, roll, 0, where=(roll < 0), color=RED, alpha=0.35, interpolate=True)
ax2.axhline(0, color='white', linewidth=0.9, alpha=0.6)
ax2.set_ylabel('30日滚动净流入（M/天）', fontsize=10.5)
ax2.xaxis.set_major_locator(mdates.YearLocator(1))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.grid(alpha=0.13, linestyle=':')

for a in (ax1, ax2):
    for dt_s, lab, c in [('2022-05-12', 'LUNA', RED), ('2024-01-11', 'ETF', GREEN),
                          ('2025-10-11', '1011', RED)]:
        dt = datetime.date.fromisoformat(dt_s)
        a.axvline(dt, color=c, linestyle=':', linewidth=1, alpha=0.6)

plt.tight_layout()
p4 = f'{OUT}/04-combined-marketcap-and-inflow.png'
plt.savefig(p4, facecolor=DARK, bbox_inches='tight')
plt.close()
print('✅', p4)

print('\n全部图表生成完毕')
