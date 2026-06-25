import json, sys, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/Trading Workflow/Stock_lab_system/data/cache/second_pass_results.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

results = d['results']

# ====== Sina 实时行情覆盖 ======
# 从新浪实时接口批量获取今日收盘价，覆盖 TDX K线里的旧价格
def fetch_sina_realtime(codes):
    """批量获取新浪实时行情，返回 {code: price}"""
    BATCH = 800
    prices = {}
    for i in range(0, len(codes), BATCH):
        batch = codes[i:i+BATCH]
        symbols = ','.join(f"{'sh' if c.startswith(('6','5','9')) else 'sz'}{c}" for c in batch)
        url = f"https://hq.sinajs.cn/list={symbols}"
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://finance.sina.com.cn'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode('gbk')
            for line in raw.strip().split('\n'):
                if '=' not in line or not line.startswith('var '):
                    continue
                # var hq_str_sz002407="name,open,prev_close,price,high,low,..."
                try:
                    code_part = line.split('=')[0].replace('var hq_str_sh','').replace('var hq_str_sz','')
                    fields = line.split('"')[1].split(',')
                    if len(fields) > 3:
                        code = code_part[-6:]  # last 6 chars = stock code
                        price = float(fields[3])  # current price (收盘/实时)
                        if price > 0:
                            prices[code] = price
                except (IndexError, ValueError):
                    continue
        except Exception as e:
            print(f"  [WARN] Sina realtime fetch failed batch {i}: {e}")
        if i + BATCH < len(codes):
            time.sleep(0.3)  # 批次间短暂间隔
    return prices

# 收集所有需要的code并批量获取价格
all_codes = list(set(r['code'] for r in results))
print(f"Fetching Sina realtime prices for {len(all_codes)} stocks...")
sina_prices = fetch_sina_realtime(all_codes)
overlaid = 0
for r in results:
    code = r['code']
    if code in sina_prices and sina_prices[code] > 0:
        old_close = r.get('close', 0)
        r['close'] = sina_prices[code]
        if abs(r['close'] - old_close) > 0.01:
            overlaid += 1
print(f"Price overlay: {overlaid}/{len(results)} updated, {len(sina_prices)} fetched")
# ====== End Sina 实时行情覆盖 ======

# === Section 1: B1 candidates (日线B点候选) ===
b1_candidates = [r for r in results if 'B1买入' in r.get('verdict','')]
b1_candidates.sort(key=lambda r: r.get('tactics_score', 0), reverse=True)

# Split top/bottom halves
half = min(110, len(b1_candidates) // 2 + 1)
top_half = b1_candidates[:half]
bottom_half = b1_candidates[half:]

def fmt_row(r, prio='⭐'):
    t = r['tactics']
    return f"| {prio} | {r['code']} | {r['name']} | 日线 B1({t.get('b1_subtype','?')}) | {r['close']:.2f} | {t.get('stop_primary',0):.2f} | {t.get('tone','?')}/{t.get('brick','?')}{'/B2共振' if t.get('b2_recent_5d') else ''} | 标准战法 | {r.get('jrx',{}).get('base_momentum',0):.0f}+{r.get('jrx',{}).get('x_momentum',0):.0f} | {r.get('tactics_score',0)} |"

# --- Section 1: B1 (top) ---
msg1 = f"## 1. 日线B点候选 ({len(b1_candidates)}只)\n\n"
msg1 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg1 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in top_half:
    msg1 += fmt_row(r) + '\n'
msg1 += f"\n> 上半部分 {len(top_half)}/{len(b1_candidates)} 只\n"
msg1 += f"\n## 1. 日线B点候选（续）({len(b1_candidates)}只)\n\n"
msg1 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg1 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in bottom_half:
    msg1 += fmt_row(r, '🔶') + '\n'
msg1 += f"\n> 下半部分 {len(bottom_half)} 只\n"

with open('D:/Trading Workflow/happyclaw/happyclaw-b67af782f44e3c117ae0f3a6dbf541abe0b3253f/data/groups/main/msg1_b1_top.md', 'w', encoding='utf-8') as f:
    f.write(msg1)
print(f"Section 1: {len(top_half)}+{len(bottom_half)} B1 candidates")

# === Section 2: 周线B点候选 (B2+B1 resonance + momentum) ===
b2_candidates = [r for r in results if 'B2加仓' in r.get('verdict','') and r.get('tactics',{}).get('b1_recent_10d') and r.get('tactics',{}).get('tone','') in ['多头', '夹心']]
b2_candidates.sort(key=lambda r: r.get('tactics_score', 0), reverse=True)
top_b2 = b2_candidates[:34]

msg2 = f"## 2. 周线B点候选 (B2加仓+动能筛选, {len(b2_candidates)}只)\n\n"
msg2 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg2 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in top_b2:
    t = r['tactics']
    jx = r.get('jrx', {})
    msg2 += f"| {'⭐' if r.get('tactics_score',0)>=100 else '🔶'} | {r['code']} | {r['name']} | 周线 B2+B1共振 | {r['close']:.2f} | {t.get('stop_primary',0):.2f} | {t.get('tone','?')}{'/缩量' if t.get('shrink') else ''}{'/黄砖' if t.get('brick')=='黄' else ''} | 标准战法 | {jx.get('base_momentum',0):.0f}+{jx.get('x_momentum',0):.0f} | {r.get('tactics_score',0)} |\n"

with open('D:/Trading Workflow/happyclaw/happyclaw-b67af782f44e3c117ae0f3a6dbf541abe0b3253f/data/groups/main/msg2_weekly.md', 'w', encoding='utf-8') as f:
    f.write(msg2)
print(f"Section 2: {len(top_b2)} weekly B2 candidates")

# === Section 3: 短线推荐 (回踩白线紫) ===
short_b1 = [r for r in b1_candidates if r.get('tactics',{}).get('b1_subtype') in ['回踩白线B','缩量拐头B']]
short_b1.sort(key=lambda r: r.get('tactics_score', 0), reverse=True)
top_short = short_b1[:60]

msg3 = f"## 3. 标准战法短线推荐 — 回踩白线紫 ({len(short_b1)}只)\n\n"
msg3 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg3 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in top_short:
    t = r['tactics']
    jx = r.get('jrx', {})
    msg3 += f"| {'⭐' if r.get('tactics_score',0)>=100 else '🔶'} | {r['code']} | {r['name']} | 短线 B1({t.get('b1_subtype','?')}) | {r['close']:.2f} | {t.get('stop_primary',0):.2f} | {t.get('tone','?')}/J={t.get('kdj_j',0):.0f} | 标准战法 | {jx.get('base_momentum',0):.0f}+{jx.get('x_momentum',0):.0f} | {r.get('tactics_score',0)} |\n"

with open('D:/Trading Workflow/happyclaw/happyclaw-b67af782f44e3c117ae0f3a6dbf541abe0b3253f/data/groups/main/msg3_short.md', 'w', encoding='utf-8') as f:
    f.write(msg3)
print(f"Section 3: {len(top_short)} short-term candidates")

# === Section 4: 中线 + 单针 ===
# 中线 (回踩黄线短黄)
mid_b1 = [r for r in b1_candidates if r.get('tactics',{}).get('b1_subtype') in ['回踩黄线B']]
# 单针下20
needle_candidates = [r for r in results if '单针下20' in r.get('verdict','')]

msg4 = f"## 4. 标准战法中线推荐 — 回踩黄线短黄 ({len(mid_b1)}只)\n\n"
msg4 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg4 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in mid_b1[:10]:
    t = r['tactics']
    jx = r.get('jrx', {})
    msg4 += f"| 🔶 | {r['code']} | {r['name']} | 中线 B1(回踩黄线) | {r['close']:.2f} | {t.get('stop_primary',0):.2f} | {t.get('tone','?')} | 标准战法 | {jx.get('base_momentum',0):.0f}+{jx.get('x_momentum',0):.0f} | {r.get('tactics_score',0)} |\n"

# 按信号等级排序: 双确认 > 白金针 > 黄金针 > 原版
needle_level_order = {"dual": 0, "platinum": 1, "golden": 2, "base": 3}
needle_candidates.sort(key=lambda r: needle_level_order.get(r.get('needle',{}).get('signal_level','base'), 4))

msg4 += f"\n## 5. 单针下20战法推荐 ({len(needle_candidates)}只)\n\n"
if needle_candidates:
    level_labels = {"dual": "🔴双确认", "platinum": "⚪白金针", "golden": "🟡黄金针", "base": "原版"}
    msg4 += "| 优先级 | 代码 | 名称 | 信号等级 | 现价 | 白线/红线 | V型 | BBI | 动能 | 评分 |\n"
    msg4 += "|--------|------|------|---------|------|-----------|-----|-----|------|------|\n"
    for r in needle_candidates[:10]:
        n = r.get('needle', {})
        jx = r.get('jrx', {})
        level = n.get('signal_level', 'base')
        level_label = level_labels.get(level, level)
        v_label = {"multi_v": "多V", "double_v": "双V", "deep_v": "深V"}.get(n.get('v_quality', ''), n.get('v_quality', '-'))
        bbi_status = "↑" if n.get('bbi_up') else ("↓⚠️" if n.get('bbi_declining') else "→")
        msg4 += f"| {'⭐' if level=='dual' else '🔶'} | {r['code']} | {r['name']} | {level_label} | {r['close']:.2f} | {n.get('white_line',0):.0f}/{n.get('red_line',0):.0f} | {v_label} | {bbi_status} | {jx.get('base_momentum',0):.0f}+{jx.get('x_momentum',0):.0f} | {r.get('needle_score',0)} |\n"
else:
    msg4 += "> 今日无符合条件的单针下20信号。\n"

with open('D:/Trading Workflow/happyclaw/happyclaw-b67af782f44e3c117ae0f3a6dbf541abe0b3253f/data/groups/main/msg4_mid_needle.md', 'w', encoding='utf-8') as f:
    f.write(msg4)
print(f"Section 4-5: mid={len(mid_b1)} needle={len(needle_candidates)}")

# === Section 5: 死叉 + 精选 ===
dead_list = [r for r in results if '死叉' in r.get('verdict','')]
# 精选 Top 10 from B1
top10 = b1_candidates[:10]

msg5 = f"## 7. 死叉警告 ({len(dead_list)}只)\n\n"
msg5 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg5 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in dead_list:
    t = r['tactics']
    jx = r.get('jrx', {})
    msg5 += f"| ❌ | {r['code']} | {r['name']} | 死叉 — 禁止 | {r['close']:.2f} | — | {t.get('tone','?')}/清仓 | 标准战法 | {jx.get('base_momentum',0):.0f}+{jx.get('x_momentum',0):.0f} | -100 |\n"

msg5 += f"\n## 8. 精选推荐 — Top 10 ({len(top10)}只候选池中精选)\n\n"
msg5 += "| 优先级 | 代码 | 名称 | 信号 | 现价 | 止损 | 理由 | 来源 | 动能 | 评分 |\n"
msg5 += "|--------|------|------|------|------|------|------|------|------|------|\n"
for r in top10:
    t = r['tactics']
    jx = r.get('jrx', {})
    msg5 += f"| ⭐ | {r['code']} | {r['name']} | B1 | {r['close']:.2f} | {t.get('stop_primary',0):.2f} | {t.get('tone','?')}{'/黄砖' if t.get('brick')=='黄' else ''} | B1 | {jx.get('base_momentum',0):.0f}+{jx.get('x_momentum',0):.0f} | {r.get('tactics_score',0)} |\n"

with open('D:/Trading Workflow/happyclaw/happyclaw-b67af782f44e3c117ae0f3a6dbf541abe0b3253f/data/groups/main/msg5_dead_pick.md', 'w', encoding='utf-8') as f:
    f.write(msg5)
print(f"Section 7-8: dead={len(dead_list)} top10={len(top10)}")

print(f"\nAll sections generated.")
print(f"B1 total: {len(b1_candidates)}")
print(f"B2 candidates: {len(b2_candidates)}")
print(f"Short B1 (紫): {len(short_b1)}")
print(f"Dead cross: {len(dead_list)}")
