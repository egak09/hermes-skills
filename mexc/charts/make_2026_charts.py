#!/usr/bin/env python3
"""2026 币安上币策略转向 — 可视化（3张图）
数据源：币安官方公告 API 全量 2253 条（2017-07-21 → 2026-09-09）
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

rows = list(csv.DictReader(open(f'{BASE}/data/binance-announcements/classified.csv', encoding='utf-8')))
for r in rows:
    r['dt'] = datetime.datetime.strptime(r['date'], '%Y-%m-%d')
    r['ym'] = r['date'][:7]; r['year'] = r['dt'].year

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

COMMODITY = {"XAU","XAG","XPT","XPD","COPPER","CL","BZ","NATGAS","WTI","BRENT","GOLD","SILVER","HG","NG"}
INDEX = {"EWY","EWJ","SPX","NDX","US500","DAX","N225","HSI"}
def is_tradfi(title, sym):
    tl = title.lower()
    if any(k in tl for k in ["equity perpetual","index perpetual","tradfi","bstock","tokenized securit","stock"]):
        return True
    return sym in COMMODITY or sym in INDEX

SYM = re.compile(r'\(([A-Z0-9]{2,15})\)')
SKIP = {"USDT","BUSD","USDC","BTC","ETH","BNB","FDUSD","TRY","BRL","EUR","USD","DAI","TUSD"}
SPOTC = {"spot","spot_legacy","ecosystem_add","launch_event"}

seen_s, seen_f = {}, {}
spot_dates, crypto_f, tradfi_f = [], [], []
for r in sorted(rows, key=lambda x: x['dt']):
    if r['cat'] in SPOTC and not re.search(r'bStock|Tokenized Securit', r['title'], re.I):
        for s in [x for x in SYM.findall(r['title']) if x not in SKIP]:
            if s not in seen_s:
                seen_s[s] = r['dt']; spot_dates.append(r['dt'])
    elif r['cat'] == 'futures':
        for s in fut_syms(r['title']):
            if s not in seen_f:
                seen_f[s] = r['dt']
                (tradfi_f if is_tradfi(r['title'], s) else crypto_f).append(r['dt'])

months26 = [f'2026-{i:02d}' for i in range(1, 10)]
lbl = [m[-2:] + '月' for m in months26]

sp26 = [sum(1 for d in spot_dates if d.strftime('%Y-%m') == m) for m in months26]
cf26 = [sum(1 for d in crypto_f  if d.strftime('%Y-%m') == m) for m in months26]
tf_sym = [sum(1 for d in tradfi_f if d.strftime('%Y-%m') == m) for m in months26]
# Multiple 复合公告（TradFi）
tf_multi = []
for m in months26:
    tf_multi.append(sum(1 for r in rows if r['cat'] == 'futures' and r['ym'] == m
                        and 'Multiple' in r['title'] and re.search(r'Equity|TradFi', r['title'], re.I)))
tf26 = [a + b for a, b in zip(tf_sym, tf_multi)]
bstock = [sum(1 for r in rows if r['ym'] == m and re.search(r'bStock|Tokenized Securit', r['title'], re.I)) for m in months26]

# ============ 图 10：2026 月度三线堆叠 ============
fig, ax = plt.subplots(figsize=(14, 7))
xi = np.arange(len(months26))
ax.bar(xi, sp26, 0.6, color='#2E86DE', label='加密现货新币')
ax.bar(xi, cf26, 0.6, bottom=sp26, color='#EE5A24', label='加密合约新标的')
ax.bar(xi, tf26, 0.6, bottom=[a+b for a, b in zip(sp26, cf26)], color='#8E44AD', label='TradFi 合约（股票/商品/指数）')
for i in range(len(months26)):
    tot = sp26[i] + cf26[i] + tf26[i]
    ax.text(i, tot + 0.6, str(tot), ha='center', fontsize=10, fontweight='bold')
ax.axvline(0.5, color='#e74c3c', lw=2, ls='--', alpha=0.8)
ax.text(0.55, ax.get_ylim()[1]*0.92, '2026-02 策略断点', color='#e74c3c', fontsize=11.5, fontweight='bold')
ax.set_xticks(xi); ax.set_xticklabels(lbl, fontsize=11)
ax.set_ylabel('新上市标的数（个/月，按符号去重）', fontsize=12)
ax.grid(axis='y', alpha=0.25, linestyle='--')
ax.legend(fontsize=10.5, loc='upper right')
ax.set_title('2026 年币安新增标的月度拆解：加密现货 / 加密合约 / TradFi 合约\n'
             '2月起加密上币收缩，5-6月起 TradFi 合约接棒（数据：币安官方公告）', fontsize=13.5, pad=14)
plt.tight_layout(); plt.savefig(f'{OUT}/10-2026-monthly-breakdown.png', bbox_inches='tight'); plt.close()
print('✅ 10-2026-monthly-breakdown.png')

# ============ 图 11：TradFi 占比 + bStocks ============
fut_all = [sum(1 for r in rows if r['cat'] == 'futures' and r['ym'] == m) for m in months26]
tradfi_ann = []
for m in months26:
    tradfi_ann.append(sum(1 for r in rows if r['cat'] == 'futures' and r['ym'] == m
                          and re.search(r'Equity Perpetual|Index Perpetual|TradFi|XAGUSDT|XPTUSDT|XPDUSDT|COPPERUSDT|CLUSDT|BZUSDT|NATGASUSDT', r['title'], re.I)))
share = [t / f * 100 if f else 0 for t, f in zip(tradfi_ann, fut_all)]

fig, ax1 = plt.subplots(figsize=(14, 7))
ax1.bar(xi - 0.2, bstock, 0.4, color='#16A085', label='bStocks/代币化证券公告数')
ax1.set_ylabel('bStocks 公告数（条/月）', fontsize=12, color='#16A085')
ax1.set_xticks(xi); ax1.set_xticklabels(lbl, fontsize=11)
ax1.set_zorder(2); ax1.patch.set_visible(False)
ax1.grid(axis='y', alpha=0.2, linestyle='--')

ax2 = ax1.twinx()
ax2.plot(xi, share, 'o-', color='#8E44AD', lw=2.8, ms=9, label='TradFi 占合约公告比例（%）')
for i, s in enumerate(share):
    if s > 0:
        ax2.text(i, s + 2.5, f'{s:.0f}%', ha='center', fontsize=9.5, color='#8E44AD', fontweight='bold')
ax2.set_ylabel('TradFi 占合约公告比例（%）', fontsize=12, color='#8E44AD')
ax2.set_ylim(0, 75)
ax2.axvline(0.5, color='#e74c3c', lw=2, ls='--', alpha=0.8)
ax2.set_zorder(3); ax2.patch.set_visible(False)

h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=10.5)
ax1.set_title('2026 年结构切换：TradFi 合约占比从 0% → 60%，bStocks 5月起登场', fontsize=13.5, pad=14)
plt.tight_layout(); plt.savefig(f'{OUT}/11-2026-tradfi-share.png', bbox_inches='tight'); plt.close()
print('✅ 11-2026-tradfi-share.png')

# ============ 图 12：1-9 月同比（可比口径）============
years = [2023, 2024, 2025, 2026]
y_sp = [sum(1 for d in spot_dates if d.year == y and d.month <= 9) for y in years]
y_cf = [sum(1 for d in crypto_f if d.year == y and d.month <= 9) for y in years]
fig, ax = plt.subplots(figsize=(12.5, 7))
bx = np.arange(len(years))
b1 = ax.bar(bx - 0.2, y_sp, 0.4, color='#2E86DE', label='加密现货新币')
b2 = ax.bar(bx + 0.2, y_cf, 0.4, color='#EE5A24', label='加密合约新标的')
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 1.8, str(int(b.get_height())),
                ha='center', fontsize=11, fontweight='bold')
ax.set_xticks(bx); ax.set_xticklabels([f'{y} 年 1-9月' for y in years], fontsize=12)
ax.set_ylabel('新增标的数（个，剔除 TradFi 后可比口径）', fontsize=12)
ax.grid(axis='y', alpha=0.25, linestyle='--')
ax.legend(fontsize=11.5)
ax.annotate(f'现货 {y_sp[3]} vs {y_sp[2]}\n同比 -{round((1-y_sp[3]/y_sp[2])*100)}%',
            xy=(3 - 0.2, y_sp[3]), xytext=(2.3, y_sp[3] + 32), fontsize=11, color='#2E86DE',
            fontweight='bold', arrowprops=dict(arrowstyle='->', color='#2E86DE'))
ax.annotate(f'合约 {y_cf[3]} vs {y_cf[2]}\n同比 -{round((1-y_cf[3]/y_cf[2])*100)}%',
            xy=(3 + 0.2, y_cf[3]), xytext=(2.35, y_cf[3] + 55), fontsize=11, color='#EE5A24',
            fontweight='bold', arrowprops=dict(arrowstyle='->', color='#EE5A24'))
ax.set_title('可比口径同比：剔除 TradFi 后的加密上币（1-9月，2023-2026）\n'
             '2026 年加密现货新币同比 -68%，加密合约新标的同比 -53%', fontsize=13.5, pad=14)
plt.tight_layout(); plt.savefig(f'{OUT}/12-2026-yoy-comparison.png', bbox_inches='tight'); plt.close()
print('✅ 12-2026-yoy-comparison.png')

print('\n数据核对：')
print(' 2026 月度 现货:', sp26)
print(' 2026 月度 加密合约:', cf26)
print(' 2026 月度 TradFi(符号+复合):', tf26)
print(' 2026 月度 bStocks:', bstock)
print(' TradFi 占合约公告比:', [f'{s:.0f}%' for s in share])
print(' 1-9月同比 现货:', y_sp, ' 合约:', y_cf)
