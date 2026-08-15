# Mock-contest results

Run date: **2026-08-11**. These results use deterministic synthetic instances from
`make_suite.py`, not the unavailable historical final tests.

## Suites

- Tuning: 12 fixed-shape cases across mixed, burst, tight-window, and high-
  interference profiles.
- Held-out: 12 unseen seeds with four different dimension shapes and all profiles.
- Stress: four large cases, producing 17–29 MB per verbose historical output before
  compact serialization.

All candidates used minimal-power trimming. Scores are summed exactly as the
historical statement specifies.

| Policy | Tuning | Held-out | Stress |
|---|---:|---:|---:|
| admission-srf | **149.997200** | **194.995382** | **434.946939** |
| completion | 139.996775 | 186.994475 | 415.939276 |
| srf | 129.996075 | 164.993157 | 226.940158 |
| admission-slack | 107.996499 | 149.993880 | — |
| edf | 80.995630 | 115.992643 | — |
| fifo | 37.995344 | 51.991963 | — |
| naïve slack | -0.004920 | 4.991512 | — |

The ordering generalized from tuning to held-out and stress data. Admission-aware
shortest-remaining-frame was therefore selected as the mock default.

## Ablations

Power trimming versus fixed power 1 for admission-SRF:

| Suite | Completions, trimmed/fixed | Score improvement |
|---|---:|---:|
| Tuning | 150 / 150 | +0.001148266956 |
| Held-out | 195 / 195 | +0.001924340188 |

The tie-break optimization improved power without changing the primary completion
count.

## Tiny exact-oracle study

An exhaustive oracle enumerated the baseline family's complete action space on 16
unseen tiny instances (three users, seven TTIs, one cell, one RBG, four profiles).
Admission-SRF matched the exact maximum completion count on all 16 cases. The
largest search visited only 93 nodes after safe finishability pruning. The complete
record is in `experiments/xr2023_oracle_study.csv`.

This is evidence that the implementation and admission behavior are coherent on
small cases, not a claim of global optimality on the unrestricted historical
problem.

The naïve slack policy failed because negative slack made already-hopeless large
frames appear most urgent. The versioned `hopeless-trap.in` case reproduces this:
naïve slack completes zero frames, while admission-SRF completes one.

## Performance engineering

- Capacity prefix sums replaced repeated future-window capacity computation.
- Selection scans at most one active frame per user, not all frames.
- The exact general SINR evaluator was removed from the single-user solver's hot
  path; a closed single-user delta is used instead.
- Compact buffered output writes `0` rather than `0.000000000000`. On the largest
  measured stress shape, output fell from about 29 MB to about 4.1 MB.
- On that shape, the local admission-SRF algorithm added roughly 0.35 CPU seconds
  beyond reject-all parsing/serialization; textual input parsing dominated. Wall
  time varied with concurrent machine load and is not treated as a stable benchmark.

## Frozen mock artifact

- Policy: admission-SRF with power trimming.
- Package:
  `artifacts/submissions/20260811T002614Z-xr2023-admission-srf-oracle-hardened/`.
- One-file SHA-256:
  `7438389747a98f8b1a23dbaca3578c96f54ec59f815feb8f02aba63e2640cdd3`
- Official sample reconstruction: 2 frames, power `0.486047665544`, score
  `1.9999995139523346`.
- The artifact compiled independently and passed the official sample plus all three
  versioned adversarial cases.

## Transferable conclusions

1. Completion-only objectives require admission control; progress is not value.
2. A plausible urgency formula can be directionally wrong on impossible work.
3. Separate primary completions from secondary power/cost optimization.
4. Optimize deltas and active sets before introducing sophisticated search.
5. Parsing, serialization, checking, and artifact selection are part of the contest
   system, not administrative details.
6. Choose on tuning data, confirm on held-out data, and stress runtime separately.
