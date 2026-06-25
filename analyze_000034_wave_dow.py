import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

with open('D:/Trading Workflow/Stock_lab_system/data/cache/daily_history/000034.json') as f:
    raw = json.load(f)

data = []
for r in raw:
    data.append({'day': r['day'], 'o': float(r['open']), 'h': float(r['high']),
                 'l': float(r['low']), 'c': float(r['close']), 'v': float(r['volume'])})

# Use 2023-01-01 onwards for wave analysis
plot_data = [d for d in data if d['day'] >= '2023-07-01']
n = len(plot_data)
closes = np.array([d['c'] for d in plot_data])
highs = np.array([d['h'] for d in plot_data])
lows = np.array([d['l'] for d in plot_data])
vols = np.array([d['v'] for d in plot_data])
dates = [d['day'][5:] for d in plot_data]

# === MA functions ===
def sma(series, period):
    result = np.zeros(len(series))
    for i in range(len(series)):
        start = max(0, i-period+1)
        result[i] = np.mean(series[start:i+1])
    return result

def ema(series, period):
    result = np.zeros(len(series))
    result[period-1] = np.mean(series[:period])
    k = 2/(period+1)
    for i in range(period, len(series)):
        result[i] = series[i]*k + result[i-1]*(1-k)
    return result

ma20 = sma(closes, 20); ma50 = sma(closes, 50); ma200 = sma(closes, 200)
e10 = ema(closes, 10); dema10 = ema(e10, 10)
ma14 = sma(closes,14); ma28 = sma(closes,28); ma57 = sma(closes,57); ma114 = sma(closes,114)
quad_ma = (ma14+ma28+ma57+ma114)/4

# === Wave Structure ===
# Manually identified from swing data:
# W1: 2024-02-06 15.01 -> 2024-03-04 25.92
# W2: 2024-03-04 25.92 -> 2024-04-22 19.13
# W3: 2024-04-22 19.13 -> 2025-02-20 45.05 (extended!)
# W4: 2025-02-20 45.05 -> 2025-03-05 34.26 then complex correction to 2025-06-23 25.95
# W5: 2025-06-23 25.95 -> 2025-09-18 35.33
# A: 2025-09-18 35.33 -> 2025-10-17 28.06
# B: 2025-10-17 28.06 -> 2025-11-10 34.85
# C: 2025-11-10 34.85 -> 2026-04-03 23.68
# Then: 23.68 -> 2026-05-11 32.58 (X/B-wave of higher degree?)
# Now declining from 32.58 -> 22.33

# === PLOT ===
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
fig = plt.figure(figsize=(30, 22))
fig.patch.set_facecolor('#0d1117')

ax1 = fig.add_axes([0.04, 0.32, 0.73, 0.64])
ax1.set_facecolor('#0d1117')

# Candles
step = max(1, n // 220)
for i in range(0, n, step):
    d = plot_data[i]
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax1.plot([i, i], [d['l'], d['h']], color=color, linewidth=0.5)
    y1, y2 = max(d['o'], d['c']), min(d['o'], d['c'])
    ax1.bar(i, y1-y2, 0.65, bottom=y2, color=color, alpha=0.85)

# MAs
ax1.plot(range(n), dema10, color='white', linewidth=1.8, label='DEMA10', alpha=0.9)
ax1.plot(range(n), quad_ma, color='#d2991d', linewidth=1.8, label='QuadMA', alpha=0.9)
ax1.plot(range(n), ma50, color='#58a6ff', linewidth=1.2, label='MA50', alpha=0.7, linestyle=':')
ax1.plot(range(n), ma200, color='#f0883e', linewidth=1.2, label='MA200', alpha=0.7, linestyle=':')

# === Wave Markers ===
def find_idx(day_str):
    for i, d in enumerate(plot_data):
        if d['day'] >= day_str: return i
    return -1

wave_points = [
    ('2024-02-06', 15.01, 'W(1)\n15.01', '#3fb950'),
    ('2024-03-04', 25.92, 'W(1) top\n25.92', '#3fb950'),
    ('2024-04-22', 19.13, 'W(2)\n19.13', '#f85149'),
    ('2024-07-09', 15.80, 'W(2) retest\n15.80', '#f85149'),
    ('2025-02-20', 45.05, 'W(3) TOP\n45.05', '#3fb950'),
    ('2025-06-23', 25.95, 'W(4) low\n25.95', '#f85149'),
    ('2025-09-18', 35.33, 'W(5)\n35.33', '#3fb950'),
    ('2025-10-17', 28.06, 'A\n28.06', '#d2991d'),
    ('2025-11-10', 34.85, 'B\n34.85', '#d2991d'),
    ('2026-04-03', 23.68, 'C\n23.68', '#d2991d'),
    ('2026-05-11', 32.58, 'X/B?\n32.58', '#a371f7'),
]

for day_str, price, label, color in wave_points:
    idx = find_idx(day_str)
    if idx < 0: continue
    yoff = 18 if 'TOP' in label else (-20 if 'low' in label.lower() or 'C' in label or 'A' in label or 'retest' in label else 15)
    ax1.annotate(label, (idx, price), textcoords='offset points',
                xytext=(0, yoff), fontsize=8, color=color, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-', color=color, lw=0.8))
    ax1.plot(idx, price, 'o', color=color, markersize=8, markeredgecolor='white', zorder=5)

# === Wave Arrows ===
arrows = [
    ('2024-02-06', 15.01, '2024-03-04', 25.92, '#3fb950', 'W(1)'),
    ('2024-03-04', 25.92, '2024-07-09', 15.80, '#f85149', 'W(2)'),
    ('2024-07-09', 15.80, '2025-02-20', 45.05, '#3fb950', 'W(3) EXTENDED'),
    ('2025-02-20', 45.05, '2025-06-23', 25.95, '#f85149', 'W(4)'),
    ('2025-06-23', 25.95, '2025-09-18', 35.33, '#3fb950', 'W(5) FAILED'),
    ('2025-09-18', 35.33, '2025-10-17', 28.06, '#f85149', 'A'),
    ('2025-10-17', 28.06, '2025-11-10', 34.85, '#d2991d', 'B'),
    ('2025-11-10', 34.85, '2026-04-03', 23.68, '#f85149', 'C'),
]
for d1, p1, d2, p2, color, label in arrows:
    i1 = find_idx(d1); i2 = find_idx(d2)
    if i1 >= 0 and i2 >= 0:
        ax1.annotate('', xy=(i2, p2), xytext=(i1, p1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2.5, alpha=0.55))
        mx, my = (i1+i2)/2, (p1+p2)/2
        yoff = -12 if 'W(2)' in label or 'W(4)' in label or 'A' in label or 'C' in label else 12
        ax1.text(mx+2, my+yoff, label, fontsize=8, color=color, fontweight='bold', ha='center',
                bbox=dict(facecolor='#0d1117', alpha=0.75, edgecolor='none'))

# === Fibonacci ===
fib_high = 45.05; fib_low = 15.01
fib_range = fib_high - fib_low
fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
for level in fib_levels:
    fp = fib_high - fib_range * level
    ax1.axhline(y=fp, color='#a371f7', linestyle=':', linewidth=0.8, alpha=0.5)
    ax1.text(n-1, fp, f' {level:.3f}={fp:.2f}', color='#a371f7', fontsize=7, va='center')

# Current price
ax1.plot(n-1, closes[-1], 'D', color='#d2991d', markersize=10, markeredgecolor='white', zorder=5)
ax1.annotate(f'Now {plot_data[-1]["day"]}\n{closes[-1]:.2f}', (n-1, closes[-1]),
            textcoords='offset points', xytext=(30,-5), fontsize=10, color='#d2991d', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#d2991d', lw=2))

# === Styling ===
ax1.set_title('SHENZHOU DIGITAL (000034) — Elliott Wave + Dow Theory Joint Analysis',
              fontsize=14, color='white', fontweight='bold', pad=12)
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#30363d'); ax1.spines['bottom'].set_color('#30363d')
ax1.tick_params(colors='#8b949e', labelsize=7)
tick_step = max(1, n//15); tick_pos = list(range(0, n, tick_step))
ax1.set_xticks(tick_pos)
ax1.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=7)
ax1.set_ylabel('Price', color='#8b949e', fontsize=10)
ax1.grid(True, alpha=0.08, color='#8b949e'); ax1.set_axisbelow(True)

legend_elements = [
    mpatches.Patch(color='white', alpha=0.9, label='DEMA10 (White Line)'),
    mpatches.Patch(color='#d2991d', alpha=0.9, label='Quad-MA (Yellow Line)'),
    mpatches.Patch(color='#58a6ff', alpha=0.7, label='MA50'),
    mpatches.Patch(color='#f0883e', alpha=0.7, label='MA200'),
    mpatches.Patch(color='#a371f7', alpha=0.5, label='Fibonacci 15.01->45.05'),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=8,
          facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')

# === Analysis Panel ===
ax2 = fig.add_axes([0.79, 0.32, 0.19, 0.64])
ax2.set_facecolor('#0d1117'); ax2.axis('off')

# Iron rules check
w1_top = 25.92; w4_low = 25.95
w1_len = 25.92 - 15.01  # 10.91
w3_len = 45.05 - 15.80  # 29.25
w2_low = 19.13
w1_start = 15.01
rule1 = w2_low > w1_start
rule2 = w3_len > w1_len
rule3 = w4_low > w1_top

# Current Dow state
cur_primary = "BULL" if ma50[-1] > ma200[-1] else "BEAR"
cur_secondary = "BULL" if ma20[-1] > ma50[-1] else "BEAR"
cur_minor = "BULL" if closes[-1] > ma20[-1] else "BEAR"

# Dow phase
if cur_primary == "BEAR" and cur_secondary == "BEAR":
    dow_phase = "Phase 1: Markdown/Panic"
elif cur_primary == "BEAR" and cur_secondary == "BULL":
    dow_phase = "Accumulation (smart money)"
elif cur_primary == "BULL" and cur_secondary == "BULL":
    dow_phase = "Phase 2: Public Participation"
else:
    dow_phase = "Phase 3: Distribution"

analysis = (
    f"SHENZHOU DIGITAL (000034)\n"
    f"========================\n"
    f"Date: {plot_data[-1]['day']}\n"
    f"Close: {closes[-1]:.2f}\n"
    f"\n"
    f"--- ELLIOTT WAVE ---\n"
    f"Cycle: 15.01 -> 45.05 -> 22.33\n"
    f"\n"
    f"5-Wave Impulse:\n"
    f"  W(1): 15.01->25.92 (+{w1_len:.1f})\n"
    f"  W(2): 25.92->15.80 (-{25.92-15.80:.1f})\n"
    f"  W(3): 15.80->45.05 (+{w3_len:.1f})\n"
    f"  W(4): 45.05->25.95 (-{45.05-25.95:.1f})\n"
    f"  W(5): 25.95->35.33 (+{35.33-25.95:.1f})\n"
    f"       FAILED! W5 < W3 top\n"
    f"\n"
    f"Iron Rules:\n"
    f"  W2>W1 start: {w2_low:.1f}>{w1_start:.1f} {'OK' if rule1 else 'FAIL'}\n"
    f"  W3 longest: {w3_len:.1f}>{w1_len:.1f} {'OK' if rule2 else 'FAIL'}\n"
    f"  W4>W1 top: {w4_low:.1f}>{w1_top:.1f} {'OK' if rule3 else 'FAIL'}\n"
    f"\n"
    f"ABC Correction:\n"
    f"  A: 35.33->28.06 (-{35.33-28.06:.1f})\n"
    f"  B: 28.06->34.85 (+{34.85-28.06:.1f})\n"
    f"  C: 34.85->23.68 (-{34.85-23.68:.1f})\n"
    f"  C={34.85-23.68:.1f} vs A={35.33-28.06:.1f}\n"
    f"  C/A={((34.85-23.68)/(35.33-28.06)):.2f}x\n"
    f"\n"
    f"--- FIBONACCI (15.01-45.05) ---\n"
)
for level in fib_levels:
    fp = fib_high - fib_range * level
    hit = " << HERE" if abs(closes[-1]-fp)/fp < 0.03 else ""
    analysis += f"  {level:.3f}: {fp:.2f}{hit}\n"

analysis += (
    f"\n"
    f"--- DOW THEORY ---\n"
    f"MA200: {ma200[-1]:.2f}\n"
    f"MA50:  {ma50[-1]:.2f}\n"
    f"MA20:  {ma20[-1]:.2f}\n"
    f"Primary:   {cur_primary}\n"
    f"Secondary: {cur_secondary}\n"
    f"Minor:     {cur_minor}\n"
    f"Phase: {dow_phase}\n"
    f"\n"
    f"--- 标准战法 ---\n"
    f"DEMA10: {dema10[-1]:.2f}\n"
    f"QuadMA: {quad_ma[-1]:.2f}\n"
    f"DC: {'YES ☠' if dema10[-1]<quad_ma[-1] else 'NO'}\n"
    f"vs Yellow: {(closes[-1]-quad_ma[-1])/quad_ma[-1]*100:.1f}%\n"
    f"\n"
    f"--- VERDICT ---\n"
    f"Wave: {'BULL (C complete, new impulse?)' if closes[-1] > 23.68 else 'BEAR (C may extend)'}\n"
    f"Dow:  {cur_primary}\n"
    f"战术: {'BEAR (dead cross)' if dema10[-1]<quad_ma[-1] else 'BULL'}\n"
)

ax2.text(0.02, 0.98, analysis, transform=ax2.transAxes, fontsize=7.2,
         color='#c9d1d9', fontfamily='monospace', verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22', edgecolor='#30363d', alpha=0.92))

# === Volume ===
ax3 = fig.add_axes([0.04, 0.18, 0.73, 0.10])
ax3.set_facecolor('#0d1117')
vcolors = ['#3fb950' if plot_data[i]['c']>=plot_data[i]['o'] else '#f85149' for i in range(n)]
ax3.bar(range(n), vols/10000, color=vcolors, alpha=0.5, width=0.8)
vol_ma20 = sma(vols, 20)
ax3.plot(range(n), vol_ma20/10000, color='#d2991d', linewidth=1, alpha=0.8)
ax3.set_ylabel('Vol(10k)', color='#8b949e', fontsize=8)
for s in ax3.spines.values(): s.set_visible(False)
ax3.spines['left'].set_color('#30363d'); ax3.spines['bottom'].set_color('#30363d')
ax3.tick_params(colors='#8b949e', labelsize=7)
ax3.set_xticks(tick_pos); ax3.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=7)
ax3.grid(True, alpha=0.08, color='#8b949e'); ax3.set_axisbelow(True)

# === Dow Theory Trend Score ===
ax4 = fig.add_axes([0.04, 0.05, 0.73, 0.12])
ax4.set_facecolor('#0d1117')
trend_score = np.zeros(n)
for i in range(n):
    score = 0
    if closes[i] > ma20[i]: score += 1
    else: score -= 1
    if ma20[i] > ma50[i]: score += 1
    else: score -= 1
    if ma50[i] > ma200[i]: score += 1
    else: score -= 1
    trend_score[i] = score
ax4.fill_between(range(n), 0, trend_score, where=trend_score>=0, color='#3fb950', alpha=0.3)
ax4.fill_between(range(n), 0, trend_score, where=trend_score<0, color='#f85149', alpha=0.3)
ax4.plot(range(n), trend_score, color='#c9d1d9', linewidth=0.8)
ax4.axhline(y=0, color='#30363d', linewidth=0.5)
ax4.set_ylim(-3.5, 3.5)
ax4.set_yticks([-3, 0, 3])
ax4.set_yticklabels(['BEAR', 'Neutral', 'BULL'], fontsize=7, color='#8b949e')
ax4.set_title('Dow Theory Trend Score (Price>MA20 + MA20>MA50 + MA50>MA200)', fontsize=8, color='#8b949e', pad=3)
for s in ax4.spines.values(): s.set_visible(False)
ax4.spines['left'].set_color('#30363d'); ax4.spines['bottom'].set_color('#30363d')
ax4.tick_params(colors='#8b949e', labelsize=7)
ax4.set_xticks(tick_pos); ax4.set_xticklabels([], fontsize=7)

# === Bottom Right: X-wave detail ===
ax5 = fig.add_axes([0.79, 0.05, 0.19, 0.25])
ax5.set_facecolor('#0d1117'); ax5.axis('off')

detail = (
    f"CURRENT STRUCTURE DEBATE\n"
    f"========================\n"
    f"\n"
    f"Scenario A (Bullish):\n"
    f"  ABC done at 23.68 (Apr'26)\n"
    f"  23.68->32.58 = W(1) new impulse\n"
    f"  32.58->22.33 = W(2) pullback\n"
    f"  Next: W(3) > 32.58\n"
    f"  Target: > 45.05 new high\n"
    f"  RISK: 22.33 < 23.68(C low)\n"
    f"  -> W(2) broke W(1) start!\n"
    f"  -> Invalid unless truncated\n"
    f"\n"
    f"Scenario B (Bearish):\n"
    f"  ABC complete at 23.68\n"
    f"  23.68->32.58 = X wave\n"
    f"  32.58->now = new A-B-C\n"
    f"  Y-target: 22.00-20.00\n"
    f"  (double zigzag)\n"
    f"\n"
    f"Scenario C (Neutral):\n"
    f"  C-wave extending to\n"
    f"  21.50-20.00 support\n"
    f"  (C=1.618xA target)\n"
    f"\n"
    f"KEY LEVEL: 22.33 close\n"
    f"Must hold 22.00 for bullish\n"
)

ax5.text(0.02, 0.98, detail, transform=ax5.transAxes, fontsize=6.8,
         color='#8b949e', fontfamily='monospace', verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#161b22', edgecolor='#30363d', alpha=0.9))

outpath = 'D:/Trade/new_tdx64/Shenzhou_000034_Wave_Dow.png'
fig.savefig(outpath, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
plt.close()
print(f'OK: {outpath} ({os.path.getsize(outpath)/1024:.0f} KB)')
print(f'Close: {closes[-1]:.2f} | DEMA10: {dema10[-1]:.2f} | QuadMA: {quad_ma[-1]:.2f}')
print(f'Rules: W2>start={rule1} W3longest={rule2} W4>W1top={rule3}')
print(f'Dow: P={cur_primary} S={cur_secondary} M={cur_minor} Score={trend_score[-1]}')
