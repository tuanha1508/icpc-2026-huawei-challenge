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
