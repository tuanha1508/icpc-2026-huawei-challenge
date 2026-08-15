# Two-week contest runbook

## Before start

- Keep the repository, toolchain, disk space, clock, and network healthy.
- Confirm Codeforces and ICPC account/email linkage.
- Recheck rules and the AI clarification.
- Do not rely on a single local copy; maintain recoverable repository backups while
  respecting challenge confidentiality.

## Opening day

Follow `OPENING_CHECKLIST.md`. The exit condition for day zero is not a high score;
it is an exact local model, a validator, and one accepted deterministic baseline.

## Days 1–2: executable truth

- Resolve every formula, boundary, event-order, and final-submission ambiguity.
- Reproduce official cases and clarification changes.
- Implement tiny exhaustive instances and adversarial generators.
- Submit a simple valid baseline early and archive it.

## Days 3–6: baseline ladder

- Measure bottlenecks by instance class.
- Add admission, finishability, deadline, placement, batching, and cache logic one
  change at a time where the statement supports them.
- Keep a frozen reliable submission at all times.

## Days 7–10: robust optimization

- Add incremental delta evaluation and bounded local repair.
- Tune only on the tuning split.
- Run ablations and held-out validation daily.
- Investigate public-score changes that disagree with local predictions before
  making more submissions.

## Days 11–12: hardening

- Stop large architectural rewrites unless a confirmed model error demands one.
- Run sanitizers, maximum dimensions, adversarial cases, repeated seeds, and the
  flattened artifact.
- Remove brittle per-test logic and unsafe parameters.

## Final 48 hours

- Re-read which submission will be used for final testing.
- Preserve a high-margin fallback and a higher-scoring candidate separately.
- Check submission-rate and judging queues; do not depend on a last-minute upload.
- Repackage, compile, hash, validate, submit, and record the exact artifact.
- Verify the online verdict and update `experiments/submissions.csv`.

