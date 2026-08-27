# Test #20

Current score **998.183** / 1000 (headroom 1.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.3800        w_c        0.6200
norm_tp    0.995218     norm_c     1.000000
dist       0       dist_base  0.000000
mean_tdr   1245.88     mean_tpot  172.801
tp         0.005607
tp_room    1.8         c_room     0.0
```

## Response across all measured configs
```
distinct scores observed : 9
best / worst             : 998.194 / 947.714   (spread 50.48)
distinct tp values       : 4
at its measured maximum  : no
```

## What we know

998.19 of 1000. Effectively perfect; 1.8 points remain.
norm_c is exactly 1.000000, so dist_base cannot be derived and #20 can never
be gated, its +0.01 from the dgfrac .45/dpost .35 corner is unreachable.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
