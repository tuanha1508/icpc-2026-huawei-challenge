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
