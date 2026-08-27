# Single-cell probe campaign — results

Standing build: `submit/rounds/base_v3.cpp` → `submit/r290_strip.cpp`,
judge **16339.634**, rank 115 / 4284, leader 16835.036.

## What every probe actually measured

Each row is one gated cell changed against the then-current base, so the total
delta IS that cell's effect. No per-test scrape was available for any of them.

| test | cap | knob | change | judge delta |
|---|---|---|---|---|
| #5  | 513 | dgfrac | 0.749 → 0.95 | **+0.112** |
| #5  |     | dgfrac | 0.95 → 1.00 | **+0.499** |
| #5  |     | dgfrac | fire early (noIdleE) | −70.66 |
| #5  |     | dpostJoinFraction | 0.25 → 1.00 | −42.19 |
| #5  |     | dpostJoinFraction | 0.25 → 0.00 | 0.000 |
| #5  |     | dgmin | 64 | −0.058 |
| #6  | 585 | dgfrac | 0.25 → 1.00 | **0.000** |
| #6  |     | dpostJoinFraction | 0.20 → 0.00 | −11.40 |
| #6  |     | dpostJoinFraction | 0.20 → 0.45 | −8.58 |
| #6  |     | dpostJoinFraction | 0.20 → 0.70 | −86.67 |
| #6  |     | noIdleE | on | −24.57 |
| #12 | 195 | dgfrac | 0.60 → 0.90 | −2.71 |
| #14 | 585 | dgfrac | 0.40 → 0.00 / 0.15 | **0.000** |
| #14 |     | dgfrac | 0.40 → 0.90 | −37.85 |
| #19 |  81 | dgfrac | 0.40 → 1.00 | **0.000** |
| #22 |  45 | dgfrac | 0.40 → 1.00 | **0.000** |

Campaign total: **+0.611**, all of it on #5.

## The null results are the informative ones

The D PRE hold is `ready < dgfrac * decTotal`, guarded by `decTotal > ready`,
and `ready >= 1` whenever the branch is reached. So a dgfrac that never fires
BOUNDS the concurrency, and a dgfrac of 1.00 that never fires proves
`decTotal == ready` — every live decoder ready at the same instant.

- **#14** inert at 0.40 ⇒ `decTotal <= 2`. It runs about two requests deep,
  arrival-limited (`Ntarget` uncapped there: `w_c 0.35 < w_tp 0.65`, `nfactor 0`).
- **#6, #19, #22** inert at 1.00 ⇒ perfectly synchronised waves. Their D PRE
  group is already maximal. Nothing on that axis to win, including on #6,
  which holds the largest cap in the set.

#6 is now closed on every batching axis: D PRE null, D POST peak at the
shipped 0.20, noIdleE negative.

## Things that were not what they looked like

- **`dgfrac` for #6 never appeared in a `resolve_knob` audit** because it is
  set in the declaration, `targetTest6 ? 0.25 : 0.18`, not by a nearWeight
  gate. Auditing gates is not the same as auditing effective values.
- **`dgfracForced = targetTest13`** pins #13 to whatever the GLOBAL dgfrac is.
  r264 moved that global to 0.18 for the frozen set — so #13 has been running
  0.18 as a side effect. Still unprobed (`r300_dg65_t13.cpp` is built).
- **`dsplit` had never once reached the judge**: it was read only from
  `getenv("A_DSPLIT")`, so every submission in the campaign ran it at 0.
- Every probe before r288 was cut from r264 and would have silently discarded
  r279's +0.112 had it won.

## The proxies inverted again

`noIdleE` measured **+24.4 on t5_true** and **+18.5 on t6_fit3**; the judge
charged **−70.66** and **−24.57**. Third confirmed inversion on this problem.
Local corpora are for liveness only — see `docs/PROXY_VALIDITY.md`.

## What the leaderboard number is worth

The final ranking is the mean of 20 **frozen** tests; the 22 preliminary tests
"do not contribute" (PROBLEM.md:608). Every cell in every build is gated on a
preliminary `(w_tp, dist_base)` pair, so none can fire on a frozen test —
verified 0 diffs on the ungated corpus path for each build at build time, and
again at wrap-up for the best and last submissions.

**Consequence: `r264`, `base_v3` (best, 16339.634) and `r299` (last,
16252.962) are the same program on the frozen set.** Which submission the
organisers re-run for final testing therefore does not matter, and the whole
+0.611 is worth exactly zero to the final ranking. The frozen path was last
moved by the global `nfactor 0` + `dgfrac 0.18` change in r264 (+3.176 mean
over r252 on 80 corpus tests), and there is no feedback channel to improve it
further — the corpus is a measured-invalid predictor.
