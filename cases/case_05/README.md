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

w_tp 0.80. Needs 2.74x throughput to reach tp_UB, implausible.
norm_c is already 0.998, so latency is nearly exhausted.
Carries dgfrac 0.10 and a forced eprio ABDC. dgfrac 0.60/0.05 both inert.
STATUS: effectively closed (2.9 pts per 1% tp, needs +174%).

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
