# Formal model

Source: [Codeforces 1885A](https://codeforces.com/problemset/problem/1885/A).

## Dimensions

- Users: `N`, 1–100.
- Cells: `K`, 1–10.
- TTIs: `T`, 1–1000; one TTI is 0.5 ms.
- RBGs per cell: `R`, 1–10; one RBG represents 5760 kHz.
- Frames: `J`, 1–5000.

For every TTI `t`, cell `k`, RBG `r`, and user `n`, the output supplies power
`p[t,k,r,n] >= 0`. Allocation `b` is exactly `p > 0`.

Hard constraints for every `(t,k)`:

- `sum(r,n,p) <= R` across the cell;
- `sum(n,p) <= 4` on each RBG.

Each frame has one user, size `TBS`, inclusive start TTI, and inclusive deadline.
Only bits transmitted inside its window count. The input guarantees at most one
active frame per user at a TTI.

## Evaluation

RBG SINR contains:

- initial channel quality multiplied by allocated power;
- exponential intra-cell interference from every other user sharing the RBG;
- cross-cell interference in the denominator from different users on the same RBG.

For a `(t,k,n)` allocation, the effective SINR is the geometric mean across all
RBGs assigned to that user. Its transmitted bits are:

```text
192 * assigned_RBG_count * log2(1 + effective_SINR)
```

A frame scores one if accumulated in-window bits are at least `TBS`. The test score
is lexicographic in effect:

```text
successful_frames - 1e-6 * total_power
```

Total submission score is the sum across tests. During the original contest, the
latest preliminary submission with a nonzero score was selected for hidden final
evaluation.

## Consequences

- Partial service to a frame that ultimately fails has no primary value.
- Allocating outside a frame window is legal but wastes power.
- Sharing an RBG creates intra-cell interference.
- Different users on the same RBG across cells create cross-cell interference.
- Serving the same user from multiple cells avoids the stated cross-user
  interference term, which motivates the single-user baseline.
- Power minimization matters only after the number of completed frames is fixed.

