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
