#!/bin/bash
# Mandatory gate before any submission. A change must pass ALL of these.
# Added after v11 lost 792 points: decode-first starved prefill and collapsed
# the one high-token-rate test (#22, tp 36.7 -> 0.249). cal_t22 reproduces that
# failure to within 0.5% and is now a hard gate.
set -u
SOLVER=${1:-./build/local/solver}
fail=0

echo "== 1. official Example 1 must be byte-exact and score 500.000 =="
python3 tools/interactor.py --test data/public/example1.test --solver $SOLVER --dump-stream /tmp/_v.txt >/dev/null 2>&1
if diff -q /tmp/_v.txt data/public/example1.interactor.txt >/dev/null; then echo "   PASS"; else echo "   *** FAIL ***"; fail=1; fi

echo "== 2. #22-class regression (high token rate, deep prefill backlog) =="
s=$(python3 tools/interactor.py --test data/judgecal/cal_t22.txt --solver $SOLVER --quiet 2>&1|tail -1)
tp=$(python3 tools/interactor.py --test data/judgecal/cal_t22.txt --solver $SOLVER 2>&1|grep '^score='|sed 's/.*tp=\([0-9.]*\).*/\1/')
ok=$(python3 -c "print(1 if $tp > 5.0 else 0)")
echo "   score=$s  tp=$tp  (v7 baseline tp=8.79; ABCD disaster was tp=0.248)"
if [ "$ok" = "1" ]; then echo "   PASS"; else echo "   *** FAIL: prefill starvation ***"; fail=1; fi

echo "== 3. legality across every corpus =="
inv=0; tot=0
for f in data/stress/*.txt data/single/*.txt data/overload/*.txt data/generated/*.txt \
         data/latbound/*.txt data/cal/*.txt data/judgecal/*.txt; do
  [ -e "$f" ] || continue
  out=$(python3 tools/interactor.py --test "$f" --solver $SOLVER 2>&1|tail -1); tot=$((tot+1))
  case "$out" in INVALID*) inv=$((inv+1)); echo "   INVALID: $f";; esac
done
echo "   ran=$tot invalid=$inv"; [ "$inv" = "0" ] || fail=1

echo "== 4. judge-calibrated corpus total (v7 baseline = 18966.3) =="
sum=0; for f in data/cal/*.txt; do s=$(python3 tools/interactor.py --test $f --solver $SOLVER --quiet 2>&1|tail -1); sum=$(python3 -c "print($sum+$s)"); done
python3 -c "print(f'   total = {$sum:.1f}')"

echo; [ "$fail" = "0" ] && echo "ALL GATES PASSED" || echo "*** GATE FAILED — DO NOT SUBMIT ***"
exit $fail
