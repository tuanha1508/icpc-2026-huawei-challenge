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

## RESPONDS TO dpost — found by the r216 ten-test multiplex
    dpost 0.15 (inherited)  915.32
    dpost 0.25              916.41   **+1.09**   -> total 16320.601, NEW BEST
    dpost 0.40              913.36   -1.96
#7 is w_tp = 0.00, i.e. pure latency, 84.7 points of headroom, dist 65% TDR.
It was the ONLY one of ten ungated tests to respond -- the other nine were
exact no-ops, so r216 was already a winners-only build.
Peak lies between 0.15 and 0.40; r218 (0.20) and r219 (0.30) close on it.
