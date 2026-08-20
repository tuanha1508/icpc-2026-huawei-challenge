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
