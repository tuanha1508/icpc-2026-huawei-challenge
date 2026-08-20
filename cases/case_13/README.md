# Test #13

Current score **728.765** / 1000 (headroom 271.2)

## Scoring parameters (derived from judge output)
```
w_tp       0.7500        w_c        0.2500
norm_tp    0.689806     norm_c     0.845645
dist       2.60683       dist_base  16.888562
mean_tdr   1680.99     mean_tpot  69.2032
tp         0.026991
SLO1       463.6       SLO2       66.73
tdr/SLO1   3.626         tpot/SLO2  1.037
tp_room    232.6         c_room     38.6
```

## Response across all measured configs
```
distinct scores observed : 19
best / worst             : 728.765 / 680.588   (spread 48.18)
distinct tp values       : 16
at its measured maximum  : YES
```

## What we know

271 points, w_tp 0.75. Runs useMarginal = FALSE, so its forced eprio is its
ENTIRE engine policy, not a fallback.
eprio fully determined by three measured axes:
  prefill block before decode block   ~9-24 pts
  P PRE before P POST  (DC > CD)        3.24
  D PRE before D POST  (BA > AB)       23.89
  => DCBA wins on all three; the other 19 permutations lose by composition.
PREFILL-STARVED ~100% of the time: an adaptive pool-depth switch never fired
even at threshold 4K. Enabling the marginal model measured -14.47.
STATUS: closed.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
