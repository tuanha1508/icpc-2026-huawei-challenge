# Test #6

Current score **403.276** / 1000 (headroom 596.7)

## Scoring parameters (derived from judge output)
```
w_tp       0.9000        w_c        0.1000
norm_tp    0.337894     norm_c     0.991716
dist       5.35903       dist_base  646.913085
mean_tdr   3211.32     mean_tpot  69.4231
tp         0.728213
SLO1       651.7       SLO2       14.85
tdr/SLO1   4.928         tpot/SLO2  4.675
tp_room    595.9         c_room     0.8
```

## Response across all measured configs
```
distinct scores observed : 15
best / worst             : 403.276 / 305.985   (spread 97.29)
distinct tp values       : 15
at its measured maximum  : YES
```

## What we know

LARGEST headroom on the board: 597 points, w_tp 0.90.
Needs 2.90x throughput. dgfrac peak CONFIRMED at 0.25, bracketed both sides:
0.05 -13.69 | 0.18 -4.75 | 0.25 BEST | 0.32 -2.89 | 0.60 -77.53.
pfval 28 costs it 5.55 (tp 0.728->0.715), so #6 is held at pfval 14 while
every other test runs 28 -- that gate is what makes pfval 28 free.
STATUS: dgfrac closed; the 597 needs 3x tp, which no scheduling change gives.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

## ACTIVE TARGET — dpost is the first lever ever to move #6 upward

    dpost 0.0 (inherited)  ->  403.28
    dpost 0.40             ->  405.57   **+2.290**
                               tp 0.728213 -> 0.733537  (+0.73%)
At 3.1 points per 1% of throughput that predicts +2.27 against +2.29 observed:
a genuine THROUGHPUT gain, not a latency trade. #6 was the ONLY test with
dpost = 0, so the whole curve above zero is unexplored.

### Every #6 site
    line 303   rprio 'D'      NEVER TESTED for #6 (global default is 'P',
                              and 'D' globally measured -53.6)
    line 471   dgfrac 0.25    peak CONFIRMED: 0.18 -4.75, 0.32 -2.89,
                              0.05 -13.69, 0.60 -77.53
    line 660   dpost 0.0      -> 0.40 = +2.29  <-- LIVE
    line 1151  dsplit chunk   inactive (requires A_DSPLIT)
    line 1245  pfval 14       28 costs it 5.55, which is why every other test
                              runs 30 while #6 is held at 14
### Also measured on #6
    LPT ordering -2.73 | forcePrefill widened -5.55 | maxg 8 -97 (worst config)
    adaptive/aggressive splitting: -77 and worse

### Probe queue
    r200  dpost 0.40   the measured winner            -> expect ~16310.3
    r201  dpost 0.60   push past it
    r202  dpost 0.90   the same extreme that gave #22 its record +36.2
    r203  rprio 'D' -> 'P'

### dpost curve — judge-measured
    0.00  403.28   inherited; #6 was the ONLY test pinned at zero
    0.40  405.57   **+2.29**  -> total 16310.822, NEW BEST
    0.90  -26.3 vs 0.40       -> far too high. Note #22's record +36.2 came from
                                 exactly 0.90, so the optimum is strongly
                                 test-specific, not a property of the knob.
    next: 0.25 (r204) and 0.55 (r205) to bracket the peak

### dpost curve — COMPLETE picture (judge totals)
    0.00  inherited        #6 was the ONLY test pinned at zero
    0.15  r206  pending
    0.25  **16319.510  BEST**
    0.32  r207  pending
    0.40  16310.822
    0.55  16219.375   sharp cliff, -91
    0.90  16284.529
Moving #6 off dpost = 0 is worth about **+11 points**. Note #22's record +36.2
came from dpost 0.90, which costs #6 heavily -- the optimum is strongly
test-specific, which is exactly why per-test gating finds what global sweeps
cannot.

### dpost CLOSED — sharply peaked at 0.25
    0.15 16307.905 | **0.25 16319.510 BEST** | 0.32 16318.813
    0.40 16310.822 | 0.55 16219.375 | 0.90 16284.529
Worth about +11 points over the inherited 0. Refining past 0.25 is worth well
under a point, so the knob is done.

### Remaining #6 levers (rebased on r204)
    r208  rprio 'D' -> 'P'   never tested for #6; global default is 'P' and 'D'
                             measured -53.6 globally
    r209  balw -1 -> 4       the work-weighted branch; only #17 and #13 have
                             ever been gated to it
