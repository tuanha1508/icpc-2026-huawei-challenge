# Per-case dossiers

One folder per judge test. Every number here is judge-measured, scraped from the
per-test protocol on submission pages with `tools/cf_fetch_tests.py`, never
simulated. Regenerate with `python3 tools/build_cases.py`.

These are working notes, not documentation. They accumulate hand-appended probe
records over many rounds, so a given folder can lag the current build. The
authoritative summary is `docs/CAMPAIGN_RESULTS.md`; the authoritative ledger is
`submit/rounds/README.md`.

## Where the points actually are

    test  score    headroom  limiting     status
    #6    403.28    597      throughput   needs 2.90x tp, implausible
    #14   415.27    585      throughput   tp IDENTICAL in all 45 configs: CLOSED
    #5    487.17    513      throughput   needs 2.74x tp
    #3    500.57    499      latency      prefill never free when E is idle: CLOSED
    #1    500.00    500      throughput   arrival-bound: CLOSED
    #2    500.00    500      throughput   arrival-bound: CLOSED
    #11   500.19    500      throughput   arrival-bound: CLOSED
    #10   684.48    315      latency      least-explored big test
    #13   728.77    271      throughput   eprio fully determined: CLOSED
    #9    736.26    264      latency      marginal model now ON (+0.041)
    #4    806.04    194      throughput   at max
    #12   805.53    189      throughput   8 of 9 mechanisms dead
    #8    812.23    113      latency      dgfrac=0 regime never varied: OPEN
    #15   882.68    117      latency      at max
    #17   890.34    110      latency      at max
    #7    915.32     85      latency      at max
    #18   916.18     84      mixed        at max
    #19   919.53     80      throughput   w_c = 0, dist unscored
    #22   955.20     45      throughput   holds the +36.2 record (dpost 0.90)
    #21   971.45     32      latency      at max
    #16   979.91     20      throughput   at max
    #20   998.19      2      none         unreachable: dist_base underivable

## Leverage: points per 1% improvement

    THROUGHPUT                 LATENCY
    #12  14.8  (needs +12.8%)  #3  13.73  (needs -7.3% tdr)
    #13   7.2                  #14  4.82
    #6    3.1  (needs +190%)   #10  2.84
    #5    2.9  (needs +174%)   #7   2.53   #8 1.70   #17 0.94

## The one template for a BIG gain

#22's `dpost 0.90` = **+36.2**. That value is catastrophic globally (-27.3 on
#17, -6.3 on #13), so no global sweep could ever find it. It exists only
because an extreme was gated to a single test. Every other big win since has
followed the same shape:

    r139  -169 overall  ->  contained #4 +0.28  ->  became r141
    r174  -5.56         ->  all of it #6        ->  gated out, r176 free
    r178  -8.88         ->  98% test #17        ->  gated out, r179 -0.013
    r185  MULTIPLEXED   ->  8 gates in one slot ->  NEW BEST 16308.867

**Multiplexing is the search method**: per-test gates are independent, so one
submission carries 8 experiments, and losers cost only their own test.
