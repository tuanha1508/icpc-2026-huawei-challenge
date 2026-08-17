# Breaking the 16265 plateau — deep research findings

Research date: 2026-08-17. Contest ends 2026-08-28 10:59 UTC (~11 days left).
Method: 5-angle fan-out web search → 20 sources fetched → 97 claims extracted →
25 verified by 3-vote adversarial verification (20 confirmed, 5 refuted).
Every claim below carries its source; refuted claims are listed at the end so we
do not act on them.

---

## 0. The one-line diagnosis

We are doing the thing that every source says does not work, and not doing the
thing that two independent lines of evidence say does.

- **What we're doing**: 80+ policy knobs swept single- and pairwise on 9
  hand-fitted proxy tests, 0.8s of a 15s budget, purely reactive greedy.
- **Psyho's improvement priority order**: transition/neighborhood design >
  evaluation speed > **parameter tuning last**. "Never start from parameter
  tuning." ([ozy4dm annotation of Psyho's tips](https://ozy4dm.hateblo.jp/entry/2022/12/22/162046))
- **Psyho on our exact failure mode**: when local results fail to transfer, the
  prescribed remedy is *more test cases* — on the order of **2,000–5,000 tests
  per iteration** before drawing a conclusion. We are drawing conclusions from 9.

The five proxy-positive/judge-zero submissions are not a mystery. They are the
expected outcome of a statistically underpowered, hand-fitted local corpus.

---

## 1. What prior Huawei-challenge winners actually did

**2020 ICPC NERC Huawei Cloud Scheduling Challenge** (closest prior art in this
contest family):

- Top-12 finishers describe their winning solutions as **randomized greedy re-run
  repeatedly until the time limit** — *not* beam search, *not* tree search, *not*
  metaheuristics. In this contest family the breakthrough lever is randomized
  restarts on top of greedy, not replacing greedy.
- **jiangshibiao** used an explicit **portfolio**: 10+ distinct parameter sets,
  each run as a separate policy, keep the best result. This is exactly the
  actionable use of an idle CPU budget when single-knob tuning has plateaued —
  and it directly recycles our 80 swept knob settings instead of discarding them.
- **ashmelev** deliberately **under-used the time limit** (4s of an allowed
  5–5.5s) and *removed* optimizations, because only 30 of 50 tests were visible.
  A documented instance of our exact failure mode and the defensive response.
- Final scores at the top clustered within **~0.13%** (303218.41 → 303600.83
  across top 12). Our 16265 → 16300 gap is **0.22%**. This is normal territory
  for the plateau in this contest family; the gap is real but small.

**Sanity check on "I've hit a wall"**: measured score trajectories across a full
two-week AHC (AHC014) show competitors at *every* rank tier — including 1st place
— improving monotonically for the entire contest and continuing to beat their
in-contest best afterwards. A hard wall on day ~4 of 14 is not the normal
top-competitor experience.

**Counter-evidence, stated honestly**: long-format (1–2 week) heuristic contests
are explicitly characterized as **not** won by dropping in a standard
metaheuristic template. SA/beam-search templates suffice mainly for the 4-hour
format; long contests are won by a deeper problem-specific iterative process.
So "swap greedy for beam search" is *not* the recommendation. "Wrap greedy in
forward simulation and spend the idle 14.2s" is.

---

## 2. The core structural recommendation: fortified one-step rollout

### The empirical precedent (this is the convincing one)

**terry-u16 on AHC007** — an online problem where each edge must be irrevocably
accepted/rejected on arrival, i.e. structurally the same shape as ours (online,
irrevocable, unknown future).
([blog](http://blog.terry-u16.net/entry/ahc007-explanation))

| approach | score | rank |
|---|---|---|
| greedy, fixed cost estimate `2·d_i` | 13,885,749,353 | ~245 |
| greedy, **best-tuned** coefficient `1.75·d_i` | 14,083,488,435 | ~140 |
| **Monte-Carlo rollout, S=14 samples** | 14,146,906,243 | **54** |

Tuning the constant to its optimum: 245 → 140. Switching to forward simulation:
140 → 54. **The structural change was worth more than the best possible tuning
of the greedy's constant.** That is precisely our situation.

Three details from that writeup that matter for us:

1. **The rule is one-step rollout**: at each decision point, estimate the
   expected *final objective* under both "take the action" and "don't", by
   completing the trajectory with a downstream optimizer on sampled futures, and
   pick the better branch. Not a myopic local heuristic score.
2. **A single sampled future is too noisy.** Average over S independently sampled
   futures. S was set empirically to fill the time budget (S=14 in the reference
   impl; the author's Rust solution ran an estimated S=50–80 per decision).
3. **Deterministic point estimates are systematically biased** in the direction
   of the objective's min/selection operator — substituting the mean overestimates
   cost, because it ignores that the downstream optimizer will select the cheap
   realizations. *This is why sampling the true distribution beats any single
   tuned constant, and it is a mechanism, not a coincidence.* Our adaptive-N
   controller is exactly such a tuned point estimate.

### The theory (why it's safe)

Bertsekas & Castañon, *Rollout Algorithms for Stochastic Scheduling Problems*,
J. Heuristics 5:89–108 (1999) — [PDF](https://www.mit.edu/~dimitrib/quiz.pdf);
Bertsekas, *Rollout Algorithms for Discrete Optimization: A Survey* (2010) —
[PDF](https://web.mit.edu/dimitrib/www/Rollouts_Survey.pdf).

**Proposition 1** (verbatim): *"Let the base heuristic H be sequentially
consistent. Then the rollout algorithm R_H is terminating. Furthermore … the cost
of R_H starting from i1 is less or equal to the cost of H starting from i1."*

And: *"the index and the greedy heuristics … are sequentially consistent. This is
a manifestation of a more general property: many common base heuristics of the
greedy type are by nature sequentially consistent."*

**Three implementation constraints that void the guarantee if ignored:**

1. **Sequential consistency requires decisions to be a function of the simulated
   STATE only.** Our adaptive Little's-law concurrency cap `N` and the measured
   TDR/TPOT accumulators are history-dependent — they **must be carried inside
   the simulated node state**, or consistency breaks silently.
2. **The rollout must break ties in favour of the base heuristic's own next
   choice**, or termination fails (Bertsekas gives a non-terminating cycle
   counterexample).
3. The guarantee is on **final cost vs the base run from the start state** — not
   per-decision optimality, and never near-optimality: *"this does not guarantee
   that the path generated by R_H will be a near-optimal path, because the
   collection of paths generated by H may be poor."*

### Fortified rollout — ship this form, not plain rollout

*"A variant … called the fortified rollout algorithm … implicitly uses a
sequentially improving base heuristic, so that it has the cost improvement
property of Prop. 2."*

Mechanism: **store the best complete simulated schedule found so far, keep
following it, and deviate only when the current lookahead STRICTLY beats its
cost. Ties keep the cached path.** When the base is already sequentially
consistent, fortified and plain rollout coincide — so fortifying is free
insurance, never harmful.

**Critical detail**: the simple comparison form is for terminal-cost-only
formulations. We have **additive per-step costs** (the fixed schedule cost `S`
per task, transfer times), so we must use the survey's p.13 additive form:

```
min_{j ∈ N(i_m)} [ c(i_m, j) + H(j) ]
    <  g(i*_k) + c(i_m, i*_{m+1}) + Σ_{l=m+1}^{k-1} c(i*_l, i*_{l+1})
```

Using the simple form with additive costs silently breaks the guarantee.

**Why fortified is the risk-correct form for us specifically**: a miscalibrated
simulator degrades toward our current scheduler rather than *below* it. Given
that our last five "improvements" were judge no-ops, we need a change whose
downside is bounded at "no worse than V103."

### Cost budgeting

*"a rollout policy involves N + (N−1) + … + (N−M) = O(MN) applications of the
base heuristic … if the running time of the base heuristic is polynomial, so is
the running time of the corresponding rollout algorithm."*

Budget as **(branching events) × (candidate actions) × (1–3 futures)**. The
authors explicitly **reject** full Monte-Carlo scenario evaluation as too
expensive and substitute a small fixed set of certainty-equivalent scenarios.
Note O(MN) is for **one-step** lookahead only; deeper lookahead grows
exponentially in depth. Do not go past one step.

### Expected magnitude — do not over-budget on this

One-step rollout recovered ≥50% of the base heuristic's optimality gap in every
case tested (41%→75% and 43%→77% of exact-DP optimal at the hardest setting).
**But the lift collapses as the base gets better**: 76%→90% and 80%→90% at the
easiest setting. Our base is tuned across 80+ knobs, so **expect the small-lift
regime.** The 41→75 headline is not our number.

### Parallel rollout — how to recycle the 80 swept knobs

*"use all of these heuristics in parallel within the rollout framework,
essentially by combining them into a single superheuristic"*, `H(i) = min_k H_k(i)`,
and *"if all the algorithms H_1,…,H_K are sequentially improving, the same is
true for H."* The improvement guarantee is then against **the best of the K
policies at the root**, not the average.
(Stochastic analogue proved independently: Chang, Givan & Chong, *Parallel
Rollout for Online Solution of POMDPs*, DEDS 14(3), 2004 —
[PDF](https://engineering.purdue.edu/~givan/papers/deds01.pdf))

This is the principled version of jiangshibiao's 10-parameter-set portfolio, and
it is the right home for 3–5 of our distinct knob configurations — **one per
bottleneck family** — evaluated per-frame instead of frozen offline.

Two framing nits: (a) parallel rollout scores candidate **next actions** by
`min_k H_k(action)`; it is *not* "pick whichever whole policy scores best and
follow it to the end", which is weaker. (b) The survey offers a weighted blend
`H(i) = Σ_k r_k H_k(i)` for which **no preservation property is claimed** — do
not use weighted blending if we want the guarantee.

---

## 3. The hidden-future problem: predicting `L_out` and `R`

Rollout needs an assumed future. Ours is genuinely unknown: `R` unannounced,
`L_out` hidden until `FIN`. Two verified tools:

### 3a. A two-class long/short predictor is the right first move

Mitzenmacher & Shahout, *Queueing, Predictions, and LLMs*, INFORMS Stochastic
Systems 2025 — [arXiv:2503.07545](https://arxiv.org/abs/2503.07545).

> *"1-bit predictions obtain a large fraction of the benefit of full predictions
> (which corresponds to SPRPT) in the cases studied"*

Recomputed from their Tables 2–3: exponential λ=0.98 → **84%**, λ=0.50 → **89%**,
Weibull λ=0.98 → **94%** of the full-size-prediction benefit.

> *"the right performance metric for 1-bit predictions is not the fraction of
> correct predictions, because predicting long jobs correctly is more important
> than predicting short jobs correctly. A mispredicted long job can be placed in
> front of several shorter jobs, blocking them from service… A mispredicted short
> job, however, is only itself hurt."*

**→ Tune the predictor for LONG-job recall, not accuracy.**

Two qualifiers: (1) "large fraction of the FIFO gap" still leaves 1-bit **31%
worse** than SPRPT in absolute mean response time at λ=0.98, and 2.7× worse than
clairvoyant SRPT in the Weibull case. (2) Scope is M/G/1, mean response time —
no batching, no flow shop, no SLO metric. The head-of-line-blocking mechanism is
**weaker** for us because maximal decode batching serves all ready requests
together anyway. Go past 1 bit where cheap: SkipPredict
([arXiv:2402.03564](https://arxiv.org/abs/2402.03564), NeurIPS 2024) pays for
full predictions only on predicted-long jobs and beats pure 1-bit when prediction
is cheap — which for us it is.

### 3b. M-SERPT — the index to rank requests by estimated remaining decode

Scully, Harchol-Balter & Scheller-Wolf, *Simple Near-Optimal Scheduling for the
M/G/1*, SIGMETRICS/POMACS 2020 — [arXiv:1907.10792](https://arxiv.org/pdf/1907.10792).

```
rank(a) = max over b ≤ a of  E[X − b | X > b]
```

the increasing envelope of expected remaining size, so a job's rank never
improves. Computable with **one suffix-sum pass plus one running-max pass over
the empirical `L_out` histogram we accumulate from `FIN` events.**

> *"we prove the mean response time ratio between M-SERPT and Gittins is at most
> 3 for load ρ ≤ 8/9 and at most 5 for any load. This makes M-SERPT the only
> non-Gittins scheduling policy known to have a constant-factor approximation
> ratio for mean response time."*

Use it as a **principled priority key, not a score guarantee** — the bound is
M/G/1, single server, free preemption, mean response time only, and does not
transfer to our clamped throughput+SLO-distance objective.

---

## 4. The admission layer: prefill vs decode

This problem is a thin disguise of LLM inference serving, and the dilemma is
named and well-mapped.

Sarathi-Serve, OSDI'24 — [PDF](https://www.usenix.org/system/files/osdi24-agrawal.pdf)
/ [arXiv:2403.02310](https://arxiv.org/abs/2403.02310). Fig. 2 caption verbatim:

> *"Prioritizing prefills optimizes throughput but sacrifices TBT tail latency
> whereas prioritizing decodes has the opposite effect."*

Both pure poles rejected: *"none of them is ideal when optimizing throughput and
latency are both important."* TaiChi ([arXiv:2508.01989](https://arxiv.org/abs/2508.01989))
restates our exact tradeoff: *"Every prefill token inserted into a decoding batch
lengthens the iteration and delays the next token for other users, while not
inserting it delays the first token for new arrivals."*

**Transfer caveat**: their mechanism is single-GPU co-batching interference,
whereas in 2251A prefill is *always* single-request and never co-batched with
decode. The dichotomy transfers as **resource/link serialization contention
across E, UP, remote and DOWN** — it gives us the correct policy *axis*, not
drop-in numbers.

### Two implementable rules, and they compose

**(A) Sarathi-Serve stall-free batching** (Algorithm 3, structure verified):
compute a per-iteration budget from the latency SLO, then in strict order —

1. pack **all running decodes**;
2. then any **partially-completed prefill**;
3. then admit **new prefill chunked into the leftover budget**.

*"stall-free batching ensures that decodes never experience a generation stall
due to a co-running prefill chunk."* Note this maps directly onto our existing
`P PROC` layer-range splitting — **that IS chunked prefill**. We measured
chunking as a trap because of the extra `S` per piece; the literature's claim is
about the **ordering rule**, which we can adopt without chunking.

Caveat: the token budget is **not** a closed-form SLO formula — §4.3 admits it
*"is a complex decision which depends on the desired TBT SLO, parallelism
configuration, and specific hardware properties"* and they tune it offline. For
us it is a per-batch duration cap implied by SLO2 plus the fixed `S`.

**(B) SLAI last-schedulable-time index** (Bari, Hegde, de Veciana, POMACS 9(3)
Art.59, Dec 2025 — [arXiv:2508.01002](https://arxiv.org/abs/2508.01002), code at
[github.com/agrimUT/SLAI](https://github.com/agrimUT/SLAI)), Eq. (8):

```
L_{n,r} = t_{n-1,r} + TBT_r − Θ · c_batch
```

end of the batch containing the previous decode, plus the per-token deadline,
minus an offset times running-average batch execution time. A decode is
**"critical"** only once wall-clock passes `L`; until then it is **deferred so
budget goes to prefill instead**. Batch construction order: critical decodes in
increasing `L`, then active prefills, then new prefills, then non-critical
decodes if budget remains. Published Θ=10 fixed; dynamic variant uses 5 below a
memory threshold else 10. *"a smaller Θ delays when decode-iterations are
considered critical (favoring prefill-phase requests), while a larger Θ marks
them critical sooner."*

**Θ is literally the tunable knob on our TDR-vs-TPOT tradeoff.**

**Four caveats before porting:**
1. "Never displaces" is *bounded delay*, not zero impact.
2. SLAI documents an **over-deferral failure mode**: with Θ too small, deferred
   decodes accumulate, block new prefill admission, and *"TTFT blows up"*. There
   is an interior optimum — hence their dynamic Θ.
3. **This interacts destructively with our existing adaptive-N cap**: both are
   controllers acting on the same variable. Do not run both unmodified.
4. SLAI targets a **per-request TBT deadline**; our SLO2 is a **mean TPOT**. A
   synthetic per-request `TBT_r` must be constructed. The *index* ports cleanly;
   the batch-construction loop (one shared token budget, one GPU) does not.

Reported SLAI gains (53% median TTFT reduction, 26% capacity increase over
Sarathi-Serve) are single-model/single-GPU — **do not assume the magnitude
transfers.**

### Our "maximal decode batching is always correct" is an untested assumption

Shen, Gupta & Buscher, *Flow shop batching and scheduling with sequence-dependent
setup times*, J. Scheduling 17(4):353–370 (2014) —
[Springer](https://link.springer.com/article/10.1007/s10951-014-0369-x):

> *"We consider violating the group technology assumption by dividing product
> families into batches… inconsistent batches are formed on different machines,
> which lead to non-permutation schedules… various experiments conducted on the
> benchmark problem instances confirm the benefits of batching… it will be
> prudent for the practitioners to consider adopting inconsistent batches and
> non-permutation schedules."*

Confidence **medium**, not high: their setups are sequence-*dependent* family
setups (ours is a fixed sequence-*independent* `S`), single experimental study,
makespan objective only, low citation count. Transfer is analogy, not
entailment.

**But the actionable reading stands**: batch composition should differ across
stages, and under-full batches can beat maximal ones once per-batch overhead and
downstream serialization are priced in. **This is one of the few structural
choices our knob sweeps could not explore — and a rollout over our exact cost
model can answer it directly rather than by rule.**

---

## 5. The real disease: why proxies say +X and the judge says 0

This is the highest-value finding in the whole report, and it is a
*test-distribution* diagnosis, not a policy one.

**AHC's official input generator is the very same tool used to produce the
judge's hidden tests, for both the public and private evaluation sets.** In AHC,
the local proxy is **faithful by construction**. That is the structural
precondition our hand-fitted proxies lack. Our failure mode is a
**test-distribution mismatch**, not a policy problem — which is exactly why every
policy-level fix has failed to move the judge.

Corrective practices, all from top-competitor tooling:

- **Volume**: Psyho prescribes **2,000–5,000 tests per iteration** before drawing
  a conclusion. We use 9 fitted proxies. Even a perfectly faithful generator at
  n=9 cannot resolve a 0.22% effect.
- **Relative, paired scoring**: [psytester](https://github.com/FakePsyho/psytester)
  (Psyho's own harness) defaults to **relative** scoring — each test normalized
  as `YOUR_SCORE / BEST_SCORE` against the best across all stored results files.
  That is the paired-per-test comparison needed to detect small real gains,
  instead of a raw mean that a few tests dominate. Directly applicable to a
  20-test frozen judge with clamped per-test scores.
- **Persist every run**: every run saved as a per-test JSON results file, multiple
  results files compared side by side on one scoreboard. Historical persistence —
  not just the latest aggregate — is what makes relative scoring and regression
  detection possible.
- **⚠ Parallel-harness timing warning**: psytester's README explicitly warns that
  running tests concurrently across threads **changes execution speed**, so
  locally measured timings under a parallel harness do not match single-run
  timings. **This becomes critical the moment we start using the time budget** —
  our `tools/sweep_policy.py` runs parallel. Any timing-sensitive verdict needs a
  serial re-run.
- **Validate the harness itself** with a deliberately tiny run before trusting
  any batch.

**And the theoretical warning**: every rollout guarantee holds relative to *our
simulator's assumed future*, not the judge's actual one. Bertsekas & Castañon's
stochastic guarantee presumes **exact** evaluation of the base policy's expected
cost; under Monte-Carlo or certainty-equivalent estimation it degrades to
approximate. **This is structurally the same trap we are already in, one level
deeper.** The one genuine mitigation in the corpus is fortified rollout.

---

## 6. Contest metagame — act on this immediately

Two confirmed rule facts that should govern submission strategy *before* any
rewrite.

**(1) The 22 preliminary tests are feedback-only.** From the statement's "Contest
aggregation" section (verified against our own archived PDF and
`docs/statement/PROBLEM.md:608-612`):

> *"The 22 preliminary tests provide feedback and do not contribute to the final
> ranking. The final score is the arithmetic mean of the 20 frozen final-test
> scores."*

**Our 16265 is a noisy proxy for what actually counts, and tuning to it is an
explicit overfitting hazard.** A rollout rewrite showing *flat* preliminary
results is not necessarily worse on the frozen set — but we have no way to
distinguish that from a genuine no-op, which is again why the fortified form
(degrades to greedy, never below) is the risk-correct thing to ship.

**(2) ~~Only the LATEST positive-scoring submission is evaluated.~~ CORRECTED
2026-08-17 by the contestant: the contest keeps the BEST (highest) score across
all submissions, not the latest.** The "latest submission" claim previously cited
here (organizer comment on blog 155646) does not govern this contest; treat the
correction as authoritative.

**→ Every submission is free upside. There is no fallback to protect and no
reason to ever re-submit an older source.** V106 scoring 16241.75 (−21.42) cost
us nothing; 16263.193 remains banked.

> ## ⚠ HARD RULE FOR THE REST OF THE CONTEST
> **Ship aggressively. Losses are free.** Best-of-all-submissions scoring means
> the only real cost of a candidate is the time to build it. Never spend a
> submission restoring old code, and never soften a candidate to protect a
> banked score. The fortified-rollout argument still holds on *engineering*
> grounds (bounded downside aids debugging), but NOT as score insurance.

---

## 7. Proposed plan (~11 days)

**Day 1 — instrumentation before any policy change.**
- Fix the test corpus first. Build a generator sweeping the *declared constraint
  space* (K, S, latency, bandwidth, num_layers, SLO1/SLO2, w_tp, tp_base/tp_UB,
  arrival processes) rather than fitting 9 judge tests. Target 500–2000 cases.
- Convert `tools/sweep_policy.py` to **paired relative scoring** vs a stored
  baseline results file, persisted per run. Add a serial re-run mode for any
  timing-sensitive verdict.
- Run the "is compute worth anything" diagnostic before building anything.

**Days 2–4 — port the simulator into the solver.**
- `tools/interactor.py` (706 lines) already is an exact event-driven replica:
  event heap, FIFO UP/DOWN queues, piecewise-linear `Curve`, exact scorer. Port
  its core to C++ inside `main.cpp`. This is a mechanical port, not research.
- Validate: replaying our own decisions through the internal simulator must
  reproduce the interactor's timestamps to the digit on Example 1.

**Days 4–7 — fortified one-step rollout.**
- Refactor the reactive policy into `base_policy(SimState) -> action` with **all**
  controller state (N cap, TDR/TPOT accumulators) inside `SimState`.
- At each frame: enumerate candidate actions for E and each free remote; for
  each, simulate to completion under the base policy over 1–3 sampled futures;
  score with the real score function; take the best.
- **Fortified**: cache best complete continuation, deviate only on strict
  improvement, using the **additive-cost** comparison form (we have per-task `S`).
- Tie-break in favour of the base heuristic's own next choice.
- Time-budget the sample count `S` to fill ~10s, leaving headroom (ashmelev's
  defensive under-use).

**Days 7–9 — the future model + index layer.**
- Learn the `L_out` histogram online from `FIN` events → M-SERPT rank
  (suffix-sum + running-max).
- Two-class long/short predictor, tuned for **long-job recall**.
- Sample futures from the learned distributions — **do not use the mean**
  (systematic selection bias).
- Fold 3–5 existing knob configs in as a **parallel-rollout portfolio**,
  `min_k H_k(action)`, one per bottleneck family. Never weighted blending.

**Days 9–10 — admission layer, only if rollout lands.**
- SLAI-style deferral index with synthetic per-request `TBT_r` from SLO2.
- **Disable or merge the existing adaptive-N cap** — two controllers, one
  variable.
- Watch for the documented over-deferral blowup.

**Day 11 — no fallback needed.**
- Best-of-all-submissions scoring: keep shipping candidates to the last minute.
  Nothing to restore, nothing to protect.

---

## 8. Refuted — do NOT act on these

Five claims were adversarially refuted during verification:

1. ✗ *"Rollout is guaranteed not to deteriorate performance"* stated
   unconditionally (0-3). The guarantee **requires** sequential
   consistency/improvement or fortification.
2. ✗ *"Gittins is the mean-response-time-optimal policy for the unknown-size /
   known-distribution case"* (0-3).
3. ✗ *"Exact Gittins is O(n²)-impractical"* (0-3).
4. ✗ *"A crude >50%-error `L_out` predictor still beats going blind"* (1-2).
   **Do not deploy a badly-calibrated predictor on this basis.**
5. ✗ *"Decode throughput grows linearly with batch size while prefill saturates
   at one request"* (1-2). **Do not use this asymmetry to justify maximal decode
   batching** — that assumption is exactly what §4 says to re-test.

---

## 9. Known gaps in this research

- **Score-clamp exploitation and hidden-weight recovery were not answered.** No
  verified source addresses detecting which clamped component is pinned, or
  recovering hidden per-test weights from reported scores. Our own `w_tp`
  recovery work remains the best available method — treat this as *unresearched*,
  not answered-in-the-negative.
- **Model mismatch is pervasive and cumulative.** Every scheduling-theory result
  cited assumes identical parallel machines with objective `Σ w_j C_j`; every
  LLM-serving result assumes one GPU with a shared per-iteration token budget.
  Our problem is a 3-stage flow shop with a shared serial bidirectional link,
  permanently-assigned remotes, fixed per-task `S`, arbitrary decode batching,
  and a **clamped** throughput+SLO-distance score. **No cited bound transfers to
  that objective.** What transfers is mechanism and index *shape*. This is
  exactly why the rollout wrapper — which evaluates *our* exact cost model rather
  than importing someone else's bound — is the recommendation with the least
  mismatch risk, and why importing M-SERPT or SLAI as raw formulas without
  simulator validation would repeat our current failure mode at a new level.
- Three verifier sessions exhausted their web-search budget (affecting the
  flow-shop batching, Sarathi-Serve dichotomy, stall-free batching, and SLAI
  claims). For those, "no contradicting evidence" rests on primary-source reading
  plus bibliographic cross-checks, not an adversarial sweep.

### One open question worth a day if the rollout stalls

Can the online-computable WSEPT/LP lower bound (Goemans, Queyranne, Schulz,
Skutella & Wang, SIAM J. Discrete Math. 15:165–192; Schulz, *Stochastic Online
Scheduling Revisited*, COCOA 2008 —
[PDF](https://web.mit.edu/schulz/www/epapers/s-cocoa-2008.pdf)) be adapted to our
3-stage flow shop as an **independent per-test ceiling estimate**? Run a
preemptive WSPT rule on a virtual single machine of speed `m` (using
`p_j = μ_j / m`); its mean busy-time vector is an **exact optimal solution to the
LP relaxation**, computable online and incrementally in O(n log n).

That would **independently validate or refute our bottleneck taxonomy**, which
currently rests on the very same proxies that produced five no-op submissions.
Right now we have no independent check that #10/#21/#4/#5 are genuinely at a
physical ceiling versus merely at a ceiling our proxies can see.

---

# Appendix A — algorithm index (implementable specs)

Tier 1 evaluates **our own** cost model, so it carries the least model-mismatch
risk. Tier 2 are index *shapes* imported from models that do not match ours
(M/G/1, single-GPU, identical parallel machines) — validate each in the simulator
before shipping, or we repeat the current failure mode one level up.

| # | Algorithm | Role | Tier |
|---|---|---|---|
| A1 | Fortified one-step rollout | main policy wrapper | 1 |
| A2 | Parallel rollout (superheuristic) | portfolio over knob configs | 1 |
| A3 | Monte-Carlo future sampling | supplies A1's unknown future | 1 |
| A4 | M-SERPT index | request priority key | 2 |
| A5 | Two-class `L_out` predictor | feeds A3/A4 | 2 |
| A6 | Sarathi stall-free ordering | prefill/decode admission order | 2 |
| A7 | SLAI last-schedulable-time | decode deferral index | 2 |
| A8 | DSOS α-point dispatch | deterministic delay-then-dispatch | 2 |
| A9 | WSEPT/LP online lower bound | **diagnostic**, not a policy | 2 |

## A1. Fortified one-step rollout

```
# state MUST include the N cap and the TDR/TPOT accumulators,
# or sequential consistency (and the guarantee) breaks.
cached      = best complete simulated schedule so far
g(cached)   = its total cost

on each frame:
    A = legal actions (E's task choice) x (each free remote's choice)
    for a in A:
        cost[a] = mean over s in 1..S of
                  simulate_to_completion(state, a, base_policy, future_s)
    best = argmin_a [ c(state,a) + cost[a] ]      # ties -> base policy's choice

    # ADDITIVE-cost fortified test (we pay S per task, so the simple
    # terminal-cost form is WRONG and silently voids the guarantee):
    if c(state,best) + cost[best]
         < g(cached) + c(state, cached.next)
                     + sum of remaining step costs along cached:
        commit best;  cached = resulting path
    else:
        commit cached.next                        # ties keep cached
```

Guarantee: cost ≤ base policy's cost. Cost: O(M·N) base-heuristic calls ×
S futures. **One step only** — depth grows exponentially.

## A2. Parallel rollout

`H(i) = min_k H_k(i)` over K policy variants. Score candidate **actions**, not
whole policies. If every `H_k` is sequentially improving, so is `H`, and the
guarantee is against the **best** of the K at the root. **Never** the weighted
form `Σ r_k H_k(i)` — no preservation property is claimed for it.

## A3. Monte-Carlo future sampling (AHC007 recipe)

Draw S independent futures from the online-learned arrival process and `L_out`
distribution; average the completed-trajectory score. S=14 was enough to move
rank 140→54 there; 50–80 if the budget allows. **Never substitute the mean** —
point estimates are systematically biased in the direction of the objective's
selection operator, which is the whole reason sampling beats a tuned constant.

## A4. M-SERPT index

From the empirical `L_out` histogram accumulated at `FIN` (`a` = decode
iterations already completed):

```
tail(b)   = P(X > b)
serpt(b)  = ( sum_{x>b} (x-b)*p(x) ) / tail(b)      # one suffix-sum pass
rank(a)   = max over b <= a of serpt(b)             # one running-max pass
```

Serve minimum rank. ≤3-approx to Gittins for ρ ≤ 8/9, ≤5 at any load.

## A5. Two-class `L_out` predictor

Binary long/short from features known at `ARR` (chiefly `L_in`). **Tune for
long-job recall, not accuracy** — a mispredicted long job blocks several short
ones; a mispredicted short job only hurts itself. Captures 84–94% of full
size-prediction benefit. Escalate to full prediction on predicted-long jobs only
(SkipPredict).

## A6. Sarathi-Serve stall-free ordering

Per scheduling round, in strict order: **(1) all running decodes → (2) any
partially-completed prefill → (3) new prefill into the leftover budget.** Prefill
enters residual capacity only, never displacing in-flight decode. Adopt the
*ordering* without adopting chunking (our chunking pays an extra `S` per piece).

## A7. SLAI last-schedulable-time

```
L(n,r) = t(n-1,r) + TBT_r - Theta * c_batch        # Theta = 10; 5 when tight
```

A decode is *critical* only once wall-clock passes `L`; until then defer it and
give the budget to prefill. Batch order: critical decodes by increasing `L` →
active prefills → new prefills → non-critical decodes. Θ is the direct
TDR-vs-TPOT knob. **Two traps**: documented over-deferral blowup (deferred
decodes accumulate, block admission, TTFT explodes), and it collides with our
existing adaptive-N cap — two controllers, one variable.

## A8. DSOS — deterministic α-point dispatch

*(Schulz, COCOA 2008, §4 — omitted from the main text above.)*

```
alpha_j = phi - 1 ~= 0.618          # golden ratio minus one, same for all jobs
virtual machine of speed m, using p_j = mu_j / m      # NOT mu_j
run preemptive WSPT (highest weight/processing ratio) on the virtual machine
job j becomes dispatchable when it reaches its alpha_j-point there
whenever a real machine frees:
    start the not-yet-processed job with the SMALLEST alpha-point
    among those whose alpha-points have already passed
```

`max{φ+1, ((φ+1)/2)·Δ + (φ+3)/2}`-competitive: **2.618** at Δ=0, **3.618** at
Δ=1 (NBUE). Still the best known deterministic bound for identical machines as
of 2022. Note how structurally close this is to A7 — both say *do not dispatch
at the earliest possible moment; dispatch at a tuned fraction of the way to the
deadline.* The randomized variant RSOS is (2+Δ)-competitive but requires
dispatch to a **uniformly random** machine (replacing that with our
least-queued-work rule voids the analysis).

## A9. WSEPT/LP online lower bound — run this first

The mean busy-time vector of preemptive WSPT on the virtual speed-`m` machine is
an **exact optimal solution to the LP relaxation** of the stochastic
parallel-machine problem, computable online and incrementally in O(n log n) with
an event-driven priority queue.

Value to us: an **independent per-test ceiling estimate** that does not come from
the proxies. It is the only tool in the corpus that can tell us whether
#10/#21/#4/#5 are genuinely at a physical ceiling or merely at a ceiling our
proxies can see — i.e. whether the "every test is walled" conclusion is real.
Cheap to build, and it decides whether the rest of this appendix is worth
implementing at all.
