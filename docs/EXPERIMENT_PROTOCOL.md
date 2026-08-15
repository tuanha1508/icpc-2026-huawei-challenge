# Experiment protocol

The goal is to make every score explainable and reproducible.

## Non-negotiable controls

- One change per experiment unless the experiment explicitly tests an interaction.
- Fixed seeds and deterministic tie-breaking by default.
- Separate tuning and held-out generated sets.
- Freeze the split with `tools/split_cases.py`; keep byte-identical cases in the
  same partition and record the manifest's corpus hash.
- Keep the exact local scorer version and test-set hash with every result.
- Report aggregate score plus per-instance score, SLO failures, runtime, peak
  memory, and relevant utilization/bottleneck metrics.
- Re-run promising changes; reject gains smaller than measurement noise.
- Compare against a frozen baseline and perform an ablation before merging.

## Suggested experiment ID

Use `YYYYMMDD-HHMM-short-name`, for example
`20260814-2140-edf-admission`.

## Run ledger

`experiments/runs.csv` contains infrastructure timings. After the scorer exists,
extend it with fields such as:

```text
experiment_id,git_commit,solver,parameters,test_set,test_hash,seed,score,
valid,slo_met,slo_total,wall_ms,peak_kib,notes
```

## Submission ledger

For every submission, record:

- timestamp and Codeforces submission ID;
- git commit and SHA-256 of the submitted file;
- compiler/language and all compiled-in parameters;
- local public, synthetic, adversarial, and held-out scores;
- public judge score, verdict, runtime, and memory;
- whether it is eligible to become the final selected submission;
- what changed, the expected effect, and the observed effect.

Never rely on the online platform as the only copy of a submitted artifact.

Use `tools/package_submission.py` to flatten project-local C++ headers into one
source file and create a non-overwriting manifest containing the source hash, Git
commit, dirty-worktree flag, and parameter values. Compile and validate the
flattened `submission.cpp`, not only the development executable.

## Parameter sweeps

Use `tools/sweep.py` with a JSON grid once the solver and scorer interfaces exist.
It expands parameter keys in sorted order, runs candidates in parallel, preserves
each output, and writes per-instance results in deterministic candidate/case order.

- Tune only on the designated tuning set.
- Choose the score aggregation formula only after copying it exactly from the
  statement; do not assume arithmetic mean or sum.
- Re-evaluate finalists on held-out and adversarial sets.
- Prefer a stable plateau to a sharp optimum.
- Freeze chosen parameters in source and record them in the submission manifest.

## Decision rule

Promote a candidate only when it:

1. remains valid on all tests;
2. improves the intended metric across more than a narrow visible subset;
3. does not consume unsafe runtime/memory margin;
4. has a plausible causal explanation; and
5. survives the held-out and adversarial suites.
