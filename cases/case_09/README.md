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
