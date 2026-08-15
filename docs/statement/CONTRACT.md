# Released-problem contract — Problem A, Edge–Cloud Collaborative Scheduling

Filled from the official statement captured 2026-08-14 21:36 UTC+7. Every entry is
sourced from the statement text in [`PROBLEM.md`](PROBLEM.md) or confirmed by hand
derivation in [`EXAMPLES.md`](EXAMPLES.md). Fields marked `UNKNOWN` are genuinely
not stated and must not be silently assumed.

## Source revision

| Item | Value |
|---|---|
| Statement URL | <https://codeforces.com/contest/2251/problem/A> |
| Capture time | 2026-08-14 21:36 UTC+7 (server time 21:32 UTC+7) |
| Original artifact | `artifacts/originals/problem-A-codeforces-2026-08-14T2136.pdf`, SHA-256 `fc5f927c6b617ffe02de8db5770e0b28cbc85b2b5520ad976303afa81eab7a8c` |
| Last announcement check | 2026-08-14 21:36 UTC+7 (statement page only; **announcements/clarifications tab not yet checked**) |
| Compiler/language | GNU G++23 14.2 (64 bit) shown in the submit box |
| Time limit / memory limit | 15 s per test / 256 MB |
| Submission limit and cadence | UNKNOWN — not in the statement; check contest rules page |
| Preliminary/final selection rule | Test 1 = public Example 1; tests 2–22 = hidden preliminary, **feedback only, excluded from ranking**; finals = 20 separate frozen tests; final score = arithmetic mean of the 20, ranked before rounding, displayed to 3 decimals |
| Hacks | Not open to hacks |
| Which submission is final | UNKNOWN — check contest rules page |

## Input grammar

Interactive. Three phases: startup (2 lines) → task-time table (`N + 1` lines) →
repeated frames. All reals are printed with 9 decimal places; fields are separated
by single spaces.

### Phase 1 — startup, line 1 (system parameters)

| Field | Type | Range | Unit | Meaning |
|---|---|---|---|---|
| `K` | int | `[1, 8]` | count | number of remote computers, ids `0 … K-1` |
| `S` | real | `[1, 10]` | ms | schedule cost added to **every** task |
| `latency_in_ms` | real | `[0.001, 50]` | ms | per-transfer fixed latency, strictly `> 0` |
| `bandwidth_gbps` | real | `[0.001, 100]` | Gb/s | link bandwidth, one direction at a time |
| `bytes_per_token` | int | `[1, 10^6]` | bytes | complete data size of one token; **do not scale it** |
| `num_layers` | int | `[1, 64]` | count | input-stage part range is `[0, num_layers)` |

### Phase 1 — startup, line 2 (scoring parameters)

| Field | Type | Range | Unit | Meaning |
|---|---|---|---|---|
| `SLO1` | real | `[0.001, 10^9]` | ms | target **mean** TDR |
| `SLO2` | real | `[0.001, 10^9]` | ms | target **mean** TPOT |
| `tp_UB` | real | `[10^-9, 10^9]`, `> tp_base` | tokens/ms | rate scoring 1.0 |
| `tp_base` | real | `[0, 10^9]` | tokens/ms | rate scoring 0.0; from a one-request-at-a-time reference schedule |
| `dist_base` | real | `[0, 10^9]` | — | `dist` scoring 0.0; `0` makes the waiting component binary |
| `w_tp` | real | `>= 0`, `w_tp + w_c = 1` | — | output-rate weight |
| `w_c` | real | `>= 0` | — | waiting-time weight |

### Phase 2 — task-time table

Line: `N` (int, `[2, 4096]`). Then `N` rows of 7 values:

| Field | Type | Meaning |
|---|---|---|
| `batch_size` | int, `[1, 4096]`, **distinct**, **unordered across rows** | key: `L_in` for the prefill columns, member count for the decode columns |
| `prefill_pre` | real, `[0.001, 10^4]` or `-1` | `P PRE` duration |
| `prefill_proc` | real | full-range `P PROC` duration (a piece scales by `(le-ls)/num_layers`) |
| `prefill_post` | real | `P POST` duration |
| `decode_pre` | real | `D PRE` duration |
| `decode_proc` | real | `D PROC` duration |
| `decode_post` | real | `D POST` duration |

`-1` means missing. Every column has at least one non-missing entry. Lookup per
column: sort available rows by `batch_size`; exact hit → that value; between two →
linear interpolation; below the smallest → the smallest's value; **above the
largest → the largest's value (constant)**. Every resulting legal duration is
strictly positive.

### Phase 3 — event frames

```text
<t>            one real, 9 decimals, frame timestamp
<e>            one int, number of event lines
<e event lines>
```

| Event line | Fields |
|---|---|
| `ARR <rid> <L_in>` | int, int. Arrival time is the frame's `t`. `L_out` is hidden. |
| `TDN <server> <task_spec> <dur>` | `task_spec` echoed canonically; `dur` excludes `S`, 9 decimals |
| `XDN <UP\|DOWN> <remote> <size> <PRE\|DEC> <m> <rid...>` | `size` in bytes = `len * bytes_per_token` |
| `FIN <rid>` | always co-arrives with the final `D POST`'s `TDN` |

`END` appears as a single line in place of the next frame's timestamp line.

**Multiple tests:** no. Each test is a separate process run. Max `2·10^6` frames
per test. `R` is never announced; there is no end-of-arrivals signal.

## Output grammar

One response per frame, flushed.

| Field | Type/precision | Count/order | Hard validity rule |
|---|---|---|---|
| `n` | int | exactly one per frame | `0 <= n <= K + 1` |
| assignment | `<server> <task_spec>` | exactly `n` of them | server currently free; at most one per resource per response |

Accepted input syntax for our integers: ordinary signed decimal, optional leading
`+`, leading zeros accepted. Whitespace between tokens is arbitrary (the examples
use one assignment per line). Echoed integers come back canonical.

| Task shape | Server | Notes |
|---|---|---|
| `P PRE <remote> <rid>` | `E` | `remote` in `[0, K)`; fixes the assignment |
| `P PROC <ls> <le> <remote> <rid>` | `C<remote>` | `remote` = the request's fixed remote |
| `P POST <remote> <rid>` | `E` | `remote` = the request's fixed remote (consistency check only) |
| `D PRE -1 <m> <rid...>` | `E` | literal `-1`; may span remotes |
| `D PROC <remote> <m> <rid...>` | `C<remote>` | all members fixed to `remote` |
| `D POST -1 <m> <rid...>` | `E` | literal `-1`; may span remotes |

Request-id order within a group has **no** semantic effect, but it is preserved on
echo and determines the id order inside derived `XDN` lines.

Not stated, therefore treat as forbidden: extra tokens after the `n` assignments,
`NaN`/`Inf`, exponential notation for our integers. **`-1` in `D PRE`/`D POST` is a
mandatory literal marker, not a sentinel; the interactor never sends `-1` as a
failure response.**

## State and resources

| Entity | Immutable fields | Mutable state | Capacity / invariant |
|---|---|---|---|
| local computer `E` | — | busy/free | exactly 1 task at a time; hosts `P PRE`, `P POST`, `D PRE`, `D POST` |
| remote `Ck`, `k in [0,K)` | index `k` | busy/free | exactly 1 task at a time; hosts `P PROC` pieces, `D PROC` |
| `UP` link | — | FIFO queue, one in flight | serial; concurrent with `DOWN` |
| `DOWN` link | — | FIFO queue, one in flight | serial; concurrent with `UP` |
| request `i` | `arrival`, `L_in[i]`, assigned remote (fixed at `P PRE`) | lifecycle stage, iteration counter, next prefill piece `ls` | `L_out[i]` hidden until `FIN`; never in two tasks at once |

Requests move strictly: `ARR → P PRE → UP → P PROC pieces → DOWN → P POST →
(D PRE → UP → D PROC → DOWN → D POST) × L_out[i] → FIN`.

## Event order

The interactor is event-driven, not tick-driven. Per frame:

```text
frame at internal time t begins
  1. all events with internal time exactly t are collected into this frame
     (arrivals, task completions TDN, transfer completions XDN, FIN)
  2. the frame is printed: t, e, then the e event lines (line order carries
     NO scheduling priority)
  3. we read the WHOLE frame and update state:
       TDN -> its server becomes free; its task's completion effect fires
              (P PRE / last P PROC piece / D PRE / D PROC enqueue transfers)
       XDN -> the carried data is available at the destination
       FIN -> the request is finished and is illegal from now on
  4. we print n and n assignments; ALL of them start at exactly t, and none may
     depend on another assignment in the same response
frame at time t ends
```

Interval convention: a task assigned at `t` occupies `[t, t + S + dur]` and its
`TDN` fires at `t + S + dur`. A transfer entering an idle link at `t` completes at
`t + latency + 8·len·bytes_per_token/(bandwidth_gbps·10^6)`; otherwise it starts
when the link's previous transfer completes. Part ranges are `[ls, le)`: `ls`
inclusive, `le` exclusive.

Deterministic queue-entry order for transfers enqueued at the same instant:

1. within one `D PRE`'s completion, by increasing remote index;
2. otherwise by interactor event order;
3. tasks started together and finishing together use our assignment-line order.

Printed timestamps are nondecreasing; internal times of consecutive frames are
strictly increasing (only exactly-equal internal times coalesce).

## Feasibility constraints

| ID | Official rule | Executable assertion | Boundary tests |
|---|---|---|---|
| C-01 | at most one task per computer | `!busy[server]` before assigning; and no two assignments in one response share a server | assign to `E` twice in one response; assign to a server whose `TDN` has not arrived |
| C-02 | `0 <= n <= K + 1` | `n <= K + 1` | `n = K + 2` |
| C-03 | predecessors delivered | per-shape predicate below | issue `P PROC` before the prefill `UP` `XDN` |
| C-04 | request not in flight, not finished | `stage[rid]` matches the shape and `!inflight[rid]` and `!fin[rid]` | reuse a rid in two groups of one response |
| C-05 | remote consistency | `P PRE`: `0 <= remote < K`; `P PROC`/`P POST`/`D PROC` member: `remote == assigned[rid]` | `P PRE` with `remote = K`; `D PROC` with a foreign member |
| C-06 | piece legality | `0 <= ls < le <= num_layers`, `ls == next_ls[rid]`, first `ls = 0`, last `le = num_layers` | `ls == le`; `le = num_layers + 1`; a gap; descending |
| C-07 | group legality | `m >= 1`, ids pairwise distinct | `m = 0`; duplicate id |
| C-08 | parseability | fixed command words copied exactly | lowercase `p pre`; missing `-1` |
| C-09 | no stuck state | if no task is running, no transfer is in flight, and unfinished requests exist, we **must** assign at least one legal task | idle everything while one ready request remains |
| C-10 | limits | 15 s wall, 256 MB, `<= 2·10^6` frames | worst case `Σ L_out = 2·10^5` with groups of size 1 |
| C-11 | EOF handling | on read failure or EOF, `exit(0)` immediately; never block, never crash | truncated stream |

Predecessor predicates (C-03):

```text
P PRE   <rid>            : ARR[rid] delivered
P PROC  piece            : first piece -> prefill UP XDN[rid] delivered
                           later piece -> previous piece's TDN delivered
P POST  <rid>            : prefill DOWN XDN[rid] delivered
D PRE   {rid...}         : for each member, its previous final-step TDN
                           (P POST for iteration 1, else previous D POST)
                           delivered, and !fin[rid]
D PROC  r, {rid...}      : for each member, the decode UP XDN carrying THAT
                           member's current-iteration data delivered
                           (members may come from different D PRE groups)
D POST  {rid...}         : for each member, the decode DOWN XDN carrying THAT
                           member's current-iteration result delivered
                           (members may come from different D PROC groups)
```

Overflow: all times are doubles up to `10^12` ms; `size` in bytes reaches
`4096 · 10^6 = 4.096·10^9`, which **overflows signed 32-bit** — parse `XDN` sizes
as 64-bit.

## Objective and final aggregation

```text
tp   = (Sigma_i L_out[i]) / (last_token_time - first_arrival_time)
tdr  = mean_i (P POST completion time of i - arrival time of i)
tpot = (sum over all i of (last_token_i - first_token_i))
       / (sum over all i of (L_out[i] - 1))          -- pooled gaps; 0 if no gaps

excess_tdr  = max(0, (tdr  - SLO1) / SLO1)
excess_tpot = max(0, (tpot - SLO2) / SLO2)
dist        = sqrt(excess_tdr^2 + excess_tpot^2)

clamp(x; base, target) = max(0, min(1, (x - base) / (target - base)))

throughput component = clamp(tp; tp_base, tp_UB)
waiting component    = dist_base > 0 ? max(0, 1 - dist/dist_base)
                                     : (dist == 0 ? 1 : 0)

per-test score    = 1000 * (w_tp * throughput_component + w_c * waiting_component)
submission score  = arithmetic mean over the 20 frozen final tests
invalid-output    = 0 for that test only; no partial credit; other tests unaffected
tie-breaking      = ranked on the unrounded mean; displayed to 3 decimals
```

Not lexicographic, not multiplicative: a plain weighted sum of two independently
clamped `[0, 1]` components. There is no per-test weighting beyond `w_tp`/`w_c`,
which are **read from the input** and therefore available to the policy at runtime.

## Numerical semantics

| Operation | Required precision | Judge tolerance | Regression case |
|---|---|---|---|
| reading times/durations | `double` (9 decimals printed) | n/a — we echo nothing numeric | `strtod` on `0.022222222` |
| our output | integers only; **we never print a real** | exact | ensure no float ever reaches stdout |
| forward simulation for planning | `double`, piecewise-linear lookup + transfer formula | statement explicitly blesses plain doubles | Example 1 replay must match to 1e-9 |
| `XDN size` | 64-bit int | exact | `4096 * 10^6` |

Our output contains no floating-point values at all, so judge float tolerance is
irrelevant to correctness; doubles matter only for our own planning.

## Worked examples

Both re-derived independently — see [`EXAMPLES.md`](EXAMPLES.md). Example 1
reproduces exactly and scores **500.000** (throughput component ≈ 0, waiting
component = 1). Example 2's excerpt reproduces exactly from `t = 16.5`.

## Unresolved questions

Tracked in `notes/clarifications.md`. Open items at transcription time:

1. Submission limit, cadence, and which submission counts as final — not in the
   statement; must be read off the contest rules page.
2. Whether the announcements/clarifications tab already contains amendments — not
   yet checked at capture time.

Neither blocks implementation of the simulator, validator, or baseline.

## Model sign-off gate

- [x] Input/output grammar transcribed with types, ranges, and units.
- [x] Official examples re-derived by hand and reproduce exactly.
- [ ] Input/output counts and indexing are tested in code.
- [ ] Literal simulator and validator are independent from the optimized solver.
- [ ] Example 1 reproduces exactly as an automated regression test (score 500.000).
- [ ] Tiny oracle covers a meaningful restricted instance family.
- [ ] Random differential and boundary tests pass.
- [x] Objective aggregation and final-submission selection are confirmed
      (mean of 20 frozen tests; preliminaries excluded).
