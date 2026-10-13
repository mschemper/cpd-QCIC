"""Method audit of site/data.json: match rate, pay sanity, flag volume, location, badges. Read-only."""
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / (sys.argv[1] if len(sys.argv) > 1 else "site/data.json")).read_text())
O, M = d["officers"], d["metrics"]
sw = [o for o in O if o["sworn"]]
matched = [o for o in sw if o["cpdp"]]
print(f"members {len(O)}  sworn {len(sw)}  matched {len(matched)} ({100*len(matched)/len(sw):.1f}%)")
print("unmatched sworn by title:", Counter(o["title"] for o in sw if not o["cpdp"]).most_common(6))
print("titles not classed sworn (top):", Counter(o["title"] for o in O if not o["sworn"]).most_common(8))

print("\n-- pay")
c = d["meta"]["counts"]
print(f"total ${c['pay_total']:,.0f}  ot ${c['ot_total']:,.0f} ({100*c['ot_total']/c['pay_total']:.1f}%)")
print("negative totals:", sum(o["total"] < 0 for o in O))
for k in ("total", "ot"):
    print(f"top 10 {k}:")
    for o in sorted(O, key=lambda o: -o[k])[:10]:
        print(f"   {o[k]:>11,.0f}  base {o['base']:>9,.0f}  ot {o['ot']:>9,.0f}  {o['title'][:34]:34} {o['name']}")

print("\n-- flags (stat by metric / fixed by key)")
n = len(O)
for i, m in enumerate(M):
    k = sum(m in o["fs"] for o in O)
    print(f"   stat {m:5} {k:5} ({100*k/n:.1f}%)")
for k, v in Counter(f for o in O for f in o["ff"]).most_common():
    print(f"   fixed {k:5} {v:5} ({100*v/n:.1f}%)")
print("any flag:", sum(bool(o["fs"] or o["ff"]) for o in O))
mad0 = [(g, m) for g, p in d["peers"].items() for i, m in enumerate(M) if p["median"][i] == p["p90"][i]]
print("peer groups with median == p90 (degenerate spread):", len(mad0), mad0[:6])

print("\n-- location")
print(f"matched with district: {sum(1 for o in matched if o['dist'])} / {len(matched)}")
print("non-district units (top):", Counter(o["unit_desc"] for o in matched if not o["dist"]).most_common(10))

print("\n-- badges")
b = [o["badge"] for o in O if o["badge"]]
dup = [k for k, v in Counter(b).items() if v > 1]
print(f"with badge {len(b)}  duplicates {len(dup)} {dup[:10]}")

print("\n-- 20 random matches (payroll name | title | badge | unit)")
random.seed(1)
for o in random.sample(matched, 20):
    print(f"   {o['name'][:28]:28} {o['title'][:28]:28} {o['badge'] or '-':>6} {o['unit_desc'] or '-'}  cpdp {o['cpdp']}")
