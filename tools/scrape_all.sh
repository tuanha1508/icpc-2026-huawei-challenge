#!/bin/bash
# Slowly scrape per-test judge output for every distinct-scoring submission.
# Codeforces throttles submission pages hard, so this paces at ~3.5 min each
# and retries rather than hammering. Runs for hours by design.
cd "$(dirname "$0")/.." || exit 1
python3 - <<'PY' > /tmp/scrape_queue.txt
import json
subs=json.load(open('data/allsubs/index.json'))
seen={}
for s in subs:                      # keep the FIRST submission at each score
    k=round(s['pts'],3)
    if k not in seen: seen[k]=s
for s in sorted(seen.values(), key=lambda x:-x['pts']):
    print(s['id'], f"{s['pts']:.3f}")
PY
n=0
while read id pts; do
  out="data/allsubs/${id}_${pts}.txt"
  [ -s "$out" ] && grep -q norm_tp "$out" && continue
  python3 tools/cf_fetch_tests.py "$id" --out "$out" >/dev/null 2>&1
  if grep -q norm_tp "$out" 2>/dev/null; then
    n=$((n+1)); echo "$(date +%H:%M) ok $id $pts  (total $n)"
  else
    rm -f "$out"; echo "$(date +%H:%M) throttled $id, backing off"; sleep 300
  fi
  sleep 210
done < /tmp/scrape_queue.txt
echo "SCRAPE COMPLETE"
