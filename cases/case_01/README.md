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
