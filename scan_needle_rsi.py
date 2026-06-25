import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('D:/Trading Workflow/Stock_lab_system/data/cache/second_pass_results.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Find RSI < 20
low_rsi = []
for r in d['results']:
    t = r.get('tactics', {})
    n = r.get('needle', {})
    rsi3 = t.get('rsi3', 50)
    if rsi3 < 20:
        low_rsi.append([r['code'], r['name'], r['close'], rsi3, t.get('kdj_j',50), n.get('white_line',100), n.get('red_line',0), n.get('signal_triggered',False), n.get('valid_signal',False)])

print("=== RSI3 < 20 stocks ===")
if low_rsi:
    low_rsi.sort(key=lambda x: x[3])
    for f in low_rsi:
        print(f"  {f[0]} {f[1]:<8} | C={f[2]:.2f} | RSI3={f[3]:.1f} J={f[4]:.1f} | White={f[5]:.1f} Red={f[6]:.1f} | NeedleTrig={f[7]} Valid={f[8]}")
else:
    print("  NONE! 0 stocks with RSI3 < 20 today")

# Find any needle signals
needle_hits = []
for r in d['results']:
    n = r.get('needle', {})
    t = r.get('tactics', {})
    if n.get('signal_triggered') or n.get('valid_signal') or n.get('four_zero'):
        needle_hits.append([r['code'], r['name'], r['close'], n.get('white_line',100), n.get('red_line',0), n.get('signal_triggered'), n.get('valid_signal'), n.get('four_zero'), t.get('rsi3',50), n.get('bbi_up')])

print("\n=== Any needle signal ===")
if needle_hits:
    for f in needle_hits:
        print(f"  {f[0]} {f[1]} | White={f[3]:.1f} Red={f[4]:.1f} | Trig={f[5]} Valid={f[6]} FourZero={f[7]} | RSI3={f[8]:.1f} BBIup={f[9]}")
else:
    print("  NONE! 0 needle signals today")

# White < 25 (near trigger)
near = []
for r in d['results']:
    n = r.get('needle', {})
    t = r.get('tactics', {})
    w = n.get('white_line', 100)
    if w <= 25:
        near.append([r['code'], r['name'], r['close'], w, n.get('red_line',0), t.get('rsi3',50), t.get('kdj_j',50), n.get('bbi_up'), n.get('price_above_bbi')])

print(f"\n=== White line <= 25 (near needle trigger, {len(near)} stocks) ===")
near.sort(key=lambda x: x[3])
for f in near[:20]:
    print(f"  {f[0]} {f[1]:<10} C={f[2]:.2f} White={f[3]:.1f} Red={f[4]:.1f} RSI3={f[5]:.1f} J={f[6]:.1f} BBIup={f[7]} P>BBI={f[8]}")

print(f"\nStats: total={d['total_scanned']} N3=80 N4=20")
print(f"Needle signals: {d['stats'].get('单针下20有效','?')}")
