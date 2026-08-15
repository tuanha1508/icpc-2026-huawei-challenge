# ICPC 2026 Online Summer Challenge — Working Memory

## Challenge

- Event: ICPC 2026 Online Summer Challenge powered by Huawei
- Problem: **A. Edge–Cloud Collaborative Scheduling**, <https://codeforces.com/contest/2251/problem/A>
- Topic: scheduling for an edge–cloud collaborative LLM inference system
- Objective: weighted sum of an output-rate component and a waiting-time component
- Start: August 14, 2026 at 11:00 UTC / 18:00 Vietnam time
- End: August 28, 2026 at 10:59 UTC / 17:59 Vietnam time
- Participant registration: completed

## Problem is OPEN — statement transcribed 2026-08-14

**Do not re-extract the PDF.** Everything is in `docs/statement/`:

- `PROBLEM.md` — full faithful statement transcription (start here)
- `CONTRACT.md` — formal I/O grammar, constraints, event order, scoring
- `ANALYSIS.md` — bounds, bottlenecks, and the strategy roadmap
- `EXAMPLES.md` — both examples re-derived by hand; Example 1 scores 500.000
- `figures/` — the five statement diagrams
- `data/public/example1.{interactor,participant}.txt` — replayable Test 1

Original PDF: `artifacts/originals/problem-A-codeforces-2026-08-14T2136.pdf`.

### The five facts that matter most

1. Interactive, non-adaptive, deterministic. 15 s / 256 MB. Not open to hacks.
2. One local computer `E` (serial, touched twice per group-iteration) + `K <= 8`
   remotes + one serial-FIFO `UP` link and one serial-FIFO `DOWN` link that run
   concurrently with each other. `E` and the links are the bottlenecks.
3. `tp_base` is the rate of a one-request-at-a-time reference schedule, so **a
   serial scheduler scores 0 on the throughput component by construction.**
   Batching and overlap are the entire scoring opportunity.
4. `TPOT ≈ N / X` (Little's law), so the TPOT target is a hard cap on decode
   concurrency: `N <= SLO2 * X`. Batch size is bought with latency.
5. All scoring parameters (`w_tp`, `w_c`, `SLO1`, `SLO2`, `tp_base`, `tp_UB`,
   `dist_base`) are **read from the input**, so the policy should branch on them
   at runtime. `dist_base = 0` makes the waiting component all-or-nothing.

### Solution status (2026-08-14): v2 ready to submit

**v1 judge result: 11772.334 / 22000 across the 22 preliminary tests, rank ~622
(leader 16164.872). All 22 returned OK** — no violations, no TLE. Recovering
per-test `w_tp` from the reported `norm_tp`/`norm_c`/points showed 7063 of the
10228 recoverable points are THROUGHPUT, and exposed a v1 design bug: the
concurrency cap engaged whenever `w_c > 0`, trading 0.99-weighted throughput for
0.01-weighted waiting on tests like #12. v2 seeds the cap only when
`w_c >= w_tp` and steers N on both excesses. That per-test weight recovery is
the highest-value diagnostic — rerun it after every submission.

### v1 notes

`src/main.cpp`, single file, GNU G++23. Details in `docs/SOLUTION.md`.
Example 1 replays byte-for-byte at 500.000; 0 violations in 85 local runs;
0.80 s / 1.98 MB against limits of 15 s / 256 MB.

Local tooling built: `tools/interactor.py` (replica + validator + scorer),
`tools/gen_test.py`, `tools/bounds.py` (ceiling check), `tools/sweep_policy.py`.

Two measured findings that are easy to get wrong:

- **Maximal batching is right even when the remotes bind.** Capping decode groups
  to stagger waves hurt (289 → 212), because `decode_proc` is sublinear and `S`
  is per-task, so splitting adds S-charges to the binding resource.
- **Prefill chunking is a trap by default.** Each extra piece adds an `S` straight
  onto TDR. It scored 0 on Example 1: TDR 30.0 → 31.0 missed `SLO1 = 30`, and
  `dist_base = 0` makes the waiting component all-or-nothing.

### Immediate next steps

1. Check the Codeforces announcements/clarifications tab (not yet done).
2. Confirm submission limit / cadence / which submission is final (not in the
   statement — see the open items in `CONTRACT.md`).
3. Improvement levers are listed at the end of `docs/SOLUTION.md`.

## Rules to remember

- The contest is for one registered individual.
- AI tools, including generative AI and AI-assisted coding tools, are explicitly
  permitted. The participant remains fully responsible for correctness,
  originality, licensing, and compliance.
- Do not collaborate or discuss the task with other human contestants or people
  other than designated challenge personnel.
- Internet research must use only publicly available information and must not use
  sources requiring authentication.
- Use only permitted information and tools under the official rules and any contest clarifications.
- The submission must be owned or properly licensed and comply with the problem specification.
- Track all third-party/open-source components and their licenses; be ready to
  provide an exhaustive list if requested.
- Keep challenge-provided non-public material confidential and do not publish it.
- Recheck Codeforces announcements and clarifications for schedule or rule changes.
- Official conditions and rules: https://docs.google.com/document/d/1y_U1fJpahNUthKYFg1o3E2n99lO1tm7cyjf7_NrGJSo/edit?tab=t.0
- Detailed operational digest: `docs/RULES.md`

## Initial workflow

1. Save the complete statement, attachments, starter code, and official clarifications here.
2. Translate the model into resources, operations, dependencies, timings, SLOs, and scoring.
3. Build an exact simulator, validator, and local scorer before optimizing.
4. Implement a simple valid baseline scheduler.
5. Generate difficult tests, measure bottlenecks, and improve iteratively.
6. Record submissions, scores, failures, and ideas in this file or an experiment log.

## Next session

When the problem opens, save the full statement and all public downloadable files,
then follow `docs/OPENING_CHECKLIST.md`. Recheck the current rules and
clarifications, establish the exact local simulator/validator/scorer, and freeze a
reproducible valid baseline before optimization.
