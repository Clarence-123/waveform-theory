import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np, os

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(16, 11))
fig.patch.set_facecolor('#0d1117')

ax1 = fig.add_axes([0.08, 0.15, 0.60, 0.78])
ax1.set_facecolor('#0d1117')

# Build candles explicitly
np.random.seed(42)
candles = []

# 1-20: downtrend
price = 50.0
for i in range(20):
    chg = np.random.normal(-0.6, 1.2)
    o = price
    c = o + chg
    h = max(o, c) + abs(np.random.normal(0.2, 0.4))
    l = min(o, c) - abs(np.random.normal(0.2, 0.4))
    candles.append({'o': o, 'c': c, 'h': h, 'l': l})
    price = c

# 21: big bear (Day 1 of Morning Star)
bear_o = price
bear_c = price - 3.8
bear_h = bear_o + 0.8
bear_l = bear_c - 0.5
candles.append({'o': bear_o, 'c': bear_c, 'h': bear_h, 'l': bear_l})
bear_idx = 20
price = bear_c

# 22: small star (Day 2) - gap down
star_o = bear_c - 1.0
star_c = star_o + 0.15
star_h = star_o + 0.6
star_l = star_o - 0.4
candles.append({'o': star_o, 'c': star_c, 'h': star_h, 'l': star_l})
star_idx = 21
price = star_c

# 23: big bull (Day 3)
bull_o = star_c + 0.3
bull_c = bear_o - 0.5  # close into body of candle 1
bull_h = bull_c + 1.2
bull_l = bull_o - 0.3
candles.append({'o': bull_o, 'c': bull_c, 'h': bull_h, 'l': bull_l})
bull_idx = 22
price = bull_c

# 24-30: recovery
for i in range(7):
    chg = np.random.normal(0.5, 0.9)
    o = price
    c = o + chg
    h = max(o, c) + abs(np.random.normal(0.3, 0.4))
    l = min(o, c) - abs(np.random.normal(0.2, 0.3))
    candles.append({'o': o, 'c': c, 'h': h, 'l': l})
    price = c

n = len(candles)

# Draw candles
for i, d in enumerate(candles):
    color = '#3fb950' if d['c'] >= d['o'] else '#f85149'
    ax1.plot([i, i], [d['l'], d['h']], color=color, linewidth=1.2)
    body_h = max(0.08, abs(d['c'] - d['o']))
    ax1.bar(i, body_h, 0.7, bottom=min(d['o'], d['c']), color=color, alpha=0.9)

# Box around Morning Star
ax1.add_patch(patches.Rectangle((bear_idx-0.6, star_l-0.5), 2.2, bull_h-star_l+1.0,
              linewidth=2.5, edgecolor='#d2991d', facecolor='none', linestyle='-'))

# Labels
ax1.annotate('1. Big Bear\n   Panic Selling',
            xy=(bear_idx, candles[bear_idx]['l']),
            textcoords='offset points', xytext=(-20, -55),
            fontsize=10, color='#f85149', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#f85149', lw=1.5))

ax1.annotate('2. Small Star\n   Selling Exhausted',
            xy=(star_idx, candles[star_idx]['l']),
            textcoords='offset points', xytext=(0, -55),
            fontsize=10, color='#d2991d', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#d2991d', lw=1.5))

ax1.annotate('3. Big Bull\n   Buyers Take Control',
            xy=(bull_idx, candles[bull_idx]['h']),
            textcoords='offset points', xytext=(18, 20),
            fontsize=10, color='#3fb950', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#3fb950', lw=1.5))

# Gap arrow
ax1.annotate('', xy=(star_idx-0.1, star_o+0.05), xytext=(bear_idx+0.1, bear_c-0.05),
            arrowprops=dict(arrowstyle='<->', color='#a371f7', lw=1.8))
ax1.text(bear_idx+0.5, bear_c-0.35, 'Gap Down', fontsize=9, color='#a371f7', ha='center', fontweight='bold')

# Close-back line
ax1.axhline(y=bear_o, xmin=(bear_idx-0.3)/n, xmax=(bull_idx+0.3)/n,
           color='#a371f7', linewidth=1, linestyle=':', alpha=0.7)
ax1.text(bull_idx, bear_o+0.1, f'  Candle3 closes into Candle1 body', fontsize=8, color='#a371f7')

# Title
ax1.text(bear_idx+1, bull_h+1.5, '★ Morning Star (启明星) ★',
         fontsize=16, color='#d2991d', fontweight='bold', ha='center')

# Styling
ax1.set_xlim(-1.5, n)
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#30363d'); ax1.spines['bottom'].set_color('#30363d')
ax1.tick_params(colors='#8b949e', labelsize=8)
ticks = [0, 5, 10, 15, bear_idx, star_idx, bull_idx, 25, 27, 29]
labels = ['...', '...', '...', '...', 'Day1\n大阴', 'Day2\n十字星', 'Day3\n大阳', '...', '...', '...']
ax1.set_xticks(ticks); ax1.set_xticklabels(labels, fontsize=8)
ax1.grid(True, alpha=0.07, color='#8b949e'); ax1.set_axisbelow(True)
ax1.set_title('Morning Star (启明星) — Three-Candle Bullish Reversal Pattern',
             fontsize=13, color='white', fontweight='bold', pad=10)

# === Right panel ===
ax2 = fig.add_axes([0.72, 0.15, 0.25, 0.78])
ax2.set_facecolor('#0d1117'); ax2.axis('off')

text = (
    "启明星 (MORNING STAR)\n"
    "========================\n"
    "\n"
    "三根K线构成:\n"
    "\n"
    "① 大阴线\n"
    "   下降趋势末端出现\n"
    "   空头最后的宣泄\n"
    "   含义: 恐慌抛售\n"
    "\n"
    "② 十字星/小K线\n"
    "   跳空低开(衰竭缺口)\n"
    "   实体极小, 振幅收窄\n"
    "   含义: 空头推不动了!\n"
    "\n"
    "③ 大阳线\n"
    "   实体长, 放量\n"
    "   收盘回到①的实体内部\n"
    "   含义: 多头接手\n"
    "\n"
    "确认条件:\n"
    "• ③收盘 > ①实体的50%\n"
    "• 次日继续上涨\n"
    "• ③放量 > ②的2倍\n"
    "\n"
    "与暴力K线的关系:\n"
    "如果③满足:\n"
    "  底部位置 ✓\n"
    "  实体 >= 5% ✓\n"
    "  量 >= 前日2倍 ✓\n"
    "  → A类暴力K线!\n"
    "  → 趋势扭转信号\n"
    "  → 可作为止损锚\n"
    "\n"
    "最佳出现位置:\n"
    "• 长期下跌后(跌30%+)\n"
    "• 重要支撑位(MA/Fib)\n"
    "• 成交量出现地量后放量\n"
    "\n"
    "常见错误:\n"
    "• 下降中继的伪启明星\n"
    "  (③太小, 量不足)\n"
    "• 没有次日确认就追\n"
)

ax2.text(0.02, 0.98, text, transform=ax2.transAxes, fontsize=8, color='#c9d1d9',
         fontfamily='monospace', verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22', edgecolor='#30363d', alpha=0.92))

outpath = 'D:/Trade/new_tdx64/MorningStar_启明星.png'
fig.savefig(outpath, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
plt.close()
print(f'OK: {outpath} ({os.path.getsize(outpath)/1024:.0f} KB)')
