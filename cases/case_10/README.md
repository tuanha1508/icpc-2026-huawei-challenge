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
