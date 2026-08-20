# Test #18

Current score **916.179** / 1000 (headroom 83.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.5800        w_c        0.4200
norm_tp    0.991894     norm_c     0.811621
dist       139.587       dist_base  740.988751
mean_tdr   1.77136e+07     mean_tpot  0
tp         9e-06
tp_room    4.7         c_room     79.1
```

## Response across all measured configs
```
distinct scores observed : 11
best / worst             : 916.179 / 653.900   (spread 262.28)
distinct tp values       : 1   <-- tp NEVER changes: makespan is workload-fixed
at its measured maximum  : YES
```

## What we know

84 points. Carries dgfrac 0.32 and a ruse-3 gate (+0.01) -- ruse 3 is worth
-1081 globally yet wins on this one test.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
