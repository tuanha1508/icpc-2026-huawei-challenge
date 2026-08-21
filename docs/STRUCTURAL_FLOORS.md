# Structural floors — which headroom is real and which is arithmetic fiction

Established 2026-08-21. Method: `tools/floor_analysis.py`.

## The bound

```
makespan = last_token - first_arrival
         >= (last_arrival - first_arrival) + T_last
T_last    = P PRE -> UP -> P PROC -> DOWN -> P POST, then L_out decode steps
```
Every component of `T_last` is mandatory and serial for a lone request, so this
is a true lower bound. A second bound comes from resource capacity (E work,
remote work / K, link work); the floor is the max of the two.

## Result: three tests are AT the floor, exactly

| test | computed floor | our makespan | verdict |
|---|---|---|---|
| #3  | 226,918.0 | 226,918.0 | **at floor, to the digit** |
| #14 | 448,445.4 | 448,445.4 | **at floor, to the digit** |
| #12 | 88,354,483.5 | 88,354,508.8 | at floor (25 ms of 88.4 M) |

An exact match on a 9-digit number is not coincidence: it confirms both the
reconstruction and the conclusion.

Worked example, #3: `tdr = 1360.0` decomposes as
`P PRE 55 + UP 276 + P PROC 698 + DOWN 276 + P POST 55`, with arrivals 2272
apart so no two requests ever coexist. Nothing is removable.

Worked example, #14: `tdr = 197.489 = 25+42+63.489+42+25` and
`tpot = 184.378 = 54.126+11+54.126+11+54.126`. Arrivals are 2245 ms apart and a
request lives 1672 ms, so the system is idle 25% of the time by construction.

Worked example, #12: arrival span is 87,204,447 of the 88,354,484 floor
(98.7%). `tp_UB` would need a makespan of 80.1 M -- **less than the arrival
span alone**. Unreachable by arithmetic, not by scheduling.

## Consequence

`docs/JUDGE_PARAMS.md` ranked #14 "the single best target, +551 points" and
listed #12 at "+189 for 11% throughput". Both are unreachable. Combined with
#3, that is **1,278 points of nominal headroom that never existed.**

`tp_UB` is an upper BOUND supplied in the input, not an achievable target.
Where the arrival span dominates the makespan, `norm_tp` is capped far below 1
no matter what the scheduler does.

## Also closed this round

- **Admission cap** (r254/r255). #9/#18/#21 never exceed 16 requests in flight,
  so caps of 16/32/64 are all exact no-ops there; #15 binds and gets *worse*
  (cap 32 = -9.4, cap 16 = -63.9, monotone). Their TDR is 10-242x SLO1 not
  because of queueing but because SLO1 sits below the critical path.
- **dpost on #9/#10/#15/#18**: values 0.25 and 0.40 give byte-identical judge
  scores. With single-token requests `futureDpost` is 0, so the join condition
  never binds. Structurally inert.
- **Oracle over all 56 harvested configs**: +0.27 remaining. Everything ever
  measured is already gated.

## Standing build: r264 (2026-08-21)

r264 = 16339.023 on the leaderboard, EXACTLY equal to r252's best, with a
frozen-path mean of 739.029 against r252's 735.853 (+3.176 on 80 ungated
corpus tests). Strictly better: same feedback score, better ranking score.
Contents: global nfactor 0 + global dgfrac 0.18, with nfactor gated back to
1.0 on #15 and #10.

## Axes closed by measurement, 2026-08-21

| axis | verdict |
|---|---|
| admission cap (dpostMin/Ntarget) | #9/#18/#21 never exceed 16 in flight; #15 monotone worse |
| dpost fraction | curves mapped on #4 #6 #13 #17; all at peak |
| dgfrac | curves mapped; #6 bracketed 0.05..0.60, peak 0.25 |
| absolute D POST minimum | new control, +96.1 on corpus, loses on all 4 judge tests |
| admission order 'F' | loses on all 9 tests where it binds, inert on 8 |
| rporder / pfair / chunk / dsplit | move 0 of 16 gate-keyed probes -- DEAD |
| prefillBoost | dead outside `!busyE && useMarginal` |
| global knobs (19 swept) | only nfactor 0 and dgfrac 0.18 positive |

#10 is inert under seven settings across three mechanisms (dgfrac 0.25/0.40/
0.60, dpost 0.25/0.40, dpostMin 4/16) -- all exactly 684.481.
