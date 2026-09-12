#!/usr/bin/env python3
"""币安上币频率 × 稳定币资金流 — 可视化（2020-2026）
数据来源：币安官方公告 API（catalogId=48，2253条，2017-07-21→2026-09-09）+ DefiLlama 稳定币市值
"""
import csv, re, os, datetime, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

font_manager.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 130

BASE = '/home/ubuntu/hermes-skills/mexc'
OUT = f'{BASE}/charts'
os.makedirs(OUT, exist_ok=True)

# ============ 读公告并构造去重上币事件 ============
rows = list(csv.DictReader(open(f'{BASE}/data/binance-announcements/classified.csv', encoding='utf-8')))
for r in rows:
    r['dt'] = datetime.datetime.strptime(r['date'], '%Y-%m-%d')
    r['year'] = int(r['year'])

MARKERS = ["USDⓈ-M ", "USDⓈ-Margined ", "USDT-Margined ", "BUSD-Margined ", "Coin-Margined "]
def fut_syms(t):
    if "Quarterly" in t: return []
    o = [m.group(1) for m in re.finditer(r'\b([A-Z0-9]{2,15})/USDT\b', t)]
    if o: return list(dict.fromkeys(o))
    o = [m.group(1) for m in re.finditer(r'\b([A-Z0-9]{2,15}) USDT-Margined\b', t)]
    if o: return list(dict.fromkeys(o))
    seg = None
    for mk in MARKERS:
        if mk in t: seg = t.split(mk, 1)[1]; break
    if seg is None: return []
    seg = re.split(r'Perpetual|Contracts?\b', seg)[0]
    for p in re.split(r'[,、&]| and ', seg):
        p = p.strip(' .()')
        if not p or len(p) > 30: continue
        p = re.sub(r'USDT$', '', p).strip()
        if re.fullmatch(r'[A-Z0-9]{2,15}', p): o.append(p)
    return list(dict.fromkeys(o))

SYM = re.compile(r'\(([A-Z0-9]{2,15})\)')
SKIP = {"USDT","BUSD","USDC","BTC","ETH","BNB","FDUSD","TRY","BRL","EUR","USD","DAI","TUSD"}
SPOTC = {"spot", "spot_legacy", "ecosystem_add", "launch_event"}

seen_s, seen_f = {}, {}
spot_dates, fut_dates = [], []
for r in sorted(rows, key=lambda x: x['dt']):
    if r['cat'] in SPOTC:
        for s in [x for x in SYM.findall(r['title']) if x not in SKIP]:
            if s not in seen_s:
                seen_s[s] = r['dt']; spot_dates.append(r['dt'])
    elif r['cat'] == 'futures':
        for s in fut_syms(r['title']):
            if s not in seen_f:
                seen_f[s] = r['dt']; fut_dates.append(r['dt'])

# ============ 稳定币 ============
daily = []
for d in csv.DictReader(open(f'{BASE}/data/stablecoin-marketcap-daily-2017-2026.csv', encoding='utf-8')):
    try: v = float(d['total_stablecoin_usd'])
    except Exception: continue
    daily.append((datetime.datetime.strptime(d['date'], '%Y-%m-%d'), v))

mflow = collections.OrderedDict()
for d, v in daily:
    if d.year < 2020: continue
    mflow.setdefault(d.strftime('%Y-%m'), []).append(v)
months = list(mflow.keys())
flow = [(mflow[k][-1] - mflow[k][0]) / 1e9 for k in months]        # B USD / 月
m_spot = collections.Counter(d.strftime('%Y-%m') for d in spot_dates)
m_fut  = collections.Counter(d.strftime('%Y-%m') for d in fut_dates)

x = [datetime.datetime.strptime(m + '-01', '%Y-%m-%d') for m in months]
spv = [m_spot.get(m, 0) for m in months]
fuv = [m_fut.get(m, 0) for m in months]

PHASES = [
 ("疫情崩盘", "2020-03", "2020-03"), ("牛市初期", "2020-04", "2020-10"),
 ("牛市主升浪", "2020-11", "2021-04"), ("牛市中继519", "2021-05", "2021-07"),
 ("牛市末期", "2021-08", "2021-11"), ("熊市初段", "2021-12", "2022-06"),
 ("熊市中继FTX", "2022-07", "2022-11"), ("熊市末期", "2022-12", "2023-09"),
 ("牛市初期2", "2023-10", "2024-03"), ("牛市中期", "2024-04", "2024-10"),
 ("牛市主升", "2024-11", "2025-01"), ("高位震荡", "2025-02", "2025-10"),
 ("结构分化", "2025-11", "2026-09"),
]

# ================= 图 5：月度双轴 =================
fig, ax1 = plt.subplots(figsize=(15, 7))
w = 22
ax1.bar(x, spv, width=w, color='#2E86DE', label='现货新币数（去重）')
ax1.bar(x, fuv, width=w, bottom=spv, color='#EE5A24', label='合约新币数（去重）')
ax1.set_ylabel('币安上币数量（个/月）', fontsize=12, color='#333')
ax1.set_xlabel('')
ax1.grid(axis='y', alpha=0.25, linestyle='--')
ax1.set_zorder(2); ax1.patch.set_visible(False)

ax2 = ax1.twinx()
ax2.plot(x, flow, color='#10AC84', lw=2.4, marker='o', ms=3, label='稳定币月度净变化（十亿美元）')
ax2.axhline(0, color='#888', lw=1, ls=':')
ax2.set_ylabel('稳定币月度净流入（十亿美元）', fontsize=12, color='#10AC84')
ax2.set_zorder(1)

for name, a, b in PHASES:
    s = datetime.datetime.strptime(a + '-01', '%Y-%m-%d')
    e = datetime.datetime.strptime(b + '-01', '%Y-%m-%d') + datetime.timedelta(days=28)
    ax1.axvspan(s, e, alpha=0.05, color='gray')
    ax1.text(s + (e - s) / 2, ax1.get_ylim()[1] * 0.94, name, ha='center', fontsize=7.5, rotation=0, color='#555')

h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=10, framealpha=0.9)
ax1.set_title('币安上币频率 × 稳定币资金流（月度，2020-2026）\n数据源：币安官方公告API 2253条 + DefiLlama', fontsize=14, pad=14)
fig.autofmt_xdate()
plt.tight_layout(); plt.savefig(f'{OUT}/05-monthly-listings-vs-flow.png', bbox_inches='tight'); plt.close()
print('✅ 05-monthly-listings-vs-flow.png')

# ================= 图 6：阶段对比 =================
def phase_stats(a, b):
    A = datetime.datetime.strptime(a + '-01', '%Y-%m-%d')
    B = datetime.datetime.strptime(b + '-01', '%Y-%m-%d')
    B = (B.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
    days = (B - A).days + 1
    s = sum(1 for d in spot_dates if A <= d <= B)
    f = sum(1 for d in fut_dates if A <= d <= B)
    vals = [v for d, v in daily if A <= d <= B]
    avg = (vals[-1] - vals[0]) / days if vals else 0
    return s / days * 30.4, f / days * 30.4, avg / 1e6, days

pnames, pspot, pfut, pflow = [], [], [], []
for n, a, b in PHASES:
    s, f, fl, _ = phase_stats(a, b)
    pnames.append(n); pspot.append(s); pfut.append(f); pflow.append(fl)

fig, ax1 = plt.subplots(figsize=(15, 7))
xi = np.arange(len(pnames))
ax1.bar(xi, pspot, 0.62, color='#2E86DE', label='现货新币（个/月）')
ax1.bar(xi, pfut, 0.62, bottom=pspot, color='#EE5A24', label='合约新币（个/月）')
ax1.set_xticks(xi); ax1.set_xticklabels(pnames, rotation=35, ha='right', fontsize=10)
ax1.set_ylabel('上币频率（个/月）', fontsize=12)
ax1.grid(axis='y', alpha=0.25, linestyle='--')
for i, (s, f) in enumerate(zip(pspot, pfut)):
    ax1.text(i, s + f + 0.4, f'{s+f:.1f}', ha='center', fontsize=9, fontweight='bold')

ax2 = ax1.twinx()
ax2.plot(xi, pflow, color='#10AC84', lw=2.6, marker='D', ms=8, label='稳定币日均净流入（百万美元）')
ax2.axhline(0, color='#888', lw=1, ls=':')
ax2.set_ylabel('稳定币日均净流入（百万美元）', fontsize=12, color='#10AC84')

h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=10.5)
ax1.set_title('各市场阶段：币安上币频率 vs 稳定币资金流向（2020-2026）', fontsize=14, pad=14)
plt.tight_layout(); plt.savefig(f'{OUT}/06-phase-listing-vs-flow.png', bbox_inches='tight'); plt.close()
print('✅ 06-phase-listing-vs-flow.png')

# ================= 图 7：领先滞后相关性 =================
def corr(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
    dx = sum((a-mx)**2 for a in xs)**.5; dy = sum((b-my)**2 for b in ys)**.5
    return num/(dx*dy) if dx and dy else 0

lags = list(range(-6, 7))
r_spot, r_fut = [], []
for lag in lags:
    xs, us, ys = [], [], []
    for i, k in enumerate(months):
        j = i + lag
        if 0 <= j < len(months):
            xs.append(m_spot.get(k, 0)); us.append(m_fut.get(k, 0)); ys.append(flow[j])
    r_spot.append(corr(xs, ys)); r_fut.append(corr(us, ys))

fig, ax = plt.subplots(figsize=(12, 6.5))
ax.plot(lags, r_spot, 'o-', color='#2E86DE', lw=2.6, ms=8, label='现货上币 vs 资金流')
ax.plot(lags, r_fut, 's-', color='#EE5A24', lw=2.6, ms=8, label='合约上线 vs 资金流')
ax.axhline(0, color='#888', lw=1, ls=':')
ax.axvline(0, color='#ccc', lw=1, ls='--')
ax.set_xlabel('滞后阶数（月）  正=上币领先资金  负=资金领先上币', fontsize=12)
ax.set_ylabel('皮尔逊相关系数 r', fontsize=12)
ax.grid(alpha=0.25, linestyle='--')
ax.annotate(f'现货峰值 r={max(r_spot):.3f}\n(资金领先1个月)', xy=(-1, max(r_spot)),
            xytext=(-4.6, max(r_spot) - 0.05), fontsize=10, color='#2E86DE',
            arrowprops=dict(arrowstyle='->', color='#2E86DE'))
ax.annotate(f'合约最高仅 r={max(r_fut):.3f}\n(与资金弱相关)', xy=(3, max(r_fut)),
            xytext=(1.2, max(r_fut) + 0.06), fontsize=10, color='#EE5A24',
            arrowprops=dict(arrowstyle='->', color='#EE5A24'))
ax.legend(fontsize=11.5)
ax.set_title('币安上币节奏与稳定币资金流的领先/滞后相关性（月度，2020-2026）', fontsize=14, pad=14)
plt.tight_layout(); plt.savefig(f'{OUT}/07-lead-lag-correlation.png', bbox_inches='tight'); plt.close()
print('✅ 07-lead-lag-correlation.png')

# ================= 图 8：年度 =================
years = list(range(2017, 2027))
ys_spot = [sum(1 for d in spot_dates if d.year == y) for y in years]
ys_fut = [sum(1 for d in fut_dates if d.year == y) for y in years]
fig, ax = plt.subplots(figsize=(13, 6.5))
bx = np.arange(len(years))
ax.bar(bx - 0.2, ys_spot, 0.4, color='#2E86DE', label='现货新币（去重）')
ax.bar(bx + 0.2, ys_fut, 0.4, color='#EE5A24', label='合约新币（去重）')
for i, (s, f) in enumerate(zip(ys_spot, ys_fut)):
    ax.text(i - 0.2, s + 1.5, str(s), ha='center', fontsize=9.5)
    ax.text(i + 0.2, f + 1.5, str(f), ha='center', fontsize=9.5)
ax.set_xticks(bx); ax.set_xticklabels([f'{y}' + ('\n(至9月)' if y == 2026 else '') for y in years], fontsize=11)
ax.set_ylabel('上币数量（个/年）', fontsize=12)
ax.grid(axis='y', alpha=0.25, linestyle='--')
ax.legend(fontsize=11.5)
ax.set_title('币安历年上币数量：现货 vs 合约（2017-2026，官方公告去重口径）', fontsize=14, pad=14)
plt.tight_layout(); plt.savefig(f'{OUT}/08-yearly-listings-2017-2026.png', bbox_inches='tight'); plt.close()
print('✅ 08-yearly-listings-2017-2026.png')

# ================= 图 9：最近 14 个月放大 =================
last = months[-14:]
lx = [datetime.datetime.strptime(m + '-01', '%Y-%m-%d') for m in last]
lsp = [m_spot.get(m, 0) for m in last]
lfu = [m_fut.get(m, 0) for m in last]
lfl = [(mflow[m][-1] - mflow[m][0]) / 1e9 for m in last]

fig, ax1 = plt.subplots(figsize=(14, 7))
ax1.bar(lx, lsp, width=18, color='#2E86DE', label='现货新币')
ax1.bar(lx, lfu, width=18, bottom=lsp, color='#EE5A24', label='合约新币')
for i, (s, f) in enumerate(zip(lsp, lfu)):
    ax1.text(lx[i], s + f + 0.5, f'{s+f}', ha='center', fontsize=10, fontweight='bold')
ax1.set_ylabel('上币数量（个/月）', fontsize=12)
ax1.grid(axis='y', alpha=0.25, linestyle='--')
ax1.set_zorder(2); ax1.patch.set_visible(False)

ax2 = ax1.twinx()
ax2.bar(lx, lfl, width=9, color='#10AC84', alpha=0.45, label='稳定币月度净变化（B）')
ax2.axhline(0, color='#666', lw=1, ls=':')
ax2.set_ylabel('稳定币月度净变化（十亿美元）', fontsize=12, color='#10AC84')
ax2.set_zorder(1)

h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=10.5, framealpha=0.9)
ax1.set_title('当前放大：最近 14 个月 上币频率 vs 资金流向（2025.08-2026.09）\n2026Q3 上币降至 5.6 个/月，低于熊市末期基准（7.2）', fontsize=13.5, pad=14)
fig.autofmt_xdate()
plt.tight_layout(); plt.savefig(f'{OUT}/09-recent-14-months.png', bbox_inches='tight'); plt.close()
print('✅ 09-recent-14-months.png')

# 输出年度数字供报告引用
print('\n年度：')
for y, s, f in zip(years, ys_spot, ys_fut):
    print(f'  {y}: 现货 {s:3d} | 合约 {f:3d}')
