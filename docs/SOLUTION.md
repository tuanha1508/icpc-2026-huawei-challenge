# Solution v2, reactive batching scheduler, weight-aware

**Submit `src/main.cpp`** as a single file, language **GNU G++23 14.2 (64 bit)**.
Frozen snapshot: `artifacts/submissions/20260814T154312Z-batching-v2-weightaware`
(source SHA-256 `da1dfe4dea0029b90665cf21502dbfb82019ecf37e55472a2f497a40a6279e45`).

## v1 judge result and what it changed

v1 scored **11772.334** across the 22 preliminary tests (rank ~622; leader
16164.872). **All 22 tests returned OK**, no protocol violation, no TLE, worst
case 2156 ms against a 15 s limit, so the contract work held up on the real
judge. Recovering `w_tp` from each test's reported `norm_tp`/`norm_c` and points
(`score = w_tp*norm_tp + w_c*norm_c`) localised the loss:

```
total recoverable via throughput = 7063
total recoverable via waiting    = 3164
```

That exposed a **design bug**: v1 engaged the concurrency cap whenever
`w_c > 0`. Throttling concurrency buys TPOT and sells throughput, so on tests
like #12 (`w_tp = 0.99`), #16 (`0.98`), #6 (`0.90`) and #5 (`0.80`) it was
trading 0.99-weighted throughput for 0.01-weighted waiting. Those tests carried
a combined 5222 points of loss.

**v2 fixes:**

- The cap is seeded **only when `w_c >= w_tp`**. Ties keep it: at `w_tp = w_c`
  the judge tests sat at `norm_c = 1.0` with `norm_tp ≈ 0` (#2, #11), so
  dropping it there risks 500 to win ~2.
- The controller now steers on **both excesses** (`ex_tdr` vs `ex_tpot`) rather
  than TPOT alone, descending `dist = sqrt(ex_tdr² + ex_tpot²)` directly. When
  TPOT dominates but throughput outweighs waiting, it *grows* N instead.
- `DGFRAC` holds `D PRE` until a quarter of the decode pool is ready (tp +0.3%,
  tdr −4.1%), `BALW` balances remotes by queued work rather than request count
  (tp +0.65%), and `PFAIR` bounds prefill starvation behind decode.

Two hypotheses were tested and **rejected** by measurement, so v2 does not do
them: decode-first `E` priority under overload (made TDR 2.3× worse) and prefill
fairness tuning (never triggers locally). The prefill-first order `CDAB` is best
in both normal and overloaded regimes.

## What it does

A purely reactive scheduler: read a frame, update state, assign every free
resource, flush. It never predicts event times, the interactor announces every
completion, so no arithmetic on future times is needed for correctness.

**Local computer `E`**, one task per frame, priority `P POST → P PRE → D POST →
D PRE`:

- `D PRE` and `D POST` always take **every** currently-eligible request in one
  group. A group spanning `r` remotes queues exactly the same `r` uplink
  transfers as `r` separate groups would, but pays `S + dpre(m)` once instead of
  `r` times, strictly better on `E`, neutral on the link.

**Each free remote `Ck`**: `D PROC` with all its ready members, else the next
prefill piece.

**Remote assignment** is permanent (fixed at `P PRE`), so requests are pinned to
the remote with the least *estimated queued work* (pending `prefill_proc` ms plus
active decode requests), not the least request count.

**Prefill chunking is off** (one full `[0, num_layers)` piece), see the measured
reason below.

### Adaptive concurrency control

Little's law ties the two scored goals together: with `N` requests decoding and a
system rate of `X` tokens/ms, each request sees a gap of about `N/X`, so meeting
the TPOT target caps concurrency at `N ≤ SLO2 · X`. The solver seeds `N` from a
cost-model estimate of `X` (the min of the `E`, remote-pool, and link bounds),
then **steers it on the two measured excesses**, moving `N` in whichever
direction reduces `dist = sqrt(ex_tdr² + ex_tpot²)`. The cap is only seeded when
`w_c >= w_tp`; otherwise throughput is worth more than the TPOT it would buy, and
`N` is left uncapped.

The static estimate alone is not enough: on link-bound tests a single prefill
transfer carries `L_in` tokens (up to 4096×) and sits in the FIFO ahead of decode
transfers, blowing the TPOT budget on its own. The feedback loop catches that;
a static formula does not.

## Verification

| Check | Result |
|---|---|
| Official Example 1 | reproduces the published transcript **byte-for-byte**, scores exactly **500.000** |
| Protocol legality | **0 violations in 97 runs** (21-test corpus + 75-test stress/overload + Example 1) |
| Degenerate corners | `K=1`, `num_layers=1`, `R=1..4` all clean |
| Speed | **0.80 s** for a 34 MB / ~670k-frame stream (limit 15 s; judge's worst v1 test was 2156 ms) |
| Memory | **2.20 MB** peak RSS (limit 256 MB) |
| Builds | clean under `-std=c++20` and `-std=c++23`, `-Wall -Wextra` |

`tools/interactor.py` is a full offline replica of the interactor and doubles as a
strict validator, it enforces every rule in `docs/statement/CONTRACT.md` and
raises on the first violation, so local runs fail loudly rather than silently
scoring 0 on the judge.

## Measured results (local corpus, mean of 18 tests)

```
maximal batching, static N cap      563.63
+ adaptive N controller             604.75
+ weight-aware gradient (v2)        620.68   [21 tests, incl. new overload profile]
```

The local mean barely moves because the corpus happens to contain few tests with
both a high `w_tp` and an active cap, which is exactly the case the judge is
full of. The v2 change is justified by the judge's own per-test weights, not by
the local mean.

Several near-zero tests were **proven optimal** with `tools/bounds.py`, which
computes resource-utilization lower bounds on makespan:

| Test | Score | Why |
|---|---|---|
| `spread_3` | 0.00 | tp ceiling **= tp_base**; comp_tp ceiling 0.000, `w_tp=1` → 0 is the max |
| `large_3` | 0.02 | at **100.0%** of the tp ceiling; comp_tp ceiling 0.000 |
| `decode_3` | 49.46 | at **98.2%** of the tp ceiling (max ≈ 51), makespan bound by arrival span |
| `large_1` | 750.00 | was 0; the controller found `N=1`, hitting `tpot = 89.623` = the exact computed floor |

## Two findings worth keeping

**Maximal batching is correct even when the remotes are the bottleneck.** Capping
the decode group to stagger waves *hurt* (`burst_1`: 289 → 212 as the cap went
64 → 4). `decode_proc` is sublinear in group size and `S` is charged per task, so
splitting a wave adds S-charges to the very resource that binds.

**Prefill chunking is a trap by default.** Each extra piece pays another `S`, and
that `S` lands directly on TDR while the only benefit is unblocking decode on the
remote. Adaptive chunking gained ~1 point of corpus mean, cost `burst_1` ~70
points, and **scored 0 on official Example 1**, one extra `S` pushed TDR from
30.0 to 31.0, missing `SLO1 = 30` exactly, and with `dist_base = 0` the waiting
component is all-or-nothing, so 1 ms cost the whole 500. The code path is kept
behind `A_PIECES` for prefill-bound tests where TDR has slack.

## Reproducing

```sh
c++ -std=c++23 -O2 -o build/local/solver src/main.cpp

# official Example 1: must print 500.000 and diff clean
python3 tools/interactor.py --test data/public/example1.test \
    --solver ./build/local/solver --dump-stream /tmp/ex1.txt
diff /tmp/ex1.txt data/public/example1.interactor.txt

python3 tools/gen_test.py --profile burst --seed 1 --out /tmp/t.txt
python3 tools/interactor.py --test /tmp/t.txt --solver ./build/local/solver
python3 tools/bounds.py /tmp/t.txt --achieved <tp>
python3 tools/sweep_policy.py --tests data/sweep --solver ./build/local/solver
```

Policy knobs are read from the environment (`A_EPRIO`, `A_NFACTOR`, `A_PIECES`,
`A_MAXG`, `A_CHUNK`, `A_RPRIO`, `A_DGFRAC`, `A_BALW`, `A_PFAIR`, `A_DEBUG`)
purely so they can be swept locally. `tools/eval_physical.py` ranks variants on
tp/tdr, which are calibration-independent, unlike local scores.
They are unset on the judge, so the compiled-in defaults are what gets submitted.

## Caveat on the local corpus

`tools/gen_test.py` invents its own scoring calibration. It follows the
statement's definition for `tp_base`/`dist_base` (a one-request-at-a-time
reference, confirmed exact against Example 1), but `SLO1`/`SLO2`/`tp_UB` are
guesses. Local means are therefore useful for **ranking policies against each
other**, not for predicting the real score. Policy choices here were kept
regime-adaptive rather than tuned to constants for that reason, and the finals
use a separate frozen test set regardless.

## Next levers, in expected-value order

1. **Judge-guided**: after the next submission, re-run the per-test `w_tp`
   recovery in the analysis above. It converts raw feedback into a ranked list of
   where points actually are, and it is what found the v1 cap bug.
2. Regime detection on the clamps: if projected `tp ≥ tp_UB` or `≤ tp_base`, the
   throughput component is pinned and all effort should go to TDR/TPOT.
3. Feed the measured `dist` back into the `E` priority order, not just `N`.
4. Re-examine chunking on tests where TDR has slack and remotes block decode.
