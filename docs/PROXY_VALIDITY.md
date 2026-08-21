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
