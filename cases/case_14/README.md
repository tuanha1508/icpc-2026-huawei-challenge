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
