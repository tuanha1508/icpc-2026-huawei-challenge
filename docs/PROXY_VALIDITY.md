# Proxies reproduce STATE, not RESPONSE — validate before sweeping

A proxy that matches the judge's `tp`/`tdr`/`tpot` at the current
configuration can still get the **sign** of a knob's effect wrong, because it
was fitted to one operating point rather than reconstructed.

## Two proxies caught failing, 2026-08-21

`t5_true` matches judge #5 to 0.68% on tp, 2.1% on tdr, 1.4% on tpot:

| balw | judge #5 | t5_true |
|---|---|---|
| -1 (base) | 487.17 | 489.19 |
| 0 | **466.09  (-21.1)** | **491.26  (+2.1)** |
| 8 | 467.61  (-19.6) | 487.56  (-1.6) |

`t13_fit` matches judge #13 to 0.03% on tp -- and still inverts dgfrac:

| knob | judge #13 | t13_fit |
|---|---|---|
| dpost 0.60 | -6.12 | -12.7 (sign ok) |
| balw 0 | -3.12 | -1.17 (sign ok) |
| **dgfrac 0.32** | **-17.3** | **+1.31 (WRONG)** |
| dgfrac 0.40 | 0.00 | -1.82 (wrong) |

4 of 7 signs correct is not a laboratory.

## The one proxy class that IS trustworthy

Reconstructions whose computed structural floor equals our measured makespan
exactly (`t3_judge`, `cal_t14_u`, `t12_fit` -- see STRUCTURAL_FLOORS.md). There
the arithmetic depends only on the test parameters, not on response fidelity.

## Rule

Before drawing any conclusion from a proxy sweep, replay knob values that the
judge has already measured on that test (`data/pertest/*.txt`) and check the
signs match. If they do not, the sweep is void. No proxy currently exists that
predicts responses on any test that still has headroom (#4 #5 #6 #13 #17), so
those tests must be probed on the judge directly.

## The corpus is not a valid instrument for GLOBAL tuning either

2026-08-21. A coordinate descent over the global defaults on 80 ungated corpus
tests (the path the frozen set takes) found three improvements. All three had
already been refuted by the judge on ~20 real ungated tests:

| change | corpus | judge |
|---|---|---|
| maxg 64    | +0.104 mean | r126 = 15919.623  (-384 vs r104) |
| balw 8     | +0.175 mean | r103 = 16281.164  (-22.6) |
| marginal 0 | +0.085 mean | r250 = 16329.044  (-9.4) |

maxg is gated only on #12, balw only on #13/#17, marginal on a handful -- so
each of those builds measured the GLOBAL setting on about twenty real ungated
tests. The corpus systematically rewards settings the real tests punish.

**Rule: the only valid instrument for a global default is the judge's own
harvests.** Every global probe already measured its setting on ~20 real
ungated tests, and the oracle over all of them says the current defaults are
best. A corpus-derived global change may only be shipped when the judge shows
it is NEUTRAL on the 22 -- which is exactly the case for r264:

  - nfactor 0   judge-validated: neutral on 8 of the 9 capped tests, and the
                only breakage (#15, -167.9) is gated back
  - dgfrac 0.18 leaderboard-invisible: all 22 preliminary tests carry their own
                dgfrac gate, so no judge probe has ever measured the global
                default. Corpus-only evidence, but zero leaderboard risk.

## The corpus gradient was refuted at its most confident point

2026-08-22. The weight-dependent marginal rule (r268/r269) was the strongest
corpus signal found all session: useMarginal OFF minus ON gave a clean monotone
gradient over 60 re-weighted workloads per point, peaking at **+5.802 (29 win /
14 lose) at w_tp = 0.00**. Both builds were verified to deliver exactly that
number on the re-weighted corpus.

The judge disagreed. r268 and r269 came back BYTE-IDENTICAL at 16329.560, and
the harvest puts the whole -9.463 on two tests:

    #7   w_tp 0.00   916.410 -> 906.988   -9.422
    #9   w_tp 0.05   736.258 -> 736.217   -0.040
    #3 #20 (also w_tp 0.00) and #14 #18 #21 #22 -- unaffected

**#7 is the only real test at w_tp = 0 where the rule binds, and it lost 9.4
where the corpus predicted +5.8.** Sign inverted, at the precise point the
corpus was most confident and had the best win/lose ratio.

NOT SHIPPED. The rule could have been kept for the frozen set by gating #7 and
#9 back -- the leaderboard would have returned to 16339.023 -- but that would
apply to frozen w_tp = 0 tests a change the judge has directly shown is harmful
on the only real w_tp = 0 test that responds to it. r264 stands.

This is now the third independent refutation of the corpus (per-test knobs,
global defaults, and a weight-conditioned rule). Treat any corpus-only result
as unproven no matter how clean the gradient looks.
