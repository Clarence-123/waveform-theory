import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json
import os

# Load data
with open('D:/Trading Workflow/Stock_lab_system/data/cache/daily_history/000977.json', 'r') as f:
    raw = json.load(f)

data = []
for r in raw:
    data.append({
        'day': r['day'],
        'o': float(r['open']), 'h': float(r['high']),
        'l': float(r['low']), 'c': float(r['close']),
        'v': float(r['volume'])
    })

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(24, 30))
fig.patch.set_facecolor('#0d1117')

# ===== TOP: Weekly Wave Structure =====
ax1 = fig.add_axes([0.04, 0.50, 0.92, 0.46])
ax1.set_facecolor('#0d1117')

wData = [d for d in data if d['day'] >= '2024-07-01']
weekly = wData
dates = [d['day'][5:] for d in weekly]

# Candles (sampled)
step = max(1, len(weekly) // 180)
for i in range(0, len(weekly), step):
    d = weekly[i]
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    body_w = 0.7
    ax1.plot([i, i], [d['l'], d['h']], color=color, linewidth=0.6)
    y1, y2 = max(d['o'], d['c']), min(d['o'], d['c'])
    ax1.bar(i, y1-y2, body_w, bottom=y2, color=color, alpha=0.85)

def find_idx(day_str, arr):
    for i, d in enumerate(arr):
        if d['day'] >= day_str:
            return i
    return -1

# Wave points: (day, price, label, color, y_offset)
wave_pts = [
    ('2024-08-15', 32.45, '1 start\n32.45', '#3fb950', 20),
    ('2025-02-17', 69.60, '3-1 top\n69.60', '#3fb950', -18),
    ('2025-04-09', 41.57, '3-2 bot\n41.57', '#f85149', 20),
    ('2025-10-09', 80.80, '3 TOP 80.80', '#3fb950', -20),
    ('2025-11-21', 57.63, '4-A\n57.63', '#f85149', 20),
    ('2026-01-12', 71.38, '4-B\n71.38', '#d2991d', -18),
    ('2026-03-23', 55.73, '4 BOT 55.73', '#f85149', 20),
    ('2026-05-08', 79.49, '5 TOP 79.49 FAIL', '#f85149', -20),
]

for day_str, price, label, color, yoff in wave_pts:
    idx = find_idx(day_str, weekly)
    if idx >= 0:
        ax1.annotate(label, (idx, price),
                    textcoords='offset points', xytext=(0, yoff),
                    fontsize=7.5, color=color, fontweight='bold', ha='center',
                    arrowprops=dict(arrowstyle='-', color=color, lw=1))
        ax1.plot(idx, price, 'o', color=color, markersize=7, markeredgecolor='white', markeredgewidth=1.2)

# Current
ci = len(weekly) - 1
ax1.annotate('NOW\n' + str(weekly[-1]['c']), (ci, weekly[-1]['c']),
            textcoords='offset points', xytext=(20, -8),
            fontsize=10, color='#d2991d', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#d2991d', lw=2))
ax1.plot(ci, weekly[-1]['c'], 'D', color='#d2991d', markersize=11, markeredgecolor='white', markeredgewidth=2)

# Key levels
for y, color, style, w, label in [
    (55.73, '#d2991d', '--', 1.8, 'Wave-4 Bottom 55.73 (Bull/Bear Line)'),
    (57.16, '#a371f7', ':', 1.3, '0.382 Fib 57.16'),
    (49.85, '#8b949e', ':', 0.8, '0.5 Fib 49.85'),
]:
    ax1.axhline(y=y, color=color, linestyle=style, linewidth=w, alpha=0.75)
    ax1.text(len(weekly)-2, y + 1.0, label, color=color, fontsize=8, ha='right', fontweight='bold')

# Draw wave arrows
arrows = [
    ('2024-08-15', 32.45, '2025-02-17', 69.60, '#3fb950', '1'),
    ('2025-02-17', 69.60, '2025-04-09', 41.57, '#f85149', '2'),
    ('2025-04-09', 41.57, '2025-10-09', 80.80, '#3fb950', '3 (extended)'),
    ('2025-10-09', 80.80, '2026-03-23', 55.73, '#f85149', '4 (complex)'),
    ('2026-03-23', 55.73, '2026-05-08', 79.49, '#f85149', '5 TRUNCATED'),
]
for d1, p1, d2, p2, color, label in arrows:
    i1 = find_idx(d1, weekly)
    i2 = find_idx(d2, weekly)
    if i1 >= 0 and i2 >= 0:
        mx, my = (i1+i2)/2, (p1+p2)/2
        ax1.annotate('', xy=(i2, p2), xytext=(i1, p1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=3.2, alpha=0.65,
                                   connectionstyle='arc3,rad=0.05'))
        yoff = 10 if '1' in label or '3' in label else -10
        ax1.text(mx, my + yoff, label, fontsize=11, color=color, fontweight='bold', ha='center',
                bbox=dict(facecolor='#0d1117', alpha=0.75, edgecolor='none', pad=2))

ax1.set_title('LANGCHAO INFO (000977) Weekly Elliott Wave Structure -- BEARISH: Truncated 5th Wave',
              fontsize=14, color='white', fontweight='bold', pad=12)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#30363d')
ax1.spines['bottom'].set_color('#30363d')
ax1.tick_params(colors='#8b949e', labelsize=7)
ax1.set_ylim(24, 92)
ax1.set_xlim(-3, len(weekly) + 5)
tick_pos = list(range(0, len(weekly), max(1, len(weekly)//10)))
ax1.set_xticks(tick_pos)
ax1.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=7)
ax1.set_ylabel('Price', color='#8b949e', fontsize=10)
ax1.grid(True, alpha=0.12, color='#8b949e')
ax1.set_axisbelow(True)

leg = [
    mpatches.Patch(color='#f85149', alpha=0.75, label='Wave-5 TOP 79.49 < Wave-3 TOP 80.80 : TRUNCATION'),
    mpatches.Patch(color='#d2991d', alpha=0.75, label='Wave-4 Bottom 55.73 = Bull/Bear dividing line'),
    mpatches.Patch(color='#a371f7', alpha=0.75, label='0.382 Fib Retrace = 57.16 (tested exactly 6/11 low 57.15)'),
]
ax1.legend(handles=leg, loc='upper left', fontsize=8.5,
          facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')

# ===== BOTTOM: Daily A-Wave Detail =====
ax2 = fig.add_axes([0.04, 0.04, 0.60, 0.40])
ax2.set_facecolor('#0d1117')

dData = [d for d in data if d['day'] >= '2026-04-20']
ddates = [d['day'][5:] for d in dData]

for i, d in enumerate(dData):
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax2.plot([i, i], [d['l'], d['h']], color=color, linewidth=0.8)
    y1, y2 = max(d['o'], d['c']), min(d['o'], d['c'])
    ax2.bar(i, y1-y2, 0.75, bottom=y2, color=color, alpha=0.85)

# Volume sub-plot on same axis with scaling
vol_max = max(d['v'] for d in dData)
vol_scale = 12.0 / vol_max
for i, d in enumerate(dData):
    vh = d['v'] * vol_scale
    vcolor = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax2.bar(i, vh, 0.6, bottom=52.5, color=vcolor, alpha=0.2)

a_wave = [
    ('2026-05-08', 79.49, '5 TOP\n79.49', '#f85149', -22),
    ('2026-05-27', 64.52, 'A-1', '#d2991d', 18),
    ('2026-05-28', 66.41, 'A-2', '#3fb950', -15),
    ('2026-06-08', 57.40, 'A-3', '#d2991d', 18),
    ('2026-06-10', 62.13, 'A-4', '#3fb950', -15),
    ('2026-06-11', 57.15, 'A-5?\n57.15', '#d2991d', 18),
]
for day_str, price, label, color, yoff in a_wave:
    idx = find_idx(day_str, dData)
    if idx >= 0:
        ax2.annotate(label, (idx, price),
                    textcoords='offset points', xytext=(0, yoff),
                    fontsize=8, color=color, fontweight='bold', ha='center',
                    arrowprops=dict(arrowstyle='-', color=color, lw=0.8))
        ax2.plot(idx, price, 'o', color=color, markersize=6, markeredgecolor='white', markeredgewidth=1)

# Current
ax2.plot(len(dData)-1, dData[-1]['c'], 'D', color='#d2991d', markersize=9, markeredgecolor='white', markeredgewidth=1.5)
ax2.annotate(f'Close {dData[-1]["c"]}', (len(dData)-1, dData[-1]['c']),
            textcoords='offset points', xytext=(15, 0), fontsize=9, color='#d2991d', fontweight='bold')

# Draw A-wave arrows
a_arrows = [
    ('2026-05-08', 79.49, '2026-05-27', 64.52, '#f85149', 'A-1'),
    ('2026-05-28', 66.41, '2026-06-08', 57.40, '#f85149', 'A-3 (ext)'),
    ('2026-06-10', 62.13, '2026-06-11', 57.15, '#f85149', 'A-5?'),
]
for d1, p1, d2, p2, color, label in a_arrows:
    i1 = find_idx(d1, dData)
    i2 = find_idx(d2, dData)
    if i1 >= 0 and i2 >= 0:
        ax2.annotate('', xy=(i2, p2), xytext=(i1, p1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2, alpha=0.6,
                                   connectionstyle='arc3,rad=0.08'))

# Levels
for y, color, style, w in [(55.73, '#d2991d', '--', 1.5), (57.16, '#a371f7', ':', 1.0)]:
    ax2.axhline(y=y, color=color, linestyle=style, linewidth=w, alpha=0.6)

# Volume label
ax2.text(len(dData)-1, 52.5 + 6, 'Volume', color='#8b949e', fontsize=8, ha='right', alpha=0.6)

ax2.set_title('Daily A-Wave Decline Detail (2026-05-08 to 06-12) -- Selling Climax / Stopping Action',
              fontsize=11, color='white', fontweight='bold')
ax2.set_ylim(51.5, 83)
ax2.set_xlim(-1, len(dData)+1)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_color('#30363d')
ax2.spines['bottom'].set_color('#30363d')
ax2.tick_params(colors='#8b949e', labelsize=7)
tick_pos = list(range(0, len(dData), max(1, len(dData)//8)))
ax2.set_xticks(tick_pos)
ax2.set_xticklabels([ddates[i] for i in tick_pos], rotation=45, fontsize=7)
ax2.grid(True, alpha=0.12, color='#8b949e')
ax2.set_axisbelow(True)

# ===== BOTTOM RIGHT: Summary Panel =====
ax3 = fig.add_axes([0.67, 0.04, 0.30, 0.40])
ax3.set_facecolor('#0d1117')
ax3.axis('off')

summary = (
    "LANGCHAO INFO (000977) - Multi-Timeframe Analysis\n"
    "Data as of: 2026-06-12  |  Close: 57.86\n"
    "\n"
    "WAVE STRUCTURE (Bull Run: 18.90 -> 79.49)\n"
    "  Wave-1:  18.90 -> 41.13  (+117%)\n"
    "  Wave-2:  41.13 -> 32.45  (-21%, shallow)\n"
    "  Wave-3:  32.45 -> 80.80  (+149%, EXTENDED)\n"
    "  Wave-4:  80.80 -> 55.73  (-31%, complex ABC)\n"
    "  Wave-5:  55.73 -> 79.49  (+42%, TRUNCATED!)\n"
    "\n"
    "THREE IRON RULES:\n"
    "  [OK] Wave-2 not below Wave-1 start\n"
    "  [OK] Wave-3 not the shortest\n"
    "  [OK] Wave-4 not entering Wave-1 territory\n"
    "  [FAIL] Wave-5 top (79.49) < Wave-3 top (80.80)\n"
    "         -> TRUNCATED 5TH = MAJOR TOP SIGNAL\n"
    "\n"
    "FIBONACCI RETRACEMENT (18.90 -> 80.80):\n"
    "  [X] 0.236 = 66.19 (broken)\n"
    "  [!] 0.382 = 57.16 (TESTING: 6/11 low=57.15)\n"
    "  [ ] 0.500 = 49.85\n"
    "  [ ] 0.618 = 42.53\n"
    "\n"
    "THREE TIMEFRAME VERDICT:\n"
    "  Weekly:  BEARISH (reversal candidate)\n"
    "  Daily:   BEARISH (A-wave near end?)\n"
    "  1H:      NEUTRAL-BULLISH (stopping action)\n"
    "\n"
    "KEY LEVEL: 55.73 = Wave-4 Bottom\n"
    "  -> Break = bull structure destroyed, SELL ALL\n"
    "  -> Hold = expect B-wave bounce to 65-68\n"
    "\n"
    "B-WAVE BOUNCE TARGETS:\n"
    "  Weak:   65.70 (0.382 retrace of A-wave)\n"
    "  Normal: 68.32 (0.5 retrace)\n"
    "  Strong: 70.95 (0.618 retrace, unlikely)\n"
)

ax3.text(0.02, 0.98, summary, transform=ax3.transAxes,
        fontsize=8.5, color='#c9d1d9', fontfamily='monospace',
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                 edgecolor='#30363d', alpha=0.92))

# Save
outpath = 'D:/Trade/new_tdx64/浪潮信息_000977_分析图.png'
fig.savefig(outpath, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
plt.close()

size_kb = os.path.getsize(outpath) / 1024
print(f'OK: {outpath} ({size_kb:.0f} KB)')
