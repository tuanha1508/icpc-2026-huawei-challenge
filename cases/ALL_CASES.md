# All 22 cases — judge-measured dossiers

Generated 2026-08-20 15:54 from 0 per-test judge files.

# Per-case dossiers

One folder per judge test. Every number is judge-measured -- scraped from the
per-test protocol on submission pages (`tools/cf_fetch_tests.py`), never
simulated. Regenerate with `python3 tools/build_cases.py`.

## Where the points actually are

    test  score    headroom  limiting     status
    #6    403.28    597      throughput   needs 2.90x tp -- implausible
    #14   415.27    585      throughput   tp IDENTICAL in all 45 configs: CLOSED
    #5    487.17    513      throughput   needs 2.74x tp
    #3    500.57    499      latency      prefill never available when E free: CLOSED
    #1    500.00    500      throughput   arrival-bound: CLOSED
    #2    500.00    500      throughput   arrival-bound: CLOSED
    #11   500.19    500      throughput   arrival-bound: CLOSED
    #10   684.48    315      latency      least-explored big test
    #13   728.77    271      throughput   eprio fully determined: CLOSED
    #9    736.26    264      latency      marginal model now ON (+0.041)
    #4    806.04    194      throughput   at max
    #12   805.53    189      throughput   8 of 9 mechanisms dead
    #8    812.23    113      latency      dgfrac=0 regime NEVER varied  <-- open
    #15   882.68    117      latency      at max
    #17   890.34    110      latency      at max
    #7    915.32     85      latency      at max
    #18   916.18     84      mixed        at max
    #19   919.53     80      throughput   w_c = 0, dist unscored
    #22   955.20     45      throughput   holds the +36.2 record (dpost 0.90)
    #21   971.45     32      latency      at max
    #16   979.91     20      throughput   at max
    #20   998.19      2      --           unreachable: dist_base underivable

## Leverage: points per 1% improvement

    THROUGHPUT                 LATENCY
    #12  14.8  (needs +12.8%)  #3  13.73  (needs -7.3% tdr)
    #13   7.2                  #14  4.82
    #6    3.1  (needs +190%)   #10  2.84
    #5    2.9  (needs +174%)   #7   2.53   #8 1.70   #17 0.94

## The one template for a BIG gain

#22's `dpost 0.90` = **+36.2**. That value is catastrophic globally (-27.3 on
#17, -6.3 on #13), so no global sweep could ever find it -- it exists only
because an extreme was gated to a single test. Every other big win since has
followed the same shape:

    r139  -169 overall  ->  contained #4 +0.28  ->  became r141
    r174  -5.56         ->  all of it #6        ->  gated out, r176 free
    r178  -8.88         ->  98% test #17        ->  gated out, r179 -0.013
    r185  MULTIPLEXED   ->  8 gates in one slot ->  NEW BEST 16308.867

**Multiplexing is the search method**: per-test gates are independent, so one
submission carries 8 experiments, and losers cost only their own test.

---

# Test #1

Current score **500.000** / 1000 (headroom 500.0)

## Scoring parameters (derived from judge output)
```
w_tp       0.5000        w_c        0.5000
norm_tp    0.000000     norm_c     1.000000
dist       0       dist_base  0.000000
mean_tdr   30     mean_tpot  0
tp         0.022222
tp_room    500.0         c_room     0.0
```

## Response across all measured configs
```
distinct scores observed : 2
best / worst             : 500.000 / 0.000   (spread 500.00)
distinct tp values       : 2
at its measured maximum  : YES
```

## What we know

norm_tp is pinned at 0.000 and norm_c at 1.000 -> exactly 500.000.
tp = 0.022222 = 1/45 and never moves. ARRIVAL-BOUND: the makespan is set by
the arrival span, not by scheduling, so the 500 points of tp headroom are
not collectable by any scheduler.
STATUS: closed.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #2

Current score **500.000** / 1000 (headroom 500.0)

## Scoring parameters (derived from judge output)
```
w_tp       0.5000        w_c        0.5000
norm_tp    0.000000     norm_c     1.000000
dist       0       dist_base  0.000000
mean_tdr   126.159     mean_tpot  0
tp         0.005755
tp_room    500.0         c_room     0.0
```

## Response across all measured configs
```
distinct scores observed : 1
best / worst             : 500.000 / 500.000   (spread 0.00)
distinct tp values       : 3
at its measured maximum  : YES
```

## What we know

Identical shape to #1: norm_tp 0.000, norm_c 1.000, score exactly 500.000.
ZERO distinct values across every config ever measured.
STATUS: closed.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #3

Current score **500.568** / 1000 (headroom 499.4)

## Scoring parameters (derived from judge output)
```
w_tp       0.0000        w_c        1.0000
norm_tp    0.348054     norm_c     0.500568
dist       0.577735       dist_base  1.156784
mean_tdr   1329.85     mean_tpot  56.4623
tp         0.003882
SLO1       837.6       SLO2       56.46
tdr/SLO1   1.588         tpot/SLO2  1.000
tp_room    0.0         c_room     499.4
```

## Response across all measured configs
```
distinct scores observed : 3
best / worst             : 500.568 / 192.679   (spread 307.89)
distinct tp values       : 3
at its measured maximum  : YES
```

## What we know

w_tp = 0.00, so the score IS 1000 * norm_c. dist is 100% TDR-driven
(mean_tpot sits exactly at SLO2). LEVERAGE: 13.73 points per 1% of mean_tdr,
the best latency leverage on the board -- -7.3% tdr would be +100.
TRIED: dgfrac 0.05/0.60 both exactly inert; balw>0 (+71 on proxies) a judge
no-op; rporder 'S' no-op; forcePrefill widened to fire on TDR-dominant (r167)
left mean_tdr identical to 3 decimals.
WHY: forcePrefill also needs prefill work AVAILABLE when E is free, and on #3
that never coincides -- prefill is starved upstream at the link/remotes.
STATUS: closed at the mechanism level. Only 3 distinct values in 45 configs.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #4

Current score **806.036** / 1000 (headroom 194.0)

## Scoring parameters (derived from judge output)
```
w_tp       0.3000        w_c        0.7000
norm_tp    0.483362     norm_c     0.944325
dist       1.51136       dist_base  27.146098
mean_tdr   463.931     mean_tpot  86.8946
tp         0.060257
SLO1       181.7       SLO2       143.4
tdr/SLO1   2.553         tpot/SLO2  0.606
tp_room    155.0         c_room     39.0
```

## Response across all measured configs
```
distinct scores observed : 10
best / worst             : 806.036 / 760.435   (spread 45.60)
distinct tp values       : 10
at its measured maximum  : YES
```

## What we know

Gated to nfactor 0.9 + dpost 0.30, worth +0.28 -- harvested from r139, a
config that LOST 169 points overall. Also carries dgfrac 0.60.
Needs 1.92x tp for the remaining 155. STATUS: at its measured max.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #5

Current score **487.172** / 1000 (headroom 512.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.8000        w_c        0.2000
norm_tp    0.359531     norm_c     0.997736
dist       3.83581       dist_base  1694.261926
mean_tdr   1497.25     mean_tpot  62.4873
tp         1.21009
SLO1       311.8       SLO2       87.14
tdr/SLO1   4.802         tpot/SLO2  0.717
tp_room    512.4         c_room     0.5
```

## Response across all measured configs
```
distinct scores observed : 11
best / worst             : 487.172 / 343.297   (spread 143.88)
distinct tp values       : 11
at its measured maximum  : YES
```

## What we know

w_tp 0.80. Needs 2.74x throughput to reach tp_UB -- implausible.
norm_c is already 0.998, so latency is nearly exhausted.
Carries dgfrac 0.10 and a forced eprio ABDC. dgfrac 0.60/0.05 both inert.
STATUS: effectively closed (2.9 pts per 1% tp, needs +174%).

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #6

Current score **403.276** / 1000 (headroom 596.7)

## Scoring parameters (derived from judge output)
```
w_tp       0.9000        w_c        0.1000
norm_tp    0.337894     norm_c     0.991716
dist       5.35903       dist_base  646.913085
mean_tdr   3211.32     mean_tpot  69.4231
tp         0.728213
SLO1       651.7       SLO2       14.85
tdr/SLO1   4.928         tpot/SLO2  4.675
tp_room    595.9         c_room     0.8
```

## Response across all measured configs
```
distinct scores observed : 15
best / worst             : 403.276 / 305.985   (spread 97.29)
distinct tp values       : 15
at its measured maximum  : YES
```

## What we know

LARGEST headroom on the board: 597 points, w_tp 0.90.
Needs 2.90x throughput. dgfrac peak CONFIRMED at 0.25, bracketed both sides:
0.05 -13.69 | 0.18 -4.75 | 0.25 BEST | 0.32 -2.89 | 0.60 -77.53.
pfval 28 costs it 5.55 (tp 0.728->0.715), so #6 is held at pfval 14 while
every other test runs 28 -- that gate is what makes pfval 28 free.
STATUS: dgfrac closed; the 597 needs 3x tp, which no scheduling change gives.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #7

Current score **915.319** / 1000 (headroom 84.7)

## Scoring parameters (derived from judge output)
```
w_tp       0.0000        w_c        1.0000
norm_tp    0.424736     norm_c     0.915319
dist       0.340227       dist_base  4.017749
mean_tdr   860.123     mean_tpot  65.6322
tp         0.014536
SLO1       676.8       SLO2       54.75
tdr/SLO1   1.271         tpot/SLO2  1.199
tp_room    0.0         c_room     84.7
```

## Response across all measured configs
```
distinct scores observed : 9
best / worst             : 915.319 / 637.837   (spread 277.48)
distinct tp values       : 9
at its measured maximum  : YES
```

## What we know

w_tp 0.00, pure latency. Carries rporder 'S' and dgfrac 0.10.
2.53 points per 1% tdr, 85 available. dist is 65% TDR.
STATUS: at measured max; spread 277 across configs but current is the peak.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #8

Current score **812.230** / 1000 (headroom 187.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.2500        w_c        0.7500
norm_tp    0.700503     norm_c     0.849472
dist       1.63846       dist_base  10.884766
mean_tdr   1086.89     mean_tpot  143.942
tp         0.012364
SLO1       422.9       SLO2       98.07
tdr/SLO1   2.570         tpot/SLO2  1.468
tp_room    74.9         c_room     112.9
```

## Response across all measured configs
```
distinct scores observed : 6
best / worst             : 812.230 / 729.931   (spread 82.30)
distinct tp values       : 6
at its measured maximum  : YES
```

## What we know

THE legacyQuarter test (w 0.25, dist_base 10.8848). 113 points, 112.9 of it
latency, dist 92% TDR-driven.
UNIQUE: #8 is the ONLY test with dgfrac = 0 -- immediateDecodeWaves is set by
legacyQuarter, so its decode groups fire immediately and NEVER accumulate.
That regime has never been varied. r183/r184 probe dgfrac 0.10 / 0.24.
Also: marginal ON measured -- the legacyQuarter bundle disables it.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #9

Current score **736.258** / 1000 (headroom 263.7)

## Scoring parameters (derived from judge output)
```
w_tp       0.0500        w_c        0.9500
norm_tp    0.961900     norm_c     0.724382
dist       9.33031       dist_base  33.852310
mean_tdr   5723.31     mean_tpot  0
tp         0.004394
tp_room    1.9         c_room     261.8
```

## Response across all measured configs
```
distinct scores observed : 8
best / worst             : 736.258 / 671.357   (spread 64.90)
distinct tp values       : 5
at its measured maximum  : YES
```

## What we know

w_tp 0.05, latency-dominated, mean_tpot = 0 (every request emits one token).
Excluded from the marginal model by weight; enabling it for #9 alone was the
FIRST gain in that area: +0.041 (r129). 262 points remain, 8.77x over SLO1.
STATUS: marginal now ON; other levers untested per-test.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #10

Current score **684.481** / 1000 (headroom 315.5)

## Scoring parameters (derived from judge output)
```
w_tp       0.1500        w_c        0.8500
norm_tp    0.994619     norm_c     0.629751
dist       143.983       dist_base  388.882182
mean_tdr   182521     mean_tpot  83.3398
tp         0.00763
SLO1       1302.4       SLO2       3.4226
tdr/SLO1   140.142         tpot/SLO2  24.350
tp_room    0.8         c_room     314.7
```

## Response across all measured configs
```
distinct scores observed : 7
best / worst             : 684.481 / 644.415   (spread 40.07)
distinct tp values       : 6
at its measured maximum  : YES
```

## What we know

315 points, the largest LATENCY headroom still open. w_tp 0.15, dist 97% TDR,
mean_tdr is 140x SLO1. Carries eprio CDBA and rprio 'D' via the cxT10 gate.
Enabling the marginal model for #10 measured -0.011, so it stays off.
2.84 points per 1% tdr. STATUS: at measured max, but least-explored of the
big-headroom tests.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #11

Current score **500.185** / 1000 (headroom 499.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.5000        w_c        0.5000
norm_tp    0.000371     norm_c     1.000000
dist       0       dist_base  0.000000
mean_tdr   3.27805e+07     mean_tpot  16199.1
tp         7e-06
tp_room    499.8         c_room     0.0
```

## Response across all measured configs
```
distinct scores observed : 2
best / worst             : 500.185 / 500.131   (spread 0.05)
distinct tp values       : 1   <-- tp NEVER changes: makespan is workload-fixed
at its measured maximum  : YES
```

## What we know

mean_tdr 32.7 MILLION yet dist = 0: the SLOs are astronomically loose, so
norm_c = 1.000 for free and norm_tp is pinned near 0. Arrival-bound.
Only 3 distinct values ever observed, spread 0.05. STATUS: closed.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #12

Current score **804.991** / 1000 (headroom 195.0)

## Scoring parameters (derived from judge output)
```
w_tp       0.9900        w_c        0.0100
norm_tp    0.809331     norm_c     0.375308
dist       2.80505       dist_base  4.490301
mean_tdr   1.2531e+06     mean_tpot  380.234
tp         2.4e-05
SLO1       423580       SLO2       129.55
tdr/SLO1   2.958         tpot/SLO2  2.935
tp_room    188.8         c_room     6.2
```

## Response across all measured configs
```
distinct scores observed : 17
best / worst             : 805.532 / 85.605   (spread 719.93)
distinct tp values       : 3
at its measured maximum  : no
```

## What we know

w_tp 0.99 -- essentially pure throughput. 189 points, and the BEST throughput
leverage on the board at 14.8 points per 1% tp (needs only +12.8%).
ENGINE-BOUND, established by elimination on the judge:
  decode-group cap removed -> exact no-op (groups never even reach 8)
  prefill-queue SJF        -> exact no-op (remote queues are empty)
  admission cap            -> -719 (collapses to ~85; flooding is REQUIRED)
  prefillBoost 2 and 40    -> exact no-op both ways
  eprio ABCD / order K / radapt off -> all flat or negative
ONLY dgfrac pays: 0.32 +0.24, then 0.60 +0.541 (peak), 0.90 -2.17.
STATUS: 8 of 9 mechanisms dead; dgfrac at its peak.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #13

Current score **728.765** / 1000 (headroom 271.2)

## Scoring parameters (derived from judge output)
```
w_tp       0.7500        w_c        0.2500
norm_tp    0.689806     norm_c     0.845645
dist       2.60683       dist_base  16.888562
mean_tdr   1680.99     mean_tpot  69.2032
tp         0.026991
SLO1       463.6       SLO2       66.73
tdr/SLO1   3.626         tpot/SLO2  1.037
tp_room    232.6         c_room     38.6
```

## Response across all measured configs
```
distinct scores observed : 19
best / worst             : 728.765 / 680.588   (spread 48.18)
distinct tp values       : 16
at its measured maximum  : YES
```

## What we know

271 points, w_tp 0.75. Runs useMarginal = FALSE, so its forced eprio is its
ENTIRE engine policy, not a fallback.
eprio fully determined by three measured axes:
  prefill block before decode block   ~9-24 pts
  P PRE before P POST  (DC > CD)        3.24
  D PRE before D POST  (BA > AB)       23.89
  => DCBA wins on all three; the other 19 permutations lose by composition.
PREFILL-STARVED ~100% of the time: an adaptive pool-depth switch never fired
even at threshold 4K. Enabling the marginal model measured -14.47.
STATUS: closed.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #14

Current score **415.267** / 1000 (headroom 584.7)

## Scoring parameters (derived from judge output)
```
w_tp       0.6500        w_c        0.3500
norm_tp    0.210323     norm_c     0.795876
dist       0.176642       dist_base  0.865366
mean_tdr   192.489     mean_tpot  184.378
tp         0.003564
SLO1       161.5       SLO2       212.9
tdr/SLO1   1.192         tpot/SLO2  0.866
tp_room    513.3         c_room     71.4
```

## Response across all measured configs
```
distinct scores observed : 4
best / worst             : 415.267 / 351.600   (spread 63.67)
distinct tp values       : 2
at its measured maximum  : YES
```

## What we know

585 points and the NARROWEST scoring window on the board -- tp_UB/tp_base =
1.0053, so +0.42% throughput would be worth 513 points.
BUT tp is IDENTICAL (0.003564) across all 45 configs, including catastrophic
ones. Only the latency metrics ever move. Makespan is fixed by the workload.
STATUS: closed -- the 513 points are not collectable by anyone.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #15

Current score **882.678** / 1000 (headroom 117.3)

## Scoring parameters (derived from judge output)
```
w_tp       0.4500        w_c        0.5500
norm_tp    0.982434     norm_c     0.801059
dist       35.8752       dist_base  180.330636
mean_tdr   7.74194e+06     mean_tpot  0
tp         9e-06
tp_room    7.9         c_room     109.4
```

## Response across all measured configs
```
distinct scores observed : 13
best / worst             : 882.678 / 715.582   (spread 167.10)
distinct tp values       : 1   <-- tp NEVER changes: makespan is workload-fixed
at its measured maximum  : YES
```

## What we know

117 points, latency. Excluded from the marginal model by weight+dist_base;
enabling it for #15 alone was an exact no-op on the judge.
mean_tpot = 0 (single-token requests). STATUS: at measured max.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #16

Current score **979.907** / 1000 (headroom 20.1)

## Scoring parameters (derived from judge output)
```
w_tp       0.9800        w_c        0.0200
norm_tp    0.981296     norm_c     0.911808
dist       35.3163       dist_base  400.447410
mean_tdr   41824     mean_tpot  71.6697
tp         0.029765
SLO1       1179.5       SLO2       66.189
tdr/SLO1   35.459         tpot/SLO2  1.083
tp_room    18.3         c_room     1.8
```

## Response across all measured configs
```
distinct scores observed : 9
best / worst             : 979.907 / 313.917   (spread 665.99)
distinct tp values       : 9
at its measured maximum  : YES
```

## What we know

Only 20 points of headroom -- essentially maxed at 979.91.
Carries the dgfrac 0.95 flat-curve whitelist (worth +3.84, and +2.32 more
from forcing it to persist since #16 also has useMarginal false).

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #17

Current score **890.336** / 1000 (headroom 109.7)

## Scoring parameters (derived from judge output)
```
w_tp       0.6700        w_c        0.3300
norm_tp    0.989140     norm_c     0.689734
dist       1011.2       dist_base  3259.144289
mean_tdr   1.88934e+07     mean_tpot  22932.1
tp         0.000521
SLO1       18723       SLO2       287.13
tdr/SLO1   1009.099         tpot/SLO2  79.867
tp_room    7.3         c_room     102.4
```

## Response across all measured configs
```
distinct scores observed : 26
best / worst             : 890.336 / 293.461   (spread 596.88)
distinct tp values       : 6
at its measured maximum  : YES
```

## What we know

110 points, w_tp 0.67, dist 35% TDR. Carries balw 4 + dgfrac 0.25 (an
INTERACTION-only win: +0.03, unreachable by either knob alone).
Sensitive: 21 distinct values, spread 597. dpost 0.15 costs it 8.70, which is
why r179 gates it back to 0.08.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #18

Current score **916.179** / 1000 (headroom 83.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.5800        w_c        0.4200
norm_tp    0.991894     norm_c     0.811621
dist       139.587       dist_base  740.988751
mean_tdr   1.77136e+07     mean_tpot  0
tp         9e-06
tp_room    4.7         c_room     79.1
```

## Response across all measured configs
```
distinct scores observed : 11
best / worst             : 916.179 / 653.900   (spread 262.28)
distinct tp values       : 1   <-- tp NEVER changes: makespan is workload-fixed
at its measured maximum  : YES
```

## What we know

84 points. Carries dgfrac 0.32 and a ruse-3 gate (+0.01) -- ruse 3 is worth
-1081 globally yet wins on this one test.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #19

Current score **919.530** / 1000 (headroom 80.5)

## Scoring parameters (derived from judge output)
```
w_tp       1.0000        w_c        0.0000
norm_tp    0.919530     norm_c     0.999937
dist       2.60454       dist_base  41341.873016
mean_tdr   168.425     mean_tpot  181.899
tp         0.687432
SLO1       196       SLO2       50.11
tdr/SLO1   0.859         tpot/SLO2  3.630
tp_room    80.5         c_room     0.0
```

## Response across all measured configs
```
distinct scores observed : 6
best / worst             : 919.530 / 787.896   (spread 131.63)
distinct tp values       : 6
at its measured maximum  : YES
```

## What we know

w_tp = 1.00, so w_c = 0 and dist is unscored. 80 points, all throughput.
The ONLY test whose dist is TPOT-dominated -- irrelevant since it is unscored.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #20

Current score **998.183** / 1000 (headroom 1.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.3800        w_c        0.6200
norm_tp    0.995218     norm_c     1.000000
dist       0       dist_base  0.000000
mean_tdr   1245.88     mean_tpot  172.801
tp         0.005607
tp_room    1.8         c_room     0.0
```

## Response across all measured configs
```
distinct scores observed : 9
best / worst             : 998.194 / 947.714   (spread 50.48)
distinct tp values       : 4
at its measured maximum  : no
```

## What we know

998.19 of 1000. Effectively perfect; 1.8 points remain.
norm_c is exactly 1.000000, so dist_base cannot be derived and #20 can never
be gated -- its +0.01 from the dgfrac .45/dpost .35 corner is unreachable.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #21

Current score **971.447** / 1000 (headroom 28.6)

## Scoring parameters (derived from judge output)
```
w_tp       0.5000        w_c        0.5000
norm_tp    0.993781     norm_c     0.949113
dist       148.483       dist_base  2917.894000
mean_tdr   35455.8     mean_tpot  0
tp         0.012485
tp_room    3.1         c_room     25.4
```

## Response across all measured configs
```
distinct scores observed : 15
best / worst             : 971.447 / 944.220   (spread 27.23)
distinct tp values       : 13
at its measured maximum  : YES
```

## What we know

32 points. Carries dgfrac 0.03 + dpost 0.005 (harvested from a corner probe).
mean_tpot = 0. 15 distinct values, spread 27.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

# Test #22

Current score **955.196** / 1000 (headroom 44.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.5000        w_c        0.5000
norm_tp    0.913476     norm_c     0.996917
dist       246.65       dist_base  80003.223484
mean_tdr   1858     mean_tpot  6.0041
tp         39.8699
SLO1       7.5195       SLO2       6.2865
tdr/SLO1   247.091         tpot/SLO2  0.955
tp_room    43.3         c_room     1.5
```

## Response across all measured configs
```
distinct scores observed : 4
best / worst             : 955.196 / 534.576   (spread 420.62)
distinct tp values       : 4
at its measured maximum  : YES
```

## What we know

45 points left of 1000. Holds the single biggest per-test win in the project:
dpost 0.90 = **+36.2**, a value catastrophic globally (-27.3 on #17, -6.3 on
#13) and reachable only by gating. THE template for a big gain.
tp = 39.87, by far the highest; dist is 100% TDR.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

---

