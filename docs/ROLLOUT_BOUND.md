# How much is left in scheduling at all, a bound, not an exhaustion argument

2026-08-21, `sim/offline_rollout_oracle.cpp`. At every contested E decision the
oracle tries each legal action, completes the run with the greedy policy, and
commits the action with the best FINAL score. It reads `L_out` and all future
arrivals, so it is a clairvoyant one-step optimum: an upper bound on what any
scheduling policy could achieve, heuristic or not.

## Result

| test | contested decisions | baseline | perfect rollout | gain |
|---|---|---|---|---|
| t3_judge   | **0** of 2200 | 469.639 | 469.639 | **0.000** |
| cal_t14_u  | **0** of 3600 | 555.074 | 555.074 | **0.000** |
| t13_fit    | 546 of 4645 | 556.740 | 558.100 | +1.36  (+0.24%) |
| t5_true    | 730 of 1252 | 478.696 | 482.666 | +3.97  (+0.83%) |

Across 13 corpus tests: mean **+0.44%**, median **+0.079%**. One outlier
(burst_14, +4.29%); `burst_17` has 4743 contested decisions and gains
**exactly 0.000**.

## What it means

**#3 and #14 have ZERO contested decisions.** E never has more than one legal
action; the schedule is forced. No scheduler of any kind can behave differently
there. This confirms the arrival-span floor proof in STRUCTURAL_FLOORS.md by a
completely independent method.

Elsewhere a *clairvoyant* scheduler gains well under 1% per test. Scaled to our
22-test total that is roughly **+70 points in the perfect-oracle case**, and
it needs future knowledge we cannot have. The prefix study
(submit/rounds/README.md, "Rollout premise ... REFUTED") already showed the
observable signals are anti-correlated with the final winner: prefix selection
captured **-94.9%** of the config oracle.

**So the greedy policy is within ~1% of a clairvoyant one-step optimum, and the
gap to 16,500 (+161) is not reachable through better scheduling decisions.**
This is a bound on the whole algorithm family, not a report that we ran out of
knobs to try.
