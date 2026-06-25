import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

with open('D:/Trading Workflow/Stock_lab_system/data/cache/daily_history/002074.json') as f:
    raw = json.load(f)

data = []
for r in raw:
    data.append({
        'day': r['day'], 'o': float(r['open']), 'h': float(r['high']),
        'l': float(r['low']), 'c': float(r['close']), 'v': float(r['volume'])
    })

# Use data from 2024-01-01
plot_data = [d for d in data if d['day'] >= '2024-01-01']
n = len(plot_data)
closes = np.array([d['c'] for d in plot_data])
highs = np.array([d['h'] for d in plot_data])
lows = np.array([d['l'] for d in plot_data])
vols = np.array([d['v'] for d in plot_data])
dates = [d['day'][5:] for d in plot_data]

# === Moving Averages (Dow Theory) ===
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

ma20 = sma(closes, 20)
ma50 = sma(closes, 50)
ma200 = sma(closes, 200)
ema10_1 = ema(closes, 10)
dema10 = ema(ema10_1, 10)
ma14 = sma(closes, 14)
ma28 = sma(closes, 28)
ma57 = sma(closes, 57)
ma114 = sma(closes, 114)
quad_ma = (ma14 + ma28 + ma57 + ma114) / 4

# === Wave Structure Identification ===
# Find major swing points using zigzag
def find_swings(highs, lows, min_bars=8):
    """Find swing highs and lows"""
    sw_highs = []  # (idx, price)
    sw_lows = []   # (idx, price)

    for i in range(min_bars, len(highs)-min_bars):
        # Swing high
        is_high = True
        for j in range(1, min_bars+1):
            if highs[i] <= highs[i-j] or highs[i] <= highs[i+j]:
                is_high = False
                break
        if is_high:
            sw_highs.append((i, highs[i]))

        # Swing low
        is_low = True
        for j in range(1, min_bars+1):
            if lows[i] >= lows[i-j] or lows[i] >= lows[i+j]:
                is_low = False
                break
        if is_low:
            sw_lows.append((i, lows[i]))

    return sw_highs, sw_lows

sw_highs, sw_lows = find_swings(highs, lows, min_bars=6)

# Find major wave structure
# Combine and sort all swings
all_swings = [(idx, price, 'H') for idx, price in sw_highs] + [(idx, price, 'L') for idx, price in sw_lows]
all_swings.sort(key=lambda x: x[0])

# Filter to alternating H-L-H-L
filtered = []
last_type = None
for idx, price, stype in all_swings:
    if stype != last_type:
        filtered.append((idx, price, stype))
        last_type = stype

# === DOW THEORY Analysis ===
# Identify primary trend phases
# Phase 1: Accumulation (after prolonged decline, sideways movement)
# Phase 2: Public participation (trend confirmation, volume increase)
# Phase 3: Distribution/excess (wide participation, divergence)

# Calculate trend phases using MA relationships
def dow_phase(idx):
    """Determine Dow Theory phase at given index"""
    if idx < 200:
        return "primary_unknown"

    # Primary trend: MA50 vs MA200
    if ma50[idx] > ma200[idx]:
        primary = "bull"
    else:
        primary = "bear"

    # Secondary: MA20 vs MA50
    if ma20[idx] > ma50[idx]:
        secondary = "bull"
    else:
        secondary = "bear"

    # Minor: price vs MA20
    if closes[idx] > ma20[idx]:
        minor = "bull"
    else:
        minor = "bear"

    # Phase detection
    if primary == "bear" and secondary == "bear":
        phase = "Dow Phase 1: Markdown / Panic"
    elif primary == "bear" and secondary == "bull":
        phase = "Dow Phase: Accumulation (smart money buying)"
    elif primary == "bull" and secondary == "bull" and minor == "bull":
        phase = "Dow Phase 2: Public Participation (up trend)"
    elif primary == "bull" and secondary == "bear":
        phase = "Dow Phase: Correction within bull"
    else:
        phase = "Dow Phase 3: Distribution / Topping"

    return phase, primary, secondary, minor

# === PLOT ===
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(30, 22))
fig.patch.set_facecolor('#0d1117')

# Top: Price + Waves + Dow
ax1 = fig.add_axes([0.04, 0.30, 0.72, 0.66])
ax1.set_facecolor('#0d1117')

# Candles (sample for readability)
step = max(1, n // 200)
for i in range(0, n, step):
    d = plot_data[i]
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax1.plot([i, i], [d['l'], d['h']], color=color, linewidth=0.5)
    y1, y2 = max(d['o'], d['c']), min(d['o'], d['c'])
    ax1.bar(i, y1-y2, 0.65, bottom=y2, color=color, alpha=0.85)

# Moving averages
ax1.plot(range(n), dema10, color='white', linewidth=1.8, label='DEMA10 White', alpha=0.9)
ax1.plot(range(n), quad_ma, color='#d2991d', linewidth=1.8, label='Quad-MA Yellow', alpha=0.9)
ax1.plot(range(n), ma50, color='#58a6ff', linewidth=1.2, label='MA50', alpha=0.7, linestyle=':')
ax1.plot(range(n), ma200, color='#f0883e', linewidth=1.2, label='MA200', alpha=0.7, linestyle=':')

# === Wave Structure Drawing ===
# Identify key wave points from filtered swings
if len(filtered) >= 6:
    # Take the most significant swing points
    wave_labels = []
    for i, (idx, price, stype) in enumerate(filtered):
        # Assign wave labels based on position in cycle
        label = f'{stype}{i+1}'
        wave_labels.append((idx, price, stype, label))

    # Draw wave connections
    for i in range(len(filtered)-1):
        idx1, p1, t1 = filtered[i]
        idx2, p2, t2 = filtered[i+1]
        color = '#3fb950' if t1 == 'L' and t2 == 'H' else '#f85149'
        ax1.plot([idx1, idx2], [p1, p2], color=color, linewidth=1.2, alpha=0.5, linestyle='--')

    # Mark major swing points
    for idx, price, stype in filtered[-8:]:
        color = '#3fb950' if stype == 'L' else '#f85149'
        marker = '^' if stype == 'L' else 'v'
        ax1.plot(idx, price, marker, color=color, markersize=10, markeredgecolor='white', markeredgewidth=1.2, zorder=5)

# === Wave Count Annotation (Manual based on data) ===
# Based on the data: major rally from ~2024 low to 2025-2026 highs, then decline
# Identify the major wave structure

# Find major low (start of rally)
rally_start_idx = None
rally_start_val = float('inf')
for i in range(min(100, n//3)):
    if lows[i] < rally_start_val:
        rally_start_val = lows[i]
        rally_start_idx = i

# Find major high (end of rally) in 2025-2026
rally_end_idx = None
rally_end_val = 0
for i in range(n//3, n):
    if highs[i] > rally_end_val:
        rally_end_val = highs[i]
        rally_end_idx = i

# Find recent low
recent_low_idx = None
recent_low_val = float('inf')
for i in range(rally_end_idx, n):
    if lows[i] < recent_low_val:
        recent_low_val = lows[i]
        recent_low_idx = i

# Wave labels
wave_annotations = []

# Find intermediate wave points
if rally_start_idx and rally_end_idx:
    # Wave 1: find first significant high
    w1_end = None
    for i in range(rally_start_idx, rally_end_idx):
        if highs[i] > highs[rally_start_idx] * 1.3:
            # local peak
            is_peak = True
            for j in range(max(0,i-5), min(n,i+6)):
                if j != i and highs[j] > highs[i]:
                    is_peak = False
                    break
            if is_peak and (w1_end is None or highs[i] > highs[w1_end]):
                w1_end = i

    # Wave 2: first significant low after wave 1
    w2_end = None
    if w1_end:
        for i in range(w1_end, rally_end_idx):
            if lows[i] < lows[w1_end] * 0.85:
                is_trough = True
                for j in range(max(0,i-5), min(n,i+6)):
                    if j != i and lows[j] < lows[i]:
                        is_trough = False
                        break
                if is_trough:
                    w2_end = i
                    break

    # Wave 3: extend to near rally_end
    # Wave 4: find correction before final push
    w4_end = None
    if w2_end and rally_end_idx > w2_end + 20:
        for i in range(rally_end_idx-30, rally_end_idx-5):
            if i > w2_end and lows[i] < lows[rally_end_idx] * 0.7:
                is_trough = True
                for j in range(max(0,i-5), min(n,i+6)):
                    if j != i and lows[j] < lows[i]:
                        is_trough = False
                        break
                if is_trough:
                    w4_end = i
                    break

    wave_annotations.append((rally_start_idx, rally_start_val, 'Wave Start', '#3fb950'))
    if w1_end:
        wave_annotations.append((w1_end, highs[w1_end], 'W1', '#3fb950'))
    if w2_end:
        wave_annotations.append((w2_end, lows[w2_end], 'W2', '#f85149'))
    wave_annotations.append((rally_end_idx, rally_end_val, 'W3(extended)\nMajor Top', '#f85149'))
    if w4_end:
        wave_annotations.append((w4_end, lows[w4_end], 'A-wave low', '#d2991d'))
    wave_annotations.append((recent_low_idx, recent_low_val, f'Recent Low\n{recent_low_val:.2f}', '#d2991d'))

# Draw annotations
for idx, price, label, color in wave_annotations:
    ax1.annotate(label, (idx, price), textcoords='offset points',
                xytext=(0, 20 if 'High' in label or 'W1' in label or 'W3' in label else -22),
                fontsize=9, color=color, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-', color=color, lw=1))
    ax1.plot(idx, price, 'o', color=color, markersize=8, markeredgecolor='white', zorder=5)

# === Fibonacci Retracement ===
if rally_start_idx and rally_end_idx:
    fib_range = rally_end_val - rally_start_val
    fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
    for level in fib_levels:
        fib_price = rally_end_val - fib_range * level
        ax1.axhline(y=fib_price, color='#a371f7', linestyle=':', linewidth=0.8, alpha=0.6)
        ax1.text(rally_end_idx + 5, fib_price, f'{level:.3f} {fib_price:.2f}',
                color='#a371f7', fontsize=7, va='center')

# Current price
ax1.plot(n-1, closes[-1], 'D', color='#d2991d', markersize=10, markeredgecolor='white', zorder=5)
ax1.annotate(f'Now\n{plot_data[-1]["day"]}\n{closes[-1]:.2f}',
            (n-1, closes[-1]), textcoords='offset points', xytext=(30, -10),
            fontsize=10, color='#d2991d', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#d2991d', lw=2))

# === Dow Theory Phase Background ===
# Color-code background based on Dow phases
for i in range(200, n, 5):
    phase, primary, secondary, minor = dow_phase(i)
    if phase and 'Panic' in phase:
        ax1.axvspan(i-2, i+3, alpha=0.05, color='#f85149')
    elif phase and ('Accumulation' in phase or 'Phase 2' in phase):
        ax1.axvspan(i-2, i+3, alpha=0.05, color='#3fb950')
    elif phase and 'Distribution' in phase:
        ax1.axvspan(i-2, i+3, alpha=0.05, color='#d2991d')

# === Current Dow Phase ===
cur_phase, cur_primary, cur_secondary, cur_minor = dow_phase(n-1)

# === Styling ===
ax1.set_title('GUOXUAN HI-TECH (002074) Elliott Wave + Dow Theory Joint Analysis',
              fontsize=14, color='white', fontweight='bold', pad=12)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#30363d')
ax1.spines['bottom'].set_color('#30363d')
ax1.tick_params(colors='#8b949e', labelsize=7)
tick_step = max(1, n // 15)
tick_pos = list(range(0, n, tick_step))
ax1.set_xticks(tick_pos)
ax1.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=7)
ax1.set_ylabel('Price', color='#8b949e', fontsize=10)
ax1.grid(True, alpha=0.08, color='#8b949e')
ax1.set_axisbelow(True)

# Legend
legend_elements = [
    mpatches.Patch(color='white', alpha=0.9, label='DEMA10 (White)'),
    mpatches.Patch(color='#d2991d', alpha=0.9, label='Quad-MA (Yellow)'),
    mpatches.Patch(color='#58a6ff', alpha=0.7, label='MA50'),
    mpatches.Patch(color='#f0883e', alpha=0.7, label='MA200'),
    mpatches.Patch(color='#a371f7', alpha=0.6, label='Fibonacci Levels'),
    mpatches.Patch(color='#3fb950', alpha=0.3, label='Elliott Impulse Wave'),
    mpatches.Patch(color='#f85149', alpha=0.3, label='Elliott Corrective Wave'),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=8,
          facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')

# === Bottom Right: Analysis Panel ===
ax2 = fig.add_axes([0.78, 0.30, 0.20, 0.66])
ax2.set_facecolor('#0d1117')
ax2.axis('off')

# DEMA/Quad status
dead_cross = dema10[-1] < quad_ma[-1]
price_vs_yellow = (closes[-1] - quad_ma[-1]) / quad_ma[-1] * 100

analysis_text = (
    f"GUOXUAN HI-TECH (002074)\n"
    f"==========================\n"
    f"Date: {plot_data[-1]['day']}\n"
    f"Close: {closes[-1]:.2f}\n"
    f"\n"
    f"--- DOW THEORY ---\n"
    f"Primary Trend: {cur_primary.upper()}\n"
    f"Secondary: {cur_secondary.upper()}\n"
    f"Minor: {cur_minor.upper()}\n"
    f"Phase: {cur_phase}\n"
    f"\n"
    f"MA200: {ma200[-1]:.2f}\n"
    f"MA50: {ma50[-1]:.2f}\n"
    f"MA20: {ma20[-1]:.2f}\n"
    f"\n"
    f"--- ELLIOTT WAVE ---\n"
    f"Major rally: {rally_start_val:.2f} -> {rally_end_val:.2f}\n"
    f"Range: {fib_range:.2f}\n"
    f"Current: {closes[-1]:.2f}\n"
    f"\n"
    f"Fibonacci Retracement:\n"
)
for level in fib_levels:
    fib_price = rally_end_val - fib_range * level
    hit = " <-- HERE" if abs(closes[-1] - fib_price) / fib_price < 0.03 else ""
    analysis_text += f"  {level:.3f}: {fib_price:.2f}{hit}\n"

analysis_text += (
    f"\n"
    f"--- 标准战法 ---\n"
    f"DEMA10: {dema10[-1]:.2f}\n"
    f"QuadMA: {quad_ma[-1]:.2f}\n"
    f"Status: {'DEAD CROSS' if dead_cross else 'OK'}\n"
    f"Price vs Yellow: {price_vs_yellow:.1f}%\n"
    f"\n"
    f"--- KEY LEVELS ---\n"
    f"Support: {recent_low_val:.2f} (recent low)\n"
    f"Resist 1: {ma20[-1]:.2f} (MA20)\n"
    f"Resist 2: {ma50[-1]:.2f} (MA50)\n"
    f"Resist 3: {ma200[-1]:.2f} (MA200)\n"
)

ax2.text(0.02, 0.98, analysis_text, transform=ax2.transAxes,
         fontsize=7.5, color='#c9d1d9', fontfamily='monospace',
         verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                  edgecolor='#30363d', alpha=0.92))

# === Bottom: Volume + Dow Theory Phase Indicator ===
ax3 = fig.add_axes([0.04, 0.15, 0.72, 0.12])
ax3.set_facecolor('#0d1117')
colors_vol = ['#3fb950' if plot_data[i]['c'] >= plot_data[i]['o'] else '#f85149' for i in range(n)]
ax3.bar(range(n), vols/10000, color=colors_vol, alpha=0.6, width=0.8)
vol_ma20 = sma(vols, 20)
ax3.plot(range(n), vol_ma20/10000, color='#d2991d', linewidth=1, alpha=0.8)
ax3.set_ylabel('Vol(10k)', color='#8b949e', fontsize=8)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.spines['left'].set_color('#30363d')
ax3.spines['bottom'].set_color('#30363d')
ax3.tick_params(colors='#8b949e', labelsize=7)
ax3.set_xticks(tick_pos)
ax3.set_xticklabels([dates[i] for i in tick_pos], rotation=45, fontsize=7)
ax3.grid(True, alpha=0.08, color='#8b949e')
ax3.set_axisbelow(True)

# === Bottom-2: Dow Theory Trend Indicator ===
ax4 = fig.add_axes([0.04, 0.04, 0.72, 0.10])
ax4.set_facecolor('#0d1117')

# Compute trend strength: +1 for each bullish MA crossover, -1 for bearish
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
ax4.axhline(y=3, color='#3fb950', linewidth=0.5, linestyle=':', alpha=0.4)
ax4.axhline(y=-3, color='#f85149', linewidth=0.5, linestyle=':', alpha=0.4)
ax4.set_ylabel('Trend', color='#8b949e', fontsize=8)
ax4.set_ylim(-3.5, 3.5)
ax4.set_yticks([-3, 0, 3])
ax4.set_yticklabels(['BEAR (-3)', 'Neutral (0)', 'BULL (+3)'], fontsize=7, color='#8b949e')
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)
ax4.spines['left'].set_color('#30363d')
ax4.spines['bottom'].set_color('#30363d')
ax4.tick_params(colors='#8b949e', labelsize=7)
ax4.set_xticks(tick_pos)
ax4.set_xticklabels([], fontsize=7)  # hide x labels
ax4.grid(True, alpha=0.08, color='#8b949e')
ax4.set_axisbelow(True)
ax4.set_title('Dow Theory Trend Score (Price>MA20 + MA20>MA50 + MA50>MA200 = 3 Bull / -3 Bear)',
             fontsize=8, color='#8b949e', pad=3)

# Save
outpath = 'D:/Trade/new_tdx64/Guoxuan_002074_Wave_Dow.png'
fig.savefig(outpath, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
plt.close()

size_kb = os.path.getsize(outpath) / 1024
print(f'OK: {outpath} ({size_kb:.0f} KB)')
print(f'Records: {n} ({plot_data[0]["day"]} -> {plot_data[-1]["day"]})')
print(f'Close: {closes[-1]:.2f}')
print(f'Rally: {rally_start_val:.2f} -> {rally_end_val:.2f} (range {fib_range:.2f})')
print(f'Recent low: {recent_low_val:.2f} at idx {recent_low_idx}')
print(f'Dow Phase: {cur_phase}')
print(f'Primary: {cur_primary} | Secondary: {cur_secondary} | Minor: {cur_minor}')
print(f'DEMA10: {dema10[-1]:.2f} | QuadMA: {quad_ma[-1]:.2f} | DeadCross: {dead_cross}')
print(f'Price vs yellow: {price_vs_yellow:.1f}%')
print(f'Trend score: {trend_score[-1]}')

# Fibonacci summary
print(f'\nFibonacci levels (from {rally_end_val:.2f} top):')
for level in fib_levels:
    fib_price = rally_end_val - fib_range * level
    mark = ' <<<' if abs(closes[-1] - fib_price) / fib_price < 0.03 else ''
    print(f'  {level:.3f}: {fib_price:.2f}{mark}')
