# Problem A — analysis, bounds, and strategy

Derived from [`PROBLEM.md`](PROBLEM.md) and the verified cost model in
[`EXAMPLES.md`](EXAMPLES.md). Nothing here is guessed from the domain; every claim
traces to a statement sentence or to arithmetic on the stated cost model.

Notation used throughout:

```text
b     = 8 * bytes_per_token / (bandwidth_gbps * 1e6)     ms of link time per token of payload
lat   = latency_in_ms                                    ms per transfer, paid per transfer
S     = schedule cost, paid once per task (not per transfer)
m     = decode group size (members in one D PRE / D POST)
r     = number of distinct remotes represented in a decode group  (1 <= r <= K)
X     = system-wide token production rate (tokens/ms)
N     = number of requests concurrently in the decode loop
dpre(), dproc(), dpost(), ppre(), pproc(), ppost()  = piecewise-linear table lookups
```

## 1. What the machine actually is

Strip the LLM framing and this is a **three-stage reentrant flow shop with one
shared serial bottleneck**:

| Resource | Count | Serves |
|---|---|---|
| local computer `E` | **1** | `P PRE`, `P POST` (once per request) and `D PRE`, `D POST` (once per group-iteration) |
| remotes `C0..C(K-1)` | `K <= 8` | `P PROC` pieces, `D PROC` |
| `UP` link | **1**, serial FIFO | every local→remote transfer |
| `DOWN` link | **1**, serial FIFO | every remote→local transfer |

`E` is touched **twice per group-iteration** and the links are touched **once per
token per direction**. That is the whole game. The remotes are the only genuinely
parallel resource, and each request is pinned to one remote for life at `P PRE`.

## 2. The baseline is defined to score zero on throughput

Example 1's `tp_base = 0.022222222 = 1/45` is *exactly* the rate of the serial
schedule shown in the statement. The statement says so directly: `tp_base` "comes
from a fixed one-request-at-a-time reference schedule."

**Consequence: a correct-but-serial scheduler scores `0` on the throughput
component of every test, by construction.** The `w_tp` fraction of the score is
unreachable without real overlap — overlapping prefill with decode, overlapping
link with compute, and batching decode.

Conversely, on Example 1 the trivial schedule already meets both SLOs, so the
waiting half is free there (score 500). Expect the same shape on easy tests: **the
first ~half of the score is protocol correctness; the second half is pipelining.**

## 3. Hard ceilings computable at startup, before any request arrives

These fall straight out of the cost model and should be computed in the first
milliseconds of the run, then used to pick a policy regime.

### 3.1 Link throughput ceiling

Every token crosses `UP` once and `DOWN` once, each carrying `bytes_per_token`.
Each direction is serial, so:

```text
X <= 1 / b  =  bandwidth_gbps * 1e6 / (8 * bytes_per_token)      tokens/ms
```

and that is *before* prefill traffic, which additionally consumes
`lat + L_in[i]*b` on each direction per request. Since `L_in <= 4096`, **one
prefill transfer can cost as much link time as 4096 decode tokens.** On tests with
large `L_in` and small `bandwidth_gbps`, the run is link-bound and prefill traffic
is the dominant consumer.

### 3.2 Local-computer throughput ceiling

```text
X <= m / (2S + dpre(m) + dpost(m))          for the group size m actually used
```

**Exploit:** above the largest listed `batch_size` in a decode column, the lookup
is *constant* (statement: "above the largest size, use the last time"). So if the
table's largest decode row is `B`, then for `m > B` the numerator grows while the
denominator does not — **`E` cost per token falls to zero as `m` grows.** Check
`max(batch_size)` per decode column at startup; if it is well below `R`, oversized
groups are free local throughput and the link becomes the sole binding constraint.

### 3.3 TDR floor

An unloaded request cannot become decode-ready faster than:

```text
TDR_floor = 2S + ppre(L_in) + pproc(L_in) + ppost(L_in)
          + 2*lat + 2*L_in*b
          + (p-1)*S                      for p prefill pieces
```

If `SLO1 < TDR_floor`, `excess_tdr > 0` is unavoidable and the waiting component is
capped no matter what — **stop paying for TDR and spend the schedule on
throughput** (and vice versa: if `SLO1` is generous, prefill can be deferred freely
to protect decode).

### 3.4 TPOT floor

Consecutive tokens of one request require a full serial loop each time:

```text
TPOT_floor = min over m of [ 3S + dpre(m) + dproc(m_r) + dpost(m)
                             + 2*lat + (m_r + m)*b ]
```

**TPOT can never go below this loop latency**, however cleverly we schedule.
Compute it at startup and compare to `SLO2`.

### 3.5 Arrival-span ceiling on `tp`

`total_elapsed = last_token_time - first_arrival_time >= last_arrival - first_arrival`.
Arrivals span up to `10^9` ms. If the arrival stream is spread out, `tp` is
essentially fixed by the test generator and scheduling barely moves it — the
throughput component is then either free or unwinnable, and everything should go
into the waiting component. If arrivals burst at `t = 0`, scheduling determines
everything. **Detect which regime we are in from the observed arrival pattern.**

## 4. The central trade-off: Little's law ties TPOT to batch size

With `N` requests concurrently decoding and total rate `X`, each request gets
`X/N` tokens/ms, so:

```text
TPOT ~= max(TPOT_floor, N / X)
```

`X` grows with batch size (which requires large `N`), but `TPOT` degrades linearly
in `N`. The SLO constraint is therefore a **hard cap on concurrency**:

```text
N <= SLO2 * X
```

This is the single most important design equation. Bigger batches are not free:
they buy throughput and spend TPOT at a fixed exchange rate. The right operating
point is `N* = min(N that saturates the binding resource, SLO2 * X)`.

## 5. Policy must be a function of the scoring parameters

`w_tp`, `w_c`, `SLO1`, `SLO2`, `tp_base`, `tp_UB`, `dist_base` are all **read from
the input on line 2**. The solver can and should branch on them at runtime rather
than being tuned to one regime:

| Regime | Detection | Policy |
|---|---|---|
| Throughput-only | `w_c = 0` | maximal batching, ignore TDR/TPOT entirely, admit everything immediately |
| Waiting-only, binary | `w_tp = 0` and `dist_base = 0` | pure feasibility hunt: meet both SLO means with margin, then stop; extra throughput is worth exactly nothing |
| Waiting-only, graded | `w_tp = 0`, `dist_base > 0` | minimize `dist`; small groups, low concurrency |
| Mixed | both `> 0` | operate at `N = SLO2 * X`; spend surplus on throughput |
| Throughput already saturated | projected `tp >= tp_UB` | clamp is at 1.0 — **all further throughput is worthless**; divert everything to TDR/TPOT |
| Throughput unreachable | projected `tp <= tp_base` even at the resource ceiling | throughput component is 0 regardless; play pure waiting |

The two clamps mean effort outside `[tp_base, tp_UB]` is literally unscored. A
policy that estimates its own projected `tp` online and checks it against both
clamp endpoints can reallocate mid-run.

**`dist_base = 0` deserves special handling**: the waiting component becomes
all-or-nothing, worth `1000 * w_c` on a knife edge. On those tests, hitting both
SLO means with a safety margin dominates every other consideration.

## 6. Mechanism-level conclusions

### 6.1 Group `D PRE` and `D POST` as widely as possible

A `D PRE` spanning `r` remotes queues `r` `UP` transfers — **exactly the same
number as issuing `r` separate single-remote `D PRE`s**, because the rule is one
transfer per distinct remote in the group. But the wide group pays `S + dpre(m)`
once on `E` instead of `r` times. Cross-remote grouping is therefore **strictly
better on `E` and neutral on the link**. Same argument for `D POST`, whose grouping
does not affect `DOWN` traffic at all (`DOWN` transfers are per `D PROC` group).

The only cost of a wide group is *waiting* for its last member to become eligible.

### 6.2 But limit how many remotes a decode wave spans

Each distinct remote in a `D PRE` costs one extra transfer, and each transfer pays
`lat` on a **serial** link. Spanning all 8 remotes costs `8*lat` of `UP` time per
iteration — with `lat` up to 50 ms that is 400 ms of serialized link time per wave.
Choose `r` to minimize:

```text
max( (2S + dpre(m) + dpost(m)) / m ,        E
     r*lat/m + b ,                          UP  (= DOWN)
     (S + dproc(m/r)) / m )                 remote pool
```

High `lat` pushes toward fewer, fatter remotes; high `dproc` pushes toward more.

### 6.3 Chunked prefill exists to stop head-of-line blocking

Splitting `P PROC` never reduces total remote work — the pieces sum to
`pproc(L_in)` exactly — and **costs an extra `S` per piece**. Its only purpose is
preemption granularity: `pproc(L_in)` can be `10^4` ms, and while it runs, every
request pinned to that remote is frozen, inflating their TPOT gaps. Splitting into
`p` pieces caps the blocking at `pproc/num_layers + S` per piece.

```text
split when   pproc(L_in) / num_layers * (blocked decode requests on that remote)
             outweighs   (p-1) * S
```

With `num_layers = 1` the mechanic is disabled; with `num_layers = 64` we get fine
control. **This is the main TPOT lever on prefill-heavy tests.** Note pieces are
serialized only by our reaction to each piece's `TDN`, and since we respond at the
same timestamp as the frame, chaining pieces loses no wall-clock time.

### 6.4 Remote assignment is permanent — balance decode load, not prefill load

`P PRE` pins a request to a remote for its entire life, including all `L_out[i]`
decode iterations. But `L_out[i]` is **hidden until `FIN`**. So assignment must
balance on an estimate; a remote that accumulates many long requests becomes a
permanent hotspot. Balance by *current active request count* per remote, and
consider that a request that has already produced many tokens is more likely to
keep going.

### 6.5 Never let the system go fully idle

The stuck-state rule is a `0`-score trap and interacts badly with batching: waiting
to accumulate a bigger group is safe **only if some other event is already
guaranteed to arrive**. Since there is no end-of-arrivals signal, the invariant is:

> If no task is running on any computer, no transfer is in flight, and at least one
> unfinished request exists, we **must** assign at least one legal task in this
> response.

Implement this as an assertion in the response builder, not as a policy nicety.

## 7. Implementation architecture

```text
src/
  proto.hpp      frame parsing, task_spec emission, fast I/O
  table.hpp      task-time table + piecewise-linear lookup with clamping
  state.hpp      per-request lifecycle FSM, per-resource busy flags, link queues
  policy_*.hpp   interchangeable schedulers behind one interface
  sim/           offline interactor replica (drives policies without the judge)
  score/         exact scorer implementing Section "Scoring"
```

The offline **interactor replica is the highest-value artifact** after a correct
baseline. The problem is fully deterministic and the entire cost model is
published, so a local replica lets us sweep policies without submitting. Build it
to reproduce `data/public/example1.interactor.txt` byte-for-byte from the
participant stream — that is the acceptance test.

Performance budget: 15 s wall, up to `2·10^6` frames → **~7.5 µs per frame**.
Groups of size 1 over `Σ L_out = 2·10^5` tokens generate on the order of `10^6`
frames, so unbatched policies are also the slowest. Batching helps twice.

## 8. Roadmap

| Phase | Deliverable | Expected effect |
|---|---|---|
| 0 | Reactive protocol-correct scheduler: full prefill piece, groups of 1, act on every frame | Non-zero on every test; throughput component ≈ 0 |
| 1 | Offline interactor replica + exact scorer; Example 1 replays to 500.000 | Enables all measurement |
| 2 | Greedy maximal batching: one wide `D PRE` / per-remote `D PROC` / wide `D POST` per opportunity | The big throughput jump |
| 3 | Concurrency control at `N ≈ SLO2 · X`; admission control on prefill | Recovers the waiting component |
| 4 | Chunked prefill sized from `num_layers`, `pproc`, and blocked-request count | TPOT on prefill-heavy tests |
| 5 | Regime detection from `w_tp`/`w_c`/clamps; per-regime policy selection | Fits each test's actual scoring |
| 6 | Short-horizon lookahead using the exact cost model | Marginal gains at the top |

Phases 0–2 are where nearly all the score is. Do not start Phase 6 before the
replica in Phase 1 exists.

## 9. Hazards

| Hazard | Consequence | Mitigation |
|---|---|---|
| Stuck state while waiting to batch | test scores 0 | invariant in §6.5, asserted in the response builder |
| Assigning to a computer whose `TDN` has not arrived | 0 | busy flags cleared **only** on `TDN` |
| Re-issuing a step after `FIN` | 0 | `FIN` co-arrives with the final `D POST`'s `TDN`; purge in the same frame, before choosing |
| `XDN size` parsed as 32-bit | wrong state | `4096 * 10^6` overflows `int32`; use 64-bit |
| Printing a float | malformed output | our output is integers only, ever |
| Forgetting to flush | hang → TLE | flush after every response, including empty `0` |
| Blocking on EOF | TLE instead of the real verdict | on read failure, `exit(0)` immediately |
| Group exceeds `n <= K+1` assignments | 0 | at most one task per resource per response |
| Assuming an assignment can depend on another in the same response | 0 | all assignments in a response start at the same `t` |
| Tuning to preliminary tests | finals use a **separate frozen set** | prefer regime-adaptive policy over per-test constants |
