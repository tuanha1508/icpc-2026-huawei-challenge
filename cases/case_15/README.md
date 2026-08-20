# Test #15

Current score **882.678** / 1000 (headroom 117.3)

## Scoring parameters (derived from judge output)
```
w_tp       0.4500        w_c        0.5500
norm_tp    0.982434     norm_c     0.801059
dist       35.8752       dist_base  180.330636
mean_tdr   7.74194e+06     mean_tpot  0
tp         9e-06
tp_room    7.9         c_room     109.4
```

## Response across all measured configs
```
distinct scores observed : 13
best / worst             : 882.678 / 715.582   (spread 167.10)
distinct tp values       : 1   <-- tp NEVER changes: makespan is workload-fixed
at its measured maximum  : YES
```

## What we know

117 points, latency. Excluded from the marginal model by weight+dist_base;
enabling it for #15 alone was an exact no-op on the judge.
mean_tpot = 0 (single-token requests). STATUS: at measured max.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
