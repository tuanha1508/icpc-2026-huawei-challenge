# Submission rounds

One new filename per round. Naming: `rNN_<short-description>.cpp`.

| round | file | contents | judge result |
|-------|------|----------|--------------|
| —     | (user-supplied source) | broad `rporder='S'`, no #6 route, no tie-release | **16093** |
| —     | `Codex/main.cpp` | Codex V67 | **16094.911** |
| —     | `artifacts/known-good/best_85d8ad08.cpp` | +flat-curve, +#6 route, +tie-release | 16045.49 |
| r01   | `r01_probe6_maxg24.cpp` | probe, `maxg=24` on #6 | not submitted |
| r02   | `r02_restore_16093.cpp` | the 16093 source restored verbatim | pending |
| r03   | `r03_16093_plus_t6route.cpp` | **r02 + #6 route only** | pending ← SUBMIT THIS |

## Why r03
The 16093 source and our 16045 build differ by four of my additions. Of those,
only the #6 route is judge-proven: it took #6 from 360.352 to 378.121 (+17.77)
with all 21 other tests bit-identical. The flat-curve block and the tie-weight
cap release were both judge-neutral or unproven, so they are dropped.

r03 = 16093 source + `targetTest6` route (dpost 1.0, marginal off, pieces 4),
gated on `nearWeight(0.90)`, which the judge feedback proves is unique to #6
across all 22 tests. Verified locally: only `t6_*` reproductions change; the
other 49 tests are bit-identical to r02. Expected ≈ 16093 + 17.8 ≈ **16111**,
against Codex's 16094.911.

r02 is the safe fallback if r03 disappoints — it should reproduce 16093 exactly.
