# ICPC 2026 Online Summer Challenge — Huawei

Pre-contest foundation for the individual optimization challenge on edge–cloud
collaborative LLM inference scheduling.

The problem is expected to open on **2026-08-14 at 11:00 UTC**
(18:00 in Vietnam) and end on **2026-08-28 at 10:59 UTC**
(17:59 in Vietnam). The official website and Codeforces clock remain authoritative.

## Current status — problem is OPEN

**Problem A. Edge–Cloud Collaborative Scheduling** — interactive scheduling over
one edge computer, `K <= 8` cloud computers, and a shared bidirectional link.
15 s / 256 MB, not open to hacks.
<https://codeforces.com/contest/2251/problem/A>

The statement is transcribed and analyzed. **Read the markdown, not the PDF:**

| Document | Contents |
|---|---|
| [`docs/statement/PROBLEM.md`](docs/statement/PROBLEM.md) | full faithful statement transcription |
| [`docs/statement/CONTRACT.md`](docs/statement/CONTRACT.md) | formal I/O grammar, constraints, event order, scoring |
| [`docs/statement/ANALYSIS.md`](docs/statement/ANALYSIS.md) | resource bounds, bottlenecks, strategy roadmap |
| [`docs/statement/EXAMPLES.md`](docs/statement/EXAMPLES.md) | both examples re-derived by hand; Example 1 scores 500.000 |
| `data/public/example1.*.txt` | replayable Test 1 transcripts |

## Solution status — ready to submit

**Submit `submit/r290_strip.cpp`** as a single file, language
**GNU G++23 14.2 (64 bit)**. It is the comment-stripped form of
`submit/rounds/base_v3.cpp` and scores **16339.634** on the 22 preliminary
tests. `src/main.cpp` is the original reference implementation and is now well
behind it. See [`docs/SOLUTION.md`](docs/SOLUTION.md) for the approach and
[`docs/CAMPAIGN_RESULTS.md`](docs/CAMPAIGN_RESULTS.md) for what each tuning
probe measured on the judge.

- Official Example 1 reproduces the published transcript **byte-for-byte** and
  scores exactly **500.000**.
- **0 protocol violations in 85 local runs.**
- **0.80 s** / **1.98 MB** on the largest stream (limits: 15 s / 256 MB).

```sh
c++ -std=c++23 -O2 -o build/local/solver src/main.cpp
python3 tools/interactor.py --test data/public/example1.test --solver ./build/local/solver
```

Local tooling:

- `tools/interactor.py` — offline interactor replica, strict validator, exact scorer.
- `tools/gen_test.py` — test generator with a statement-faithful reference schedule.
- `tools/bounds.py` — resource lower bounds; says whether a test has headroom left.
- `tools/sweep_policy.py` — parallel policy-knob sweep ranked by mean score.

Remaining open items:

1. Resolved: the submission limit is **2 per 900 seconds**, and which submission
   is judged last does not matter — every per-test cell is gated on a preliminary
   `(w_tp, dist_base)` pair, so none can fire on the 20 frozen tests that decide
   the final ranking. See [`docs/CAMPAIGN_RESULTS.md`](docs/CAMPAIGN_RESULTS.md).
2. Improvement levers are listed at the end of `docs/SOLUTION.md`.
3. Record every experiment and submission according to
   [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md).

## Build

The provisional implementation language is C++20. Change this to the exact
Codeforces compiler mode if the problem specifies something different.

```sh
cmake --preset release
cmake --build --preset release -j
ctest --preset release
./build/release/solver < input.txt > output.txt
```

During development, run the same tests with undefined-behavior and address
sanitizers enabled:

```sh
cmake --preset sanitize
cmake --build --preset sanitize -j
ctest --preset sanitize
```

Run the infrastructure tests:

```sh
python3 -m unittest discover -s tests -v
```

Or run the complete release, sanitizer, Python, syntax, and whitespace verification
ladder with one command:

```sh
python3 tools/verify_foundation.py
```

Inventory downloaded public materials immediately after saving them:

```sh
python3 tools/inventory_materials.py \
  --root data/public \
  --output artifacts/originals/materials.json
```

Create a stable tuning/held-out assignment once generated cases exist. Files with
identical content are kept in the same split to avoid leakage:

```sh
python3 tools/split_cases.py \
  --inputs data/generated \
  --output artifacts/corpora/generated-v1.json \
  --seed generated-v1 --heldout-percent 25 --recursive
```

Run repeated timing measurements over a directory of inputs:

```sh
python3 tools/benchmark.py \
  --solver ./build/release/solver \
  --inputs data/public \
  --outputs artifacts/outputs \
  --runs 3 \
  --timeout 10 \
  --log experiments/runs.csv
```

The benchmark records wall time, exit status, output size, and output SHA-256.
Once the official scorer exists, its score should be added to the experiment log.

Run a parallel parameter grid after adapting `configs/sweep.example.json` to the
released solver and scorer interfaces:

```sh
python3 tools/sweep.py \
  --config configs/sweep.example.json \
  --inputs data/public \
  --outputs artifacts/sweeps/example \
  --log artifacts/sweeps/example.csv \
  --jobs 4 --timeout 10
```

Rank only after selecting the official aggregation semantics explicitly:

```sh
python3 tools/rank_sweep.py \
  --log artifacts/sweeps/example.csv \
  --aggregate sum --direction maximize
```

Freeze a single-file submission and provenance manifest:

```sh
python3 tools/package_submission.py \
  --source src/main.cpp \
  --include-dir include \
  --label baseline-v1 \
  --parameters '{"seed":0}'
```

## Repository map

- `docs/statement/`: transcribed statement, contract, analysis, examples, figures.
- `docs/RULES.md`: durable rule and compliance digest.
- `docs/RESEARCH.md`: prior-challenge and LLM-serving research.
- `docs/OPENING_CHECKLIST.md`: time-critical launch workflow.
- `docs/EXPERIMENT_PROTOCOL.md`: reproducible optimization procedure.
- `docs/ARCHITECTURE.md`: implementation boundaries and verification ladder.
- `docs/CONTEST_RUNBOOK.md`: opening-to-final-submission operating plan.
- `docs/RISK_REGISTER.md`: known failure modes and mitigations.
- `docs/PROVENANCE.md`: dependency, source, and material-handling ledger.
- `docs/CONTRACT_TEMPLATE.md`: fill-in statement/model contract for opening day.
- `include/foundation.hpp`: deterministic RNG and time-budget utilities.
- `tools/benchmark.py`: repeatable local runner.
- `tools/sweep.py`: deterministic parallel parameter-grid runner.
- `tools/rank_sweep.py`: explicit, validity-aware sweep aggregation and ranking.
- `tools/package_submission.py`: single-file source snapshot and hash manifest.
- `tools/inventory_materials.py`: sorted size and SHA-256 manifest for public inputs.
- `tools/verify_foundation.py`: one-command release and sanitizer verification.
- `tools/preflight.py`: toolchain, clock, disk-space, and Git readiness check.
- `tools/split_cases.py`: deterministic, duplicate-safe corpus partition manifest.
- `experiments/`: run and submission ledgers.
- `notes/`: clarifications, hypotheses, and decisions.
- `practice/xr2023/`: completed historical scheduling mock contest.
