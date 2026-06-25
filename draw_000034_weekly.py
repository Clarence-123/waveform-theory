import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime, timedelta
import os

with open('D:/Trading Workflow/Stock_lab_system/data/cache/daily_history/000034.json') as f:
    raw = json.load(f)

daily = []
for r in raw:
    daily.append({
        'day': r['day'], 'o': float(r['open']), 'h': float(r['high']),
        'l': float(r['low']), 'c': float(r['close']), 'v': float(r['volume']),
        'dt': datetime.strptime(r['day'], '%Y-%m-%d')
    })

# Aggregate to weekly
weekly = {}
for d in daily:
    # ISO week
    iso = d['dt'].isocalendar()
    wk = f"{iso[0]}-W{iso[1]:02d}"
    if wk not in weekly:
        weekly[wk] = {'o': d['o'], 'h': d['h'], 'l': d['l'], 'c': d['c'],
                      'v': d['v'], 'day': d['day']}
    else:
        w = weekly[wk]
        w['h'] = max(w['h'], d['h'])
        w['l'] = min(w['l'], d['l'])
        w['c'] = d['c']
        w['v'] += d['v']
        w['day'] = d['day']  # last day of week

# Convert to sorted list
wk_sorted = sorted(weekly.items())
wdata = []
for wk, v in wk_sorted:
    wdata.append({'day': v['day'], 'o': v['o'], 'h': v['h'], 'l': v['l'],
                  'c': v['c'], 'v': v['v']})

# Use data from 2024 onwards
plot_wk = [d for d in wdata if d['day'] >= '2024-01-01']
n = len(plot_wk)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(28, 18),
    gridspec_kw={'height_ratios': [3, 1]})
fig.patch.set_facecolor('#0d1117')
ax1.set_facecolor('#0d1117')
ax2.set_facecolor('#0d1117')

# ============ WEEKLY CANDLES ============
for i, d in enumerate(plot_wk):
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax1.plot([i, i], [d['l'], d['h']], color=color, linewidth=1.2)
    y1, y2 = max(d['o'], d['c']), min(d['o'], d['c'])
    ax1.bar(i, y1-y2, 0.7, bottom=y2, color=color, alpha=0.88)

closes = [d['c'] for d in plot_wk]
highs = [d['h'] for d in plot_wk]
lows = [d['l'] for d in plot_wk]
vol_wk = [d['v']/10000 for d in plot_wk]
dates = [d['day'][:10] for d in plot_wk]

# ============ MOVING AVERAGES ============
def sma_s(series, period):
    result = [0]*len(series)
    for i in range(len(series)):
        start = max(0, i-period+1)
        result[i] = sum(series[start:i+1])/min(i+1, period)
    return result

def ema(series, period):
    result = [0]*len(series)
    result[period-1] = sum(series[:period])/period
    k = 2/(period+1)
    for i in range(period, len(series)):
        result[i] = series[i]*k + result[i-1]*(1-k)
    return result

# DEMA10-weekly (approximate: 10-period on weekly)
ema10_w = ema(closes, 10)
dema10_w = ema(ema10_w, 10)

# quad-MA on weekly (14,28,57,114 periods - scaled for weekly: roughly 10,20,40,80)
ma10w = sma_s(closes, 10)
ma20w = sma_s(closes, 20)
ma40w = sma_s(closes, 40)
ma80w = sma_s(closes, 80)
quad_ma_w = [(ma10w[i]+ma20w[i]+ma40w[i]+ma80w[i])/4 for i in range(n)]

ax1.plot(range(n), dema10_w, color='white', linewidth=2, label='DEMA10-Weekly', alpha=0.9)
ax1.plot(range(n), quad_ma_w, color='#d2991d', linewidth=2, label='Quad-MA-Weekly', alpha=0.9)

# ============ WEEKLY DESCENDING CHANNEL ============
# The weekly descending channel from 2025 peak
# Find the major peak (late 2025 / early 2026)
# Looking at weekly: find highest point in recent year

# Find peak from mid-2025 onwards
peak_idx_w = None
peak_val_w = 0
for i, d in enumerate(plot_wk):
    if d['day'] >= '2025-09-01' and d['h'] > peak_val_w:
        peak_val_w = d['h']
        peak_idx_w = i

# Second lower high (after peak, before current)
sh_idx_w = None
sh_val_w = 0
for i, d in enumerate(plot_wk):
    if i > peak_idx_w and d['day'] <= '2026-05-15':
        # Find local weekly high
        if i > peak_idx_w + 3:
            is_local_high = True
            for j in range(max(peak_idx_w+1, i-3), min(n, i+4)):
                if j != i and plot_wk[j]['h'] > d['h']:
                    is_local_high = False
                    break
            if is_local_high and d['h'] > sh_val_w and d['h'] < peak_val_w * 0.95:
                sh_val_w = d['h']
                sh_idx_w = i

# If not found, use early May 2026 peak
if sh_idx_w is None:
    for i, d in enumerate(plot_wk):
        if i > peak_idx_w + 10 and d['h'] > sh_val_w and d['h'] < peak_val_w * 0.95:
            sh_val_w = d['h']
            sh_idx_w = i

# Also find pre-rally low (channel start reference)
pre_low_idx_w = None
pre_low_val_w = float('inf')
for i in range(max(0, peak_idx_w-70), peak_idx_w):
    if lows[i] < pre_low_val_w:
        pre_low_val_w = lows[i]
        pre_low_idx_w = i

# Draw weekly channel
if peak_idx_w is not None and sh_idx_w is not None:
    dx = sh_idx_w - peak_idx_w
    dy = sh_val_w - peak_val_w
    slope_w = dy / dx  # negative

    x_range = np.arange(peak_idx_w, n + 3)
    y_upper = peak_val_w + slope_w * (x_range - peak_idx_w)

    # Find max distance for lower line
    max_dist_w = 0
    low_idx_w = n-1
    for i in range(peak_idx_w, n):
        y_at_i = peak_val_w + slope_w * (i - peak_idx_w)
        dist = y_at_i - lows[i]
        if dist > max_dist_w:
            max_dist_w = dist
            low_idx_w = i

    y_lower = y_upper - max_dist_w * 0.95

    # Draw weekly channel
    ax1.plot(x_range, y_upper, color='#f85149', linewidth=2.5, linestyle='-', alpha=0.9)
    ax1.plot(x_range, y_lower, color='#f85149', linewidth=2.5, linestyle='-', alpha=0.9)
    ax1.fill_between(x_range, y_lower, y_upper, color='#f85149', alpha=0.05)

    # Annotate
    ax1.plot(peak_idx_w, peak_val_w, 'v', color='#f85149', markersize=14,
             markeredgecolor='white', markeredgewidth=2, zorder=5)
    ax1.plot(sh_idx_w, sh_val_w, 'v', color='#ff7b72', markersize=12,
             markeredgecolor='white', markeredgewidth=1.5, zorder=5)

    # Labels
    ax1.annotate(f'Major Peak\n{plot_wk[peak_idx_w]["day"]}\n{peak_val_w:.2f}',
                xy=(peak_idx_w, peak_val_w),
                xytext=(peak_idx_w-15, peak_val_w+8),
                fontsize=9, color='#f85149', fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='->', color='#f85149', lw=1.5))

    ax1.annotate(f'Lower High\n{plot_wk[sh_idx_w]["day"]}\n{sh_val_w:.2f}',
                xy=(sh_idx_w, sh_val_w),
                xytext=(sh_idx_w+3, sh_val_w+4),
                fontsize=9, color='#ff7b72', fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='->', color='#ff7b72', lw=1.5))

    # Channel stats
    # Estimate slope per week and per year
    weeks_in_channel = n - 1 - peak_idx_w
    decline_pct = (closes[-1] - peak_val_w) / peak_val_w * 100
    chan_width_w = y_upper[min(n-1, len(y_upper)-1)] - y_lower[min(n-1, len(y_lower)-1)]

    stats_w = (
        f"WEEKLY CHANNEL STATS\n"
        f"{'='*35}\n"
        f"Channel Start: {plot_wk[peak_idx_w]['day']}\n"
        f"Peak Price: {peak_val_w:.2f}\n"
        f"2nd Lower High: {plot_wk[sh_idx_w]['day']} ({sh_val_w:.2f})\n"
        f"Weeks in Channel: {weeks_in_channel}\n"
        f"Slope: {slope_w:.4f}/wk = {slope_w*52:.2f}/yr\n"
        f"Peak-to-Now Decline: {decline_pct:.1f}%\n"
        f"Current: {closes[-1]:.2f}\n"
        f"Channel Lower (now): {y_lower[min(n-1,len(y_lower)-1)]:.2f}\n"
        f"Channel Upper (now): {y_upper[min(n-1,len(y_upper)-1)]:.2f}\n"
        f"Channel Width: {chan_width_w:.2f}\n"
        f"\n"
        f"vs DAILY CHANNEL\n"
        f"{'='*35}\n"
        f"Daily channel: 5/11 peak 32.58 -> now 22.33\n"
        f"Weekly channel: captures LARGER trend\n"
        f"Weekly is the 'senior' timeframe\n"
        f"Both aligning bearish = high confidence\n"
    )

    ax1.text(0.985, 0.50, stats_w, transform=ax1.transAxes,
            fontsize=8.5, color='#c9d1d9', fontfamily='monospace',
            verticalalignment='center', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                     edgecolor='#30363d', alpha=0.92))

# ============ HORIZONTAL LEVELS ============
# Key weekly support/resistance
levels_w = [
    (22.00, '#d2991d', '--', 'Support 22.00 (weekly)'),
    (27.00, '#8b949e', ':', 'Mid 27.00'),
    (32.58, '#a371f7', '--', 'Resistance 32.58 (daily peak)'),
]
# Add pre-rally low if found
if pre_low_idx_w is not None:
    levels_w.append((pre_low_val_w, '#3fb950', '--', f'Pre-Rally Low {pre_low_val_w:.2f}'))

for price, color, style, label in levels_w:
    ax1.axhline(y=price, color=color, linestyle=style, linewidth=1.2, alpha=0.7)
    ax1.text(n-1, price, f' {label}', color=color, fontsize=8, va='center', fontweight='bold')

# ============ MARK KEY POINTS ============
# Current
ax1.annotate(f'Now\n{closes[-1]:.2f}\n{plot_wk[-1]["day"]}',
            (n-1, closes[-1]),
            textcoords='offset points', xytext=(30, -10),
            fontsize=10, color='#d2991d', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#d2991d', lw=1.8))
ax1.plot(n-1, closes[-1], 'D', color='#d2991d', markersize=10,
         markeredgecolor='white', markeredgewidth=1.5, zorder=5)

# Pre-rally low
if pre_low_idx_w is not None:
    ax1.plot(pre_low_idx_w, pre_low_val_w, 'o', color='#3fb950', markersize=10,
             markeredgecolor='white', markeredgewidth=1.5, zorder=5)
    ax1.annotate(f'Pre-Rally Low\n{pre_low_val_w:.2f}',
                xy=(pre_low_idx_w, pre_low_val_w),
                textcoords='offset points', xytext=(0, -25),
                fontsize=9, color='#3fb950', fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='->', color='#3fb950', lw=1.2))

# ============ DEATH CROSS STATUS ============
last_dema = dema10_w[-1]
last_quad = quad_ma_w[-1]
dc_text = f'Weekly DEMA10={last_dema:.2f} | Weekly QuadMA={last_quad:.2f} | {"WEEKLY DEATH CROSS!" if last_dema < last_quad else "No Weekly Death Cross"}'
ax1.text(0.02, 0.98, dc_text, transform=ax1.transAxes, fontsize=10,
         color='#f85149' if last_dema < last_quad else '#3fb950',
         fontweight='bold', va='top',
         bbox=dict(facecolor='#161b22', alpha=0.9, edgecolor='#30363d', pad=5))

# ============ VOLUME ============
colors_vol = ['#3fb950' if plot_wk[i]['c'] >= plot_wk[i]['o'] else '#f85149' for i in range(n)]
ax2.bar(range(n), vol_wk, color=colors_vol, alpha=0.7, width=0.8)
vol_ma3 = sma_s(vol_wk, 3)
ax2.plot(range(n), vol_ma3, color='#d2991d', linewidth=1.2, alpha=0.8, label='VOL MA3')

# Rising/Falling volume phases
# Mark declining volume in recent weeks
vol_decl_line = sma_s(vol_wk, 5)
ax2.plot(range(n), vol_decl_line, color='#8b949e', linewidth=0.8, alpha=0.5, linestyle=':')

# ============ STYLING ============
ax1.set_title('Shenzhou Digital (000034) WEEKLY Chart — Descending Channel Analysis',
              fontsize=15, color='white', fontweight='bold', pad=15)

tick_step = max(1, n // 14)
tick_pos = list(range(0, n, tick_step))
ax1.set_xticks(tick_pos)
ax1.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=8)
ax2.set_xticks(tick_pos)
ax2.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=8)

for ax in [ax1, ax2]:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#30363d')
    ax.spines['bottom'].set_color('#30363d')
    ax.tick_params(colors='#8b949e', labelsize=8)
    ax.grid(True, alpha=0.1, color='#8b949e')
    ax.set_axisbelow(True)

ax1.set_xlim(-2, n+3)
ax2.set_xlim(-2, n+3)
ax1.set_ylabel('Price', color='#8b949e', fontsize=11)
ax2.set_ylabel('Volume (10k)', color='#8b949e', fontsize=10)

legend_elements = [
    mpatches.Patch(color='white', alpha=0.9, label='DEMA10-Weekly (White)'),
    mpatches.Patch(color='#d2991d', alpha=0.9, label='Quad-MA-Weekly (Yellow)'),
    mpatches.Patch(color='#f85149', alpha=0.7, label='Weekly Channel Upper'),
    mpatches.Patch(color='#f85149', alpha=0.4, label='Weekly Channel Lower'),
    mpatches.Patch(color='#3fb950', alpha=0.7, label='Pre-Rally Low / Support'),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=9,
          facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')

# Save
outpath = 'D:/Trade/new_tdx64/ShenzhouDigital_000034_WeeklyChannel.png'
fig.savefig(outpath, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
plt.close()

size_kb = os.path.getsize(outpath) / 1024
print(f'OK: {outpath} ({size_kb:.0f} KB)')
print(f'Total weekly bars: {len(wdata)}')
print(f'Plotted weekly bars: {n} (from 2024)')
print(f'Weekly Peak: idx={peak_idx_w} val={peak_val_w} day={plot_wk[peak_idx_w]["day"]}')
print(f'Weekly 2nd High: idx={sh_idx_w} val={sh_val_w} day={plot_wk[sh_idx_w]["day"]}')
print(f'Weekly DEMA10={last_dema:.2f} QuadMA={last_quad:.2f}')
print(f'Weekly slope: {slope_w:.4f}/week')
