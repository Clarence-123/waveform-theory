import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# Load data
with open('D:/Trading Workflow/Stock_lab_system/data/cache/daily_history/000034.json') as f:
    raw = json.load(f)

data = []
for r in raw:
    data.append({
        'day': r['day'], 'o': float(r['open']), 'h': float(r['high']),
        'l': float(r['low']), 'c': float(r['close']), 'v': float(r['volume'])
    })

# Use data from 2026-03-01 onwards for channel analysis
plot_data = [d for d in data if d['day'] >= '2026-03-01']
n = len(plot_data)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(28, 18),
    gridspec_kw={'height_ratios': [3, 1]})
fig.patch.set_facecolor('#0d1117')
ax1.set_facecolor('#0d1117')
ax2.set_facecolor('#0d1117')

# ============ CANDLE CHART ============
for i, d in enumerate(plot_data):
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax1.plot([i, i], [d['l'], d['h']], color=color, linewidth=0.8)
    y1, y2 = max(d['o'], d['c']), min(d['o'], d['c'])
    ax1.bar(i, y1-y2, 0.75, bottom=y2, color=color, alpha=0.88)

# ============ DESCENDING CHANNEL DETECTION ============
# The descending channel from May peak to current
# Upper line: connecting declining highs
# Lower line: parallel, through declining lows

highs = [d['h'] for d in plot_data]
lows = [d['l'] for d in plot_data]
closes = [d['c'] for d in plot_data]
dates = [d['day'][5:] for d in plot_data]

# Find channel key points
# Peak area: early May (5/7-5/11-5/13)
# Find the peak index
peak_idx = None
peak_val = 0
for i, d in enumerate(plot_data):
    if d['day'] >= '2026-05-06' and d['day'] <= '2026-05-13':
        if d['h'] > peak_val:
            peak_val = d['h']
            peak_idx = i

# Secondary high (lower): late May / early June
# Find the next lower high after the peak
second_high_idx = None
second_high_val = 0
for i, d in enumerate(plot_data):
    if i > peak_idx and d['day'] <= '2026-06-05':
        # Look for local highs (surrounded by lower highs)
        if i > 0 and i < len(plot_data)-1:
            if d['h'] > plot_data[i-1]['h'] and d['h'] > plot_data[i+1]['h']:
                if d['h'] > second_high_val and d['h'] < peak_val * 0.95:
                    second_high_val = d['h']
                    second_high_idx = i

# If no clear second high found, use 5/29 or 6/1-2
if second_high_idx is None:
    for i, d in enumerate(plot_data):
        if i > peak_idx + 5 and d['h'] > second_high_val and d['h'] < peak_val:
            second_high_val = d['h']
            second_high_idx = i

# Find recent low (bottom of channel)
low_idx = None
low_val = float('inf')
for i, d in enumerate(plot_data):
    if i > peak_idx and d['l'] < low_val:
        low_val = d['l']
        low_idx = i

# Find an earlier low for the lower channel line (parallel to upper)
early_low_idx = None
early_low_val = float('inf')
for i, d in enumerate(plot_data):
    if peak_idx - 5 <= i <= peak_idx + 5:
        # skip, near peak
        continue
    if i > peak_idx and i < second_high_idx + 5:
        if d['l'] < early_low_val:
            early_low_val = d['l']
            early_low_idx = i

# Draw the descending channel
# Upper trendline: from peak to second_high
# Lower trendline: parallel, through the lows

# Calculate channel slope from upper line
if peak_idx is not None and second_high_idx is not None:
    dx_upper = second_high_idx - peak_idx
    dy_upper = second_high_val - peak_val
    slope = dy_upper / dx_upper  # negative for descending

    # Extend upper line to current
    x_upper = np.arange(peak_idx, n + 5)
    y_upper = peak_val + slope * (x_upper - peak_idx)

    # Lower line: parallel, offset to touch the lows
    # Find the max distance from upper line for lows between peak and now
    max_dist = 0
    for i in range(peak_idx, n):
        y_upper_at_i = peak_val + slope * (i - peak_idx)
        dist = y_upper_at_i - lows[i]
        if dist > max_dist:
            max_dist = dist
            low_idx = i

    # Actually, let's use the typical lows to draw the lower parallel line
    # Use the lowest point in the channel as reference
    y_lower = y_upper - max_dist * 0.95  # slightly inside

    # Draw channel
    ax1.plot(x_upper, y_upper, color='#f85149', linewidth=2.5, linestyle='-', alpha=0.9)
    ax1.plot(x_upper, y_lower, color='#f85149', linewidth=2.5, linestyle='-', alpha=0.9)

    # Fill channel
    ax1.fill_between(x_upper, y_lower, y_upper, color='#f85149', alpha=0.05)

    # Annotate upper line
    mid_upper_x = (peak_idx + second_high_idx) / 2
    mid_upper_y = (peak_val + second_high_val) / 2
    ax1.annotate(f'Descending Channel Upper\nSlope={slope:.3f}/day',
                xy=(peak_idx, peak_val),
                xytext=(peak_idx-8, peak_val+1.5),
                fontsize=9, color='#f85149', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#f85149', lw=1.5))

    # Annotate lower line
    ax1.annotate(f'Channel Lower (parallel)\nSupport zone',
                xy=(low_idx, low_val),
                xytext=(low_idx-15, low_val-2),
                fontsize=9, color='#f85149', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#f85149', lw=1.5))

    # Mark key points
    ax1.plot(peak_idx, peak_val, 'v', color='#f85149', markersize=12,
             markeredgecolor='white', markeredgewidth=1.5, zorder=5)
    ax1.plot(second_high_idx, second_high_val, 'v', color='#ff7b72', markersize=10,
             markeredgecolor='white', markeredgewidth=1.2, zorder=5)

    # Channel width annotation
    chan_width = (y_upper[n-1] - y_lower[n-1]) if n-1 < len(y_upper) else 0
    ax1.text(n-1, (y_upper[min(n-1,len(y_upper)-1)] + y_lower[min(n-1,len(y_lower)-1)])/2,
             f'Width: {chan_width:.2f}', color='#f85149', fontsize=8, ha='right',
             bbox=dict(facecolor='#0d1117', alpha=0.8, edgecolor='#f85149', pad=2))

else:
    print(f"WARNING: Could not identify channel points. peak={peak_idx} second={second_high_idx}")

# ============ KEY PRICE LEVELS ============
# Horizontal support/resistance
for price, color, style, label in [
    (22.00, '#d2991d', '--', 'Support 22.00'),
    (27.00, '#8b949e', ':', 'Mid 27.00 (previous support)'),
    (32.58, '#a371f7', '--', 'Resistance 32.58 (May peak)'),
]:
    ax1.axhline(y=price, color=color, linestyle=style, linewidth=1.2, alpha=0.7)
    ax1.text(n-1, price, f' {label}', color=color, fontsize=8, va='center', fontweight='bold')

# ============ LABEL KEY POINTS ============
# Mark major highs and lows
key_points = [
    (peak_idx, peak_val, f'Peak\n{peak_val:.2f}', '#f85149'),
]

# Find the channel start (pre-peak low)
pre_low_idx = None
pre_low_val = float('inf')
for i in range(0, peak_idx):
    if i > 20 and lows[i] < pre_low_val:
        # check if local minimum
        if i < len(plot_data)-2 and lows[i] <= lows[i-1] and lows[i] <= lows[i+1]:
            pre_low_val = lows[i]
            pre_low_idx = i

if pre_low_idx:
    key_points.append((pre_low_idx, pre_low_val, f'Pre-rally Low\n{pre_low_val:.2f}', '#3fb950'))

# Most recent point
key_points.append((n-1, closes[-1], f'Now\n{closes[-1]:.2f}', '#d2991d'))

for idx, price, label, color in key_points:
    ax1.annotate(label, (idx, price),
                textcoords='offset points', xytext=(0, 15 if 'Peak' in label else -22),
                fontsize=9, color=color, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-', color=color, lw=0.8))
    ax1.plot(idx, price, 'o', color=color, markersize=8,
             markeredgecolor='white', markeredgewidth=1.2, zorder=5)

# Current price marker
ax1.annotate(f'Close {plot_data[-1]["c"]:.2f}\n{plot_data[-1]["day"]}',
            (n-1, plot_data[-1]['c']),
            textcoords='offset points', xytext=(25, 5),
            fontsize=10, color='#d2991d', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#d2991d', lw=1.8))

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

close_all = [d['c'] for d in plot_data]
ema10_full = ema(close_all, 10)
dema10_full = ema(ema10_full, 10)
ma14 = sma_s(close_all, 14)
ma28 = sma_s(close_all, 28)
ma57 = sma_s(close_all, 57)
ma114 = sma_s(close_all, 114)
quad_ma = [(ma14[i]+ma28[i]+ma57[i]+ma114[i])/4 for i in range(len(plot_data))]

ax1.plot(range(len(plot_data)), dema10_full, color='white', linewidth=1.8, label='DEMA10 (White)', alpha=0.9)
ax1.plot(range(len(plot_data)), quad_ma, color='#d2991d', linewidth=1.8, label='Quad-MA (Yellow)', alpha=0.9)

# Check death cross
last_dema = dema10_full[-1]
last_quad = quad_ma[-1]
dc_text = f'DEMA10={last_dema:.2f} | QuadMA={last_quad:.2f} | {"DEATH CROSS!" if last_dema < last_quad else "No Death Cross"}'
ax1.text(0.02, 0.98, dc_text, transform=ax1.transAxes, fontsize=10,
         color='#f85149' if last_dema < last_quad else '#3fb950',
         fontweight='bold', va='top',
         bbox=dict(facecolor='#161b22', alpha=0.9, edgecolor='#30363d', pad=5))

# ============ VOLUME ============
vol_data = [d['v']/10000 for d in plot_data]
colors_vol = ['#3fb950' if plot_data[i]['c'] >= plot_data[i]['o'] else '#f85149' for i in range(n)]
ax2.bar(range(n), vol_data, color=colors_vol, alpha=0.7, width=0.8)

# Volume MA
vol_ma5 = sma_s(vol_data, 5)
ax2.plot(range(n), vol_ma5, color='#d2991d', linewidth=1, alpha=0.8, label='VOL MA5')

# ============ STYLING ============
ax1.set_title('Shenzhou Digital (000034) Daily Chart — Descending Channel Analysis',
              fontsize=15, color='white', fontweight='bold', pad=15)

# X-axis
tick_step = max(1, n // 12)
tick_pos = list(range(0, n, tick_step))
ax1.set_xticks(tick_pos)
ax1.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=8)
ax2.set_xticks(tick_pos)
ax2.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=8)

# Styling both axes
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

# Y-axis labels
ax1.set_ylabel('Price', color='#8b949e', fontsize=11)
ax2.set_ylabel('Volume (10k)', color='#8b949e', fontsize=10)

# Legend
legend_elements = [
    mpatches.Patch(color='white', alpha=0.9, label='DEMA10 (White Line)'),
    mpatches.Patch(color='#d2991d', alpha=0.9, label='Quad-MA (Yellow Line)'),
    mpatches.Patch(color='#f85149', alpha=0.7, label='Descending Channel Upper'),
    mpatches.Patch(color='#f85149', alpha=0.4, label='Descending Channel Lower'),
    mpatches.Patch(color='#a371f7', alpha=0.7, label='Resistance 32.58'),
    mpatches.Patch(color='#d2991d', alpha=0.7, label='Support 22.00'),
]
ax1.legend(handles=legend_elements, loc='upper right', fontsize=9,
          facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')

# Channel statistics annotation
if peak_idx is not None and second_high_idx is not None:
    days_in_channel = n - 1 - peak_idx
    total_decline = (plot_data[-1]['c'] - peak_val) / peak_val * 100

    stats = (
        f"CHANNEL STATISTICS\n"
        f"{'='*30}\n"
        f"Channel Start: {plot_data[peak_idx]['day']} (Peak {peak_val:.2f})\n"
        f"2nd High: {plot_data[second_high_idx]['day']} ({second_high_val:.2f})\n"
        f"Days in Channel: {days_in_channel}\n"
        f"Slope: {slope:.4f}/day = {slope*20:.2f}/month\n"
        f"Decline from Peak: {total_decline:.1f}%\n"
        f"Current: {plot_data[-1]['c']:.2f}\n"
        f"Channel Lower (projected): {y_lower[min(n-1,len(y_lower)-1)]:.2f}\n"
        f"Channel Upper (projected): {y_upper[min(n-1,len(y_upper)-1)]:.2f}\n"
        f"\n"
        f"KEY OBSERVATIONS\n"
        f"{'='*30}\n"
        f"* Clear descending channel from May peak\n"
        f"* Lower highs confirming downtrend\n"
        f"* Reaching historical support near 22.00\n"
        f"* Volume declining = selling pressure easing\n"
        f"* Watch for breakout above upper channel\n"
        f"  as reversal signal\n"
    )

    # Add text box on the right side
    ax1.text(0.985, 0.50, stats, transform=ax1.transAxes,
            fontsize=8.5, color='#c9d1d9', fontfamily='monospace',
            verticalalignment='center', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                     edgecolor='#30363d', alpha=0.92))

# Save
outpath = 'D:/Trade/new_tdx64/ShenzhouDigital_000034_DescendingChannel.png'
fig.savefig(outpath, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
plt.close()

size_kb = os.path.getsize(outpath) / 1024
print(f'OK: {outpath} ({size_kb:.0f} KB)')
print(f'Peak: idx={peak_idx} val={peak_val}')
print(f'Second High: idx={second_high_idx} val={second_high_val}')
print(f'Low: idx={low_idx} val={low_val}')
print(f'DEMA10={last_dema:.2f} QuadMA={last_quad:.2f}')
