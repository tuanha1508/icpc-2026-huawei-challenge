# Released-problem contract

Copy this file to `docs/statement/CONTRACT.md` when the problem opens. Fill every
field from an official public source before implementing an optimization policy.
Use `UNKNOWN` rather than silently choosing an interpretation.

## Source revision

| Item | Value |
|---|---|
| Statement URL and revision time | UNKNOWN |
| Download/material manifest | UNKNOWN |
| Last announcement check | UNKNOWN |
| Compiler/language | UNKNOWN |
| Time limit / memory limit | UNKNOWN |
| Submission limit and cadence | UNKNOWN |
| Preliminary/final selection rule | UNKNOWN |

## Input grammar

| Field | Type | Range | Unit | Indexing | Meaning |
|---|---|---|---|---|---|
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

State whether there are multiple tests, how arrays are ordered, whether values fit
32-bit integers, and the maximum total input size.

## Output grammar

| Field | Type/precision | Count/order | Hard validity rule |
|---|---|---|---|
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

Record whether extra tokens, missing lines, `-0`, exponential notation, NaN/Inf,
or out-of-window actions are accepted.

## State and resources

| Entity/resource | Immutable fields | Mutable state | Capacity/invariant |
|---|---|---|---|
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

## Event order

For each time step, list the exact order of arrivals, decisions, transfer, compute,
completion, cache/memory changes, SLO checks, expiration, and output accounting.
Specify which interval endpoints are inclusive.

```text
time t begins
  1. UNKNOWN
  2. UNKNOWN
time t ends
```

## Feasibility constraints

Number every hard constraint and translate it into both a mathematical statement
and a validator assertion. Include overflow bounds and ownership/exclusivity rules.

| ID | Official rule/formula | Executable assertion | Boundary tests |
|---|---|---|---|
| C-01 | UNKNOWN | UNKNOWN | UNKNOWN |

## Objective and final aggregation

Write the formula exactly. Mark lexicographic priorities, normalization, weights,
caps, rounding, per-test aggregation, invalid-output score, and tie-breaking.

```text
primary objective: UNKNOWN
secondary objective: UNKNOWN
per-test score: UNKNOWN
submission score: UNKNOWN
```

## Numerical semantics

| Operation | Required precision/rounding | Known judge tolerance | Regression case |
|---|---|---|---|
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

## Worked examples

Recalculate every official example independently. Record intermediate state and
the exact expected score, then make each example an automated regression test.

## Unresolved questions

Move every ambiguity to `notes/clarifications.md` with a minimal counterexample.
No unresolved question may be hidden inside policy code.

## Model sign-off gate

- [ ] Input/output counts and indexing are tested.
- [ ] Literal simulator and validator are independent from optimized deltas.
- [ ] Official examples reproduce exactly.
- [ ] Tiny oracle covers a meaningful restricted instance family.
- [ ] Random differential and boundary tests pass.
- [ ] Objective aggregation and final-submission selection are confirmed.
