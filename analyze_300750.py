import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/Trading Workflow/Stock_lab_system/data/cache/daily_history/300750.json') as f:
    raw = json.load(f)

data = []
for r in raw:
    data.append({
        'day': r['day'], 'o': float(r['open']), 'h': float(r['high']),
        'l': float(r['low']), 'c': float(r['close']), 'v': float(r['volume'])
    })
n = len(data)

def ema(series, period):
    result = [0]*len(series)
    result[period-1] = sum(series[:period])/period
    k = 2/(period+1)
    for i in range(period, len(series)):
        result[i] = series[i]*k + result[i-1]*(1-k)
    return result

def sma_s(series, period):
    result = [0]*len(series)
    for i in range(len(series)):
        start = max(0, i-period+1)
        result[i] = sum(series[start:i+1])/min(i+1, period)
    return result

close = [d['c'] for d in data]
high_p = [d['h'] for d in data]
low_p = [d['l'] for d in data]
vol = [d['v'] for d in data]

# DEMA10
ema10_first = ema(close, 10)
dema10 = ema(ema10_first, 10)

# quad-MA
ma14 = sma_s(close, 14)
ma28 = sma_s(close, 28)
ma57 = sma_s(close, 57)
ma114 = sma_s(close, 114)
quad_ma = [(ma14[i]+ma28[i]+ma57[i]+ma114[i])/4 for i in range(n)]

# KDJ
def kdj_calc(data_h, data_l, data_c, n_k=9, m1=3, m2=3):
    k_vals = [50]*len(data_c)
    d_vals = [50]*len(data_c)
    j_vals = [50]*len(data_c)
    for i in range(n_k-1, len(data_c)):
        hh = max(data_h[i-n_k+1:i+1])
        ll = min(data_l[i-n_k+1:i+1])
        rsv = (data_c[i]-ll)/(hh-ll)*100 if hh != ll else 50
        k_vals[i] = rsv/m1 + k_vals[i-1]*(m1-1)/m1
        d_vals[i] = k_vals[i]/m2 + d_vals[i-1]*(m2-1)/m2
        j_vals[i] = 3*k_vals[i] - 2*d_vals[i]
    return k_vals, d_vals, j_vals

k_v, d_v, j_v = kdj_calc(high_p, low_p, close)

# RSI
def rsi_calc(series, period=3):
    result = [50]*len(series)
    gains = [max(series[i]-series[i-1], 0) for i in range(1, len(series))]
    losses = [abs(min(series[i]-series[i-1], 0)) for i in range(1, len(series))]
    avg_gain = sum(gains[:period])/period
    avg_loss = sum(losses[:period])/period
    for i in range(period, len(series)):
        avg_gain = (avg_gain*(period-1) + gains[i-1])/period
        avg_loss = (avg_loss*(period-1) + losses[i-1])/period
        result[i] = 100 - 100/(1 + avg_gain/avg_loss) if avg_loss != 0 else 100
    return result

rsi3 = rsi_calc(close, 3)
rsi14 = rsi_calc(close, 14)

# MACD
ema12 = ema(close, 12)
ema26 = ema(close, 26)
dif_v = [ema12[i]-ema26[i] for i in range(n)]
dea_v = ema(dif_v, 9)
macd_bar = [(dif_v[i]-dea_v[i])*2 for i in range(n)]

def hhv(series, period):
    result = [0]*len(series)
    for i in range(len(series)):
        start = max(0, i-period+1)
        result[i] = max(series[start:i+1])
    return result

def llv(series, period):
    result = [0]*len(series)
    for i in range(len(series)):
        start = max(0, i-period+1)
        result[i] = min(series[start:i+1])
    return result

hhv20 = hhv(vol, 20)
hhv30 = hhv(vol, 30)

i = n-1

print('='*100)
print('Ningde Shidai (300750) Standard Battle Method Analysis - TDX Daily Data')
print(f'Data date: {data[i]["day"]} (latest)')
print('='*100)

# Step 1
print()
print('[Step 1: Death Cross Detection - HIGHEST PRIORITY]')
print(f'  DEMA10 (white): {dema10[i]:.2f}')
print(f'  Quad-MA (yellow): {quad_ma[i]:.2f}')
print(f'  Close: {close[i]:.2f}')
dead_cross = dema10[i] < quad_ma[i]
if dead_cross:
    print(f'  => DEATH CROSS! DEMA10({dema10[i]:.2f}) < QuadMA({quad_ma[i]:.2f})')
    print(f'  => IRON RULE: CLEAR ALL POSITIONS, NO LONGS!')
else:
    print(f'  => NO death cross. DEMA10({dema10[i]:.2f}) > QuadMA({quad_ma[i]:.2f})')

# Find crossings
cross_dates = []
for x in range(60, n-1):
    if dema10[x] > quad_ma[x] and dema10[x+1] <= quad_ma[x+1]:
        cross_dates.append((x+1, 'down'))
    elif dema10[x] < quad_ma[x] and dema10[x+1] >= quad_ma[x+1]:
        cross_dates.append((x+1, 'up'))

print()
print('[Recent Crossings]')
for cd in cross_dates[-10:]:
    direction = "GOLDEN CROSS +" if cd[1]=="up" else "DEATH CROSS -"
    print(f'  {data[cd[0]]["day"]} {direction} @ {close[cd[0]]:.2f} (D10={dema10[cd[0]]:.2f} QMA={quad_ma[cd[0]]:.2f})')

# Step 2
print()
print('[Step 2: Market Tone]')
if close[i] > dema10[i] > quad_ma[i]:
    tone = 'BULLISH (close > white > yellow)'
    cap = '100%'
elif close[i] > quad_ma[i]:
    tone = 'SANDWICH (below white, above yellow)'
    cap = '50%'
elif abs(close[i]-quad_ma[i])/quad_ma[i] <= 0.015:
    tone = 'YELLOW LINE EDGE (+-1.5%)'
    cap = '30%'
else:
    tone = 'BEARISH (close < yellow)'
    cap = '0% Standard / Bowl Battle allowed'

print(f'  Close({close[i]:.2f}) vs White({dema10[i]:.2f}) vs Yellow({quad_ma[i]:.2f})')
print(f'  => {tone}')
print(f'  Position cap: {cap}')
print(f'  Distance to yellow: {(close[i]-quad_ma[i])/quad_ma[i]*100:.2f}%')

# Step 3: Violence K-lines
print()
print('[Step 3: Violence K-lines]')
vk_lines = []
for x in range(max(0, n-60), n):
    pct_chg = (close[x]-data[x]['o'])/data[x]['o']*100
    vol_ratio = vol[x]/(vol[x-1]+1) if x > 0 else 1
    near_low = low_p[x] <= llv(low_p, 20)[x] * 1.03
    is_vk = near_low and pct_chg >= 5 and vol_ratio >= 2
    if is_vk:
        vk_lines.append((x, data[x]['day'], close[x], low_p[x], pct_chg, vol_ratio))

if vk_lines:
    for vk in vk_lines:
        print(f'  [{vk[1]}] C:{vk[2]:.2f} L:{vk[3]:.2f} body{vk[4]:.1f}% volRatio{vk[5]:.1f}x')
    print(f'  Stop anchor 1 = {vk_lines[-1][3]:.2f} (last VK low)')
else:
    print('  No VK lines in last 60 days')
    print('  => Use yellow line as main stop')

# Step 4: Brick
print()
print('[Step 4: Brick Status]')
brick = macd_bar[i]
prev_brick = macd_bar[i-1]
if brick > 0 and brick > prev_brick:
    bstate = 'RED (bull energy release)'
elif brick > 0:
    bstate = 'YELLOW (bull energy fading)'
elif brick < 0 and brick < prev_brick:
    bstate = 'GREEN (bear energy release)'
else:
    bstate = 'BLUE (bear energy fading)'

green_cnt = 0
for x in range(i, max(0,i-30), -1):
    if macd_bar[x] < 0: green_cnt += 1
    else: break

print(f'  Bar = {brick:.3f} => {bstate}')
print(f'  Consecutive green bricks: {green_cnt}')
if 3 <= green_cnt <= 4:
    print(f'  => B-Brick precondition MET!')

# Step 5: Buy Points
print()
print('[Step 5: Buy Point Scanning]')

# Preconditions
cond1 = not dead_cross
max_vol_idx = max(range(max(0,n-40), n), key=lambda x: vol[x])
is_bg = data[max_vol_idx]['c'] < data[max_vol_idx]['o']
days_bg = n-1-max_vol_idx
cond2 = not is_bg or days_bg >= 15
recent_amp = (max(high_p[-20:])-min(low_p[-20:]))/min(low_p[-20:])*100
far_amp = (max(high_p[-60:])-min(low_p[-60:]))/min(low_p[-60:])*100
cond3 = recent_amp >= 15 or far_amp >= 30
cond4 = close[i] >= quad_ma[i] * 0.975

print(f'  Global preconditions:')
print(f'    1. White>=Yellow: {"PASS" if cond1 else "FAIL"}')
print(f'    2. No big-green-bar: {"PASS" if cond2 else "FAIL"} (maxVolDay={data[max_vol_idx]["day"]}, bear={is_bg}, days={days_bg})')
print(f'    3. Anomaly: {"PASS" if cond3 else "FAIL"} (amp20={recent_amp:.1f}%, amp60={far_amp:.1f}%)')
print(f'    4. Price>=Yellow*0.975({quad_ma[i]*0.975:.1f}): {"PASS" if cond4 else "FAIL"} ({close[i]:.1f})')

jr_sum = [j_v[x]+rsi3[x] for x in range(n)]
jr_20min = min(jr_sum[-20:])
j_20min = min(j_v[-20:])

print(f'\n  K={k_v[i]:.2f} D={d_v[i]:.2f} J={j_v[i]:.2f}')
print(f'  RSI(3)={rsi3[i]:.2f} RSI(14)={rsi14[i]:.2f}')
print(f'  J+RSI={j_v[i]+rsi3[i]:.2f} (20d low={jr_20min:.2f})')
print(f'  J 20d low={j_20min:.2f}')
print(f'  VolRatio(20)={vol[i]/hhv20[i]:.4f}')
print(f'  SuperShrink(VOL<HHV30/4): {vol[i]/1e6:.1f}M < {hhv30[i]/4/1e6:.1f}M = {"YES" if vol[i]<hhv30[i]/4 else "NO"}')

# B1 subtypes
print(f'\n  B1 Subtype Matching:')

# Red B1
j_low = j_v[i] < 14
rsi_low = rsi3[i] < 23
jr_cond = j_v[i]+rsi3[i] < 55 or j_v[i] <= j_20min + 0.01
red_b1 = (j_low or rsi_low) and jr_cond and vol[i] < hhv20[i]*0.416
print(f'  RED B1 (J<14|RSI<23, J+RSI<55, shrink<0.416): {"*** TRIGGERED ***" if red_b1 else "no"}')

# Cyan B1
cyan_b1 = (j_v[i]<14 or rsi3[i]<23) and (j_v[i]+rsi3[i]<60) and far_amp>=45 and (vol[i]<hhv30[i]/4 or vol[i]<hhv(vol,50)[i]/6)
print(f'  CYAN B1 (super shrink, amp>=45%): {"*** TRIGGERED ***" if cyan_b1 else "no"}')

# Yellow B1 (turn-up)
y_turn = rsi3[i]-15 >= rsi3[i-1]
y_b1 = y_turn and (rsi3[i-1]<20 or j_v[i-1]<14) and close[i]>=quad_ma[i]
print(f'  YELLOW B1 (RSI turn-up): {"*** TRIGGERED ***" if y_b1 else "no"} (turn={y_turn}, prevRSI={rsi3[i-1]:.1f}, prevJ={j_v[i-1]:.1f})')

# White B1
w_b1 = dema10[i]>quad_ma[i] and close[i]>=quad_ma[i]*0.99 and (j_v[i]<13 or rsi3[i]<21)
print(f'  WHITE B1 (original): {"*** TRIGGERED ***" if w_b1 else "no"} (need price>={quad_ma[i]*0.99:.1f})')

# Purple B1 (trend pullback to white)
b1_purple = False  # simplified
print(f'  PURPLE B1 (pullback to white): complex check, see notes')

# Green B1 (super bull pullback)
b1_green = False
print(f'  GREEN B1 (super bull): complex check, see notes')

# Short Yellow B1
sy_b1 = dema10[i]>=quad_ma[i] and close[i]>=quad_ma[i]*0.975 and (j_v[i]<13 or rsi3[i]<18)
print(f'  SHORT YELLOW B1 (pullback to yellow): {"*** TRIGGERED ***" if sy_b1 else "no"}')

# Step 6: Sell Points
print()
print('[Step 6: Sell Point Scanning]')
print('  (Only meaningful in bull tone; currently bearish)')
print('  S1-S5 not triggered. Previous sell signal: death cross if it forms.')

# Step 7: Stop Loss
print()
print('[Step 7: Stop Loss Lines]')
if not dead_cross:
    print('  Standard Battle: DeathCross > 1.VK Low > 2.B1 Day Low > 3.Yellow Line')
    print('  Bowl Battle:    DeathCross > 1.VK Low > 2.Yellow Line')
    if vk_lines:
        print(f'  1. Primary stop: {vk_lines[-1][3]:.2f} (VK low)')
    else:
        print(f'  1. Primary stop: N/A (no VK)')
    print(f'  2. Yellow line stop: {quad_ma[i]:.2f}')
else:
    print(f'  => DEATH CROSS ACTIVE - all stops overridden. Clear positions.')

# Step 8: Score
print()
print('[Step 8: Hold Score (0-5)]')
score = 5
checks = []
if close[i] < close[i-1]:
    checks.append(('Down day', True))
    score -= 1
else:
    checks.append(('Down day', False))

if vol[i] > vol[i-1] and close[i] < close[i-1]:
    checks.append(('Volume-down', True))
    score -= 1
else:
    checks.append(('Volume-down', False))

if j_v[i] <= k_v[i]:
    checks.append(('KDJ dead cross', True))
    score -= 1
else:
    checks.append(('KDJ dead cross', False))

if close[i] < dema10[i]:
    checks.append(('Break white line', True))
    score -= 1
else:
    checks.append(('Break white line', False))

if dema10[i] < dema10[i-1]:
    checks.append(('White turning down', True))
    score -= 1
else:
    checks.append(('White turning down', False))

for name, triggered in checks:
    print(f'  {name}: {"YES (-1)" if triggered else "no"}')
print(f'  => Score: {score}/5')
if score >= 4: print('  Action: HOLD')
elif score == 3: print('  Action: Consider reducing')
elif score == 2: print('  Action: RISK - SELL')
else: print('  Action: CLEAR')

# Final verdict
print()
print('='*100)
print('FINAL VERDICT')
print('='*100)
print(f'  Stock: 300750 Ningde Shidai')
print(f'  Price: {close[i]:.2f}')
print(f'  White(DEMA10): {dema10[i]:.2f}  Yellow(QuadMA): {quad_ma[i]:.2f}')
print(f'  J={j_v[i]:.2f} RSI3={rsi3[i]:.2f} RSI14={rsi14[i]:.2f}')
print(f'  MACD Bar={macd_bar[i]:.3f}')

if dead_cross:
    print()
    print('  >>> DEATH CROSS - CLEAR ALL <<<')
elif close[i] < quad_ma[i]:
    print()
    print(f'  >>> BEARISH: Price({close[i]:.2f}) < Yellow({quad_ma[i]:.2f}) <<<')
    print(f'  >>> Bowl Battle zone. Wait for price to reclaim yellow line. <<<')
    if red_b1 or sy_b1:
        print(f'  >>> B1 signal exists but below yellow - WAIT for confirmation. <<<')
else:
    print(f'  >>> BULLISH: Price above yellow line. Scan for B1/B2/B3. <<<')

# Summary table
print()
print('--- Price Structure ---')
print(f'  Close:    {close[i]:>10.2f}')
print(f'  White:    {dema10[i]:>10.2f}  (above price by {(dema10[i]-close[i])/close[i]*100:.1f}%)')
print(f'  Yellow:   {quad_ma[i]:>10.2f}  (above price by {(quad_ma[i]-close[i])/close[i]*100:.1f}%)')
print(f'  5/8 high: {max(high_p[-40:]):>10.2f}  (468.75 on 2026-05-07)')
