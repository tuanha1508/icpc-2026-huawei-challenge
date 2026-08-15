# Problem-opening checklist

Run this in order when the challenge opens. Accuracy during the first hour is worth
more than a premature heuristic.

Before opening the statement, run `python3 tools/preflight.py` and resolve every
error. Treat disk and dirty-worktree warnings as explicit decisions.

## First 15 minutes: preserve authoritative material

- Confirm the official start/end time and time zone on the contest page.
- Re-read current rules, AI clarification, announcements, and all clarifications.
- Download the English statement, every attachment, starter, sample, checker,
  generator, compiler note, and submission-format document from public sources.
- Save untouched originals and record their URLs and SHA-256 hashes.
- Record compiler versions, time/memory limits, submission limits, judge cadence,
  public/final test selection, scoreboard freeze, and which submission is final.

Suggested layout:

```text
docs/statement/        statement and amendments
data/public/           official public instances
third_party/           licensed official starter/checker code
artifacts/originals/   immutable downloaded archives and hashes
```

Create the first inventory before unpacking or modifying anything:

```sh
python3 tools/inventory_materials.py \
  --root data/public \
  --output artifacts/originals/materials.json
```

## Minutes 15–35: formalize the contract

- Copy `docs/CONTRACT_TEMPLATE.md` to `docs/statement/CONTRACT.md` and fill it from
  the current official statement revision.
- Transcribe every input field with type, unit, range, and indexing convention.
- Transcribe every output field and all hard feasibility constraints.
- Write the event/time ordering: arrivals, scheduling decisions, compute,
  transmission, completion, expiration, and tie behavior.
- Write the exact objective and determine whether components are lexicographic,
  multiplicative, normalized, capped, or test-weighted.
- List all rounding, floating-point, overflow, and inclusive/exclusive boundaries.
- Work every official example by hand.
- Put ambiguities in `notes/clarifications.md`; do not silently assume.

## Minutes 35–60: executable truth

- Implement parser and serializer tests.
- Build a slow, literal simulator independent from the optimized solver.
- Build a validator that reports the first violated constraint with context.
- Reproduce all official example scores exactly.
- Add tiny exhaustive tests where brute force can enumerate every valid schedule.
- Commit/tag this state before implementing optimization.

## First baseline

- Implement the simplest valid deterministic policy.
- Keep feasibility checks centralized and shared by every later policy.
- Use fixed seeds and deterministic tie-breaks.
- Measure runtime and memory as well as score.
- Submit early enough to validate the entire pipeline, then archive the exact source
  and result in `experiments/submissions.csv`.

## Clarification template

```text
Subject: [Problem A] Ambiguity in <section/formula>

The statement says <short quotation or formula>. For the case <minimal example>,
interpretation X gives <result>, while interpretation Y gives <result>.
Which interpretation does the judge use?
```
