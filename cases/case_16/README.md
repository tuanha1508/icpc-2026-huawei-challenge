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
