# Optimization research — 2026-08-15

This note translates public scheduling research into changes that fit the exact
contest model. It deliberately avoids competitor solutions and test-ID-specific
rules. The current `src/main.cpp` was not modified because another agent is
actively building v8.

## Executive conclusion

The current scheduler already has the right throughput foundation:

- iteration-level decode batching;
- maximal ready groups;
- cross-remote grouping;
- online admission control;
- work-aware remote placement.

The largest remaining opportunity is **not another static priority or batch-size
constant**. It is replacing coarse global decisions with a score-aware controller
that prices each millisecond of TDR, TPOT, and makespan at the moment an action is
chosen.

Recommended implementation order:

1. startup fluid optimization over decode concurrency and remote count;
2. marginal-score action selection on `E`;
3. dynamic, dispatch-time prefill chunking;
4. shallow rollout over the next known events;
5. empirical residual-output estimates for remote placement.

## What the current judge data says

The recoverable-score analysis in `JUDGE_PARAMS.md` gives three high-value
regimes:

- **#3:** waiting-only; both TDR and TPOT must fall substantially;
- **#14 and other narrow clamps:** throughput is already close to `tp_UB`, so a
  small throughput improvement or earlier switch to waiting optimization can
  recover many points;
- **#4/#8/#13:** mixed regimes requiring a better marginal trade-off rather than
  a globally throughput-first or waiting-first policy.

Tests #5/#6 are far from `tp_UB`; the measured resource bounds indicate that they
are poor optimization targets compared with #3/#14 and the narrow-clamp family.

## Research translated to this problem

### Controlled batching, not fixed waiting

[Batchy](https://www.usenix.org/conference/nsdi20/presentation/levai) treats batch
formation as controlled queueing under a delay SLO. Its useful ideas here are:

- batch only where fixed per-batch cost is large;
- expose a backlog trigger rather than a fixed timeout;
- update the trigger with a one-step receding-horizon controller;
- react aggressively to an SLO violation and cautiously to additional slack.

The current `DGFRAC` is a coarse global backlog trigger. Replace it with a trigger
computed from the exact decode curves and current TPOT slack.

### Just-enough service to reach the scoring clamp

[JITServe](https://www.usenix.org/conference/nsdi26/presentation/zhang-wei)
allocates only the bandwidth needed to meet each request's SLO and ranks work by
payoff per unit resource. The direct contest translation is:

- `tp_UB` is the maximum useful throughput; throughput above it has zero value;
- `tp_base` and `tp_UB` define the exact marginal throughput score;
- after projected throughput reaches `tp_UB`, all marginal capacity should protect
  TDR/TPOT;
- action choice should use marginal score, not only `w_tp` versus `w_c` or points
  remaining in each component.

### Stall-free prefill

[Sarathi-Serve](https://www.usenix.org/conference/osdi24/presentation/agrawal)
chunks long prefills so they can coexist with ongoing decode without generation
stalls. Static chunking is unsafe in this contest because every extra piece pays
another `S`, but **dispatch-time conditional chunking** is still promising:

- keep one piece when no decode request is blocked on that remote;
- split only when the current prefill piece would consume meaningful TPOT slack;
- choose the next piece endpoint at dispatch time, after observing current queues;
- stop chunking as soon as decode pressure disappears.

[Orca](https://www.usenix.org/conference/osdi22/presentation/yu) supports the
existing iteration-level scheduling direction: decode membership should be
reconsidered every token rather than frozen for an entire response.

### Unknown output lengths

[FastServe](https://www.usenix.org/conference/nsdi26/presentation/wu-bingyang)
uses a skip-join multilevel feedback queue because output lengths are unknown.
Classical unknown-size scheduling likewise favors age-dependent policies;
[M-SERPT](https://arxiv.org/abs/1907.10792) is a simple constant-factor
approximation to the optimal Gittins policy for mean response time.

The contest does not permit migration, and TPOT averages token gaps rather than
request response time, so MLFQ should not directly replace maximal decode
batching. Its useful application is **remote-load estimation**:

- track tokens already produced for every active request;
- learn a completed-output-length histogram online;
- estimate `E[remaining | survived to age a]`;
- assign new requests to the remote with the smallest estimated residual decode
  work plus known prefill work.

Keep active-count balancing as the cold-start fallback because tests need not be
i.i.d.

### Setup-aware queue pressure

[Biased Max-Weight](https://arxiv.org/abs/1701.03831) shows why ordinary queue
pressure is insufficient when changing service modes incurs setup overhead. Here,
every task pays `S`, and transfers pay `latency_in_ms`. The scheduler should switch
from the current action family only when the score-weighted queue-pressure gain
exceeds these fixed costs.

[Drift-plus-penalty](https://arxiv.org/abs/1011.5942) supplies the broader pattern:
choose each variable-duration action by its ratio of queue-drift reduction plus
reward to action duration. This matches this interactor better than a controller
that adjusts only `Ntarget` every 16 or 64 observations.

## Proposed score-gradient controller

For the current estimates, define:

```text
e_tdr  = max(0, (tdr_hat  - SLO1) / SLO1)
e_tpot = max(0, (tpot_hat - SLO2) / SLO2)
dist   = hypot(e_tdr, e_tpot)
```

Inside the unclamped scoring ranges, the marginal values are:

```text
lambda_tp   = w_tp / (tp_UB - tp_base)
lambda_tdr  = w_c / dist_base * e_tdr  / (dist * SLO1)
lambda_tpot = w_c / dist_base * e_tpot / (dist * SLO2)
```

Use zero for a derivative whose component is already clamped. Handle
`dist_base == 0` separately with virtual deficits and a safety margin; its
waiting score is discontinuous and has no useful derivative.

There is also an exact queueing interpretation:

- each millisecond with `q_prefill` arrived-but-not-ready requests adds
  `q_prefill` milliseconds to the eventual TDR sum;
- each millisecond with `q_gap` requests between consecutive tokens adds
  `q_gap` milliseconds to the eventual TPOT numerator;
- delaying the final token increases makespan and lowers `tp`.

Therefore candidate action `a` should be compared using a short-horizon index of
the form:

```text
value(a) = predicted throughput gain
         - lambda_tdr  * predicted added TDR sum
         - lambda_tpot * predicted added gap sum
         - setup/link switching penalty
```

Divide by the time until the next decision point. Evaluate all currently legal
`E` actions (`P PRE`, `P POST`, `D PRE`, `D POST`) instead of selecting from a
fixed permutation. The branching factor is at most four.

## Startup fluid optimizer

The task table is fully known before arrivals. Enumerate candidate concurrency
`n = 1..2000` and remote count `r = 1..K`. A first-order steady-state rate is:

```text
X_E(n)    = n / (2*S + dpre(n) + dpost(n))
X_link    = n / (r*latency + n*b)
X_remote  = n / (S + dproc(max(1, n/r)))
X(n,r)    = min(X_E, X_link, X_remote)
TPOT(n,r) = n / X(n,r)
```

This improves on the current startup estimate because it includes per-transfer
latency and searches `n` and `r` jointly. Score every candidate using:

- `min(X(n,r), tp_UB)` for useful throughput;
- `TPOT(n,r)` for the steady-state gap estimate;
- the known unloaded TDR floor;
- the actual score clamps and weights.

Use the best candidate as an initial operating point, then let online feedback
correct it. This should reduce irreversible startup damage on short tests.

Important leaked structure from the scoring line:

- small `tp_UB / tp_base` means the throughput window is cheap to saturate;
- `tp_UB` below the physical ceiling means excess batching has no score value;
- `SLO1` below the unloaded TDR floor makes the TDR excess unavoidable;
- `SLO2` below the decode-loop floor makes TPOT infeasible;
- `dist_base == 0` requires a feasibility policy, not smooth optimization.

## Dynamic prefill chunk rule

Do not decide all pieces at admission. When a remote is about to run `P PROC`:

1. compute the full remaining prefill duration;
2. count decode requests on that remote with an open token gap;
3. estimate the non-prefill decode-loop latency;
4. let `gap_budget = SLO2 - predicted_nonprefill_gap`;
5. if the full piece exceeds the useful gap budget, evaluate a shorter legal
   layer range;
6. split only if the predicted TPOT-score gain exceeds the extra `S` cost paid
   into TDR and throughput.

A practical initial inequality is:

```text
lambda_tpot * blocked_decoders * avoided_blocking
    > lambda_tdr * extra_schedule_cost
      + lambda_tp * predicted_throughput_loss
```

This is the contest-specific version of stall-free batching.

## Short-horizon rollout

The durations of all running tasks are known from the table, and already queued
transfers are FIFO. Maintain predicted release times for `E`, every remote, `UP`,
and `DOWN`. At each free-`E` frame:

- clone the compact scheduler state for each legal action;
- simulate until the next one or two known completion events;
- assume no unseen arrival inside the short horizon;
- score the resulting queue holding cost and useful throughput;
- execute only the first action and replan at the next real frame.

This is a small model-predictive controller, not an expensive global search. Four
root actions and a depth of two are enough for the first experiment.

## Local experiments completed

### Rejected: global `tp_UB` admission cap

A variant that always seeded concurrency with
`SLO2 * min(X_est, tp_UB)` improved the #3-like burst calibration from
`298.06` to `356.47` and one #14 calibration from `0` to `130.82`. Across 45
local cases, however, mean score fell from `573.46` to `568.87`, with severe
losses on prefill-heavy and burst workloads. The idea needs regime detection or
fluid-model scoring; it is not safe as a global rule.

### Rejected: finite decode-group cap

Sweeping `A_MAXG` over infinity, 128, 64, 32, 16, 8, 4, 2, and 1 produced:

```text
infinity mean = 562.121
oracle mean   = 562.143
```

Only one generated case gained more than noise (`+0.59`). Maximal ready decode
groups should remain the default.

### Conditional evidence: initial `E` priority

On one #3-like burst calibration, forced decode-first changed `298.06 -> 351.02`
and improved both TDR and TPOT. On a second burst pattern it changed
`400.25 -> 369.80`. This is strong evidence for state/action scoring and strong
evidence against another static priority order.

### Conditional evidence: chunking

Two prefill pieces changed one #3-like burst from `298.06 -> 314.98`, but changed
another from `400.25 -> 314.22`. Static chunk counts remain unsafe. Chunking must
depend on current remote decode pressure and predicted score gain.

### Rejected: more fairness tuning

`A_PFAIR` values from decode-always through strict alternation were effectively
identical on the generated physical corpus except that the most aggressive
prefill preference slightly reduced throughput and increased TDR. This knob is
not a leading opportunity.

## Ranked experiment plan

1. **Startup `(n,r)` fluid enumeration** — low implementation risk, uses only
   published data, directly exploits `tp_UB` and transfer latency.
2. **Dynamic `E` action index** — highest expected score gain; ablate first on
   #3-like, narrow-clamp, burst, and prefill-heavy held-out sets.
3. **Dispatch-time chunk endpoint** — enable only when the action index predicts
   positive marginal score.
4. **Depth-2 rollout** — compare against the action-index result; retain only if
   it adds material value over the simpler controller.
5. **Survival-based remote load** — modest expected gain and higher overfitting
   risk; keep behind a feature flag until held-out results are stable.

Promotion criteria:

- no protocol failures across all stress tests;
- no regression on Example 1;
- gains on calibration-independent `tp/tdr/tpot`, not only invented local score;
- improvement across multiple arrival patterns within the target regime;
- no test-ID or preliminary-test-specific branches.
