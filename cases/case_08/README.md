# Test #8

Current score **812.230** / 1000 (headroom 187.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.2500        w_c        0.7500
norm_tp    0.700503     norm_c     0.849472
dist       1.63846       dist_base  10.884766
mean_tdr   1086.89     mean_tpot  143.942
tp         0.012364
SLO1       422.9       SLO2       98.07
tdr/SLO1   2.570         tpot/SLO2  1.468
tp_room    74.9         c_room     112.9
```

## Response across all measured configs
```
distinct scores observed : 6
best / worst             : 812.230 / 729.931   (spread 82.30)
distinct tp values       : 6
at its measured maximum  : YES
```

## What we know

THE legacyQuarter test (w 0.25, dist_base 10.8848). 113 points, 112.9 of it
latency, dist 92% TDR-driven.
UNIQUE: #8 is the ONLY test with dgfrac = 0 -- immediateDecodeWaves is set by
legacyQuarter, so its decode groups fire immediately and NEVER accumulate.
That regime has never been varied. r183/r184 probe dgfrac 0.10 / 0.24.
Also: marginal ON measured -- the legacyQuarter bundle disables it.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
