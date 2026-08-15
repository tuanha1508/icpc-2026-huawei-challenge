# Planned 2026 solution architecture

This is an interface plan, not a guessed problem implementation.

```text
official input
    ↓
strict parser → immutable Instance
                    ↓
             literal Simulator/Validator ← candidate schedule
                    ↑                         ↑
          tiny exact oracle             Policy interface
                                              ↑
                       baseline → admission → batching/cache → local repair
```

## Required boundaries

- **Instance:** immutable source data, dimensions, units, precomputed legal
  candidates, and safe index functions.
- **State:** mutable resource availability, queues, request progress, cache/model
  residency, and event clock. Every mutation must have one owner.
- **Simulator:** the slow literal interpretation of the statement. It is the local
  source of truth and must not share optimized policy shortcuts.
- **Validator:** rejects the first hard-constraint violation with time, request, and
  resource context.
- **Policy:** observes only allowed state and proposes an action. Baselines and
  advanced policies use the same interface.
- **Delta evaluator:** computes the effect of one candidate action without replaying
  the full schedule. It must be differential-tested against the literal simulator.
- **Oracle:** exhaustive or mathematical solver for tiny restricted instances,
  providing upper bounds and counterexamples.
- **Serializer:** deterministic output with compact formatting and no debug text.

## Performance rules

- Precompute static feasibility and cost terms.
- Iterate active requests/resources, never maximum-size empty arrays in hot loops.
- Maintain incremental queue load, memory, capacity, and deadline statistics.
- Use integer/fixed-point arithmetic when the official formula permits it.
- Allocate memory once; avoid per-event heap allocation.
- Keep deterministic tie-breaking by stable IDs.
- Reserve at least 20–30% of the official runtime and memory limits for hidden-test
  variance unless measurements justify a larger margin.

## Verification ladder

1. Hand-worked examples.
2. Parser/serializer round trips.
3. Literal simulator invariants.
4. Tiny exhaustive oracle comparisons.
5. Random differential tests for every optimized delta.
6. Metamorphic tests: relabeling equivalent resources, adding unused capacity,
   scaling units where valid, and deterministic replay.
7. Sanitizers and maximum-dimension stress.
8. Compile and test the flattened submission artifact.

