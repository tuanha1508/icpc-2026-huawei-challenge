# Test #3

Current score **500.568** / 1000 (headroom 499.4)

## Scoring parameters (derived from judge output)
```
w_tp       0.0000        w_c        1.0000
norm_tp    0.348054     norm_c     0.500568
dist       0.577735       dist_base  1.156784
mean_tdr   1329.85     mean_tpot  56.4623
tp         0.003882
SLO1       837.6       SLO2       56.46
tdr/SLO1   1.588         tpot/SLO2  1.000
tp_room    0.0         c_room     499.4
```

## Response across all measured configs
```
distinct scores observed : 3
best / worst             : 500.568 / 192.679   (spread 307.89)
distinct tp values       : 3
at its measured maximum  : YES
```

## What we know

w_tp = 0.00, so the score IS 1000 * norm_c. dist is 100% TDR-driven
(mean_tpot sits exactly at SLO2). LEVERAGE: 13.73 points per 1% of mean_tdr,
the best latency leverage on the board -- -7.3% tdr would be +100.
TRIED: dgfrac 0.05/0.60 both exactly inert; balw>0 (+71 on proxies) a judge
no-op; rporder 'S' no-op; forcePrefill widened to fire on TDR-dominant (r167)
left mean_tdr identical to 3 decimals.
WHY: forcePrefill also needs prefill work AVAILABLE when E is free, and on #3
that never coincides -- prefill is starved upstream at the link/remotes.
STATUS: closed at the mechanism level. Only 3 distinct values in 45 configs.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.
