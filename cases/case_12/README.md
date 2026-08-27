# Test #12

Current score **804.991** / 1000 (headroom 195.0)

## Scoring parameters (derived from judge output)
```
w_tp       0.9900        w_c        0.0100
norm_tp    0.809331     norm_c     0.375308
dist       2.80505       dist_base  4.490301
mean_tdr   1.2531e+06     mean_tpot  380.234
tp         2.4e-05
SLO1       423580       SLO2       129.55
tdr/SLO1   2.958         tpot/SLO2  2.935
tp_room    188.8         c_room     6.2
```

## Response across all measured configs
```
distinct scores observed : 17
best / worst             : 805.532 / 85.605   (spread 719.93)
distinct tp values       : 3
at its measured maximum  : no
```

## What we know

w_tp 0.99, essentially pure throughput. 189 points, and the BEST throughput
leverage on the board at 14.8 points per 1% tp (needs only +12.8%).
ENGINE-BOUND, established by elimination on the judge:
  decode-group cap removed -> exact no-op (groups never even reach 8)
  prefill-queue SJF        -> exact no-op (remote queues are empty)
  admission cap            -> -719 (collapses to ~85; flooding is REQUIRED)
  prefillBoost 2 and 40    -> exact no-op both ways
  eprio ABCD / order K / radapt off -> all flat or negative
ONLY dgfrac pays: 0.32 +0.24, then 0.60 +0.541 (peak), 0.90 -2.17.
STATUS: 8 of 9 mechanisms dead; dgfrac at its peak.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
