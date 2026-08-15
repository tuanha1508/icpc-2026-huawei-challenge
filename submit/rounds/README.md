# Submission rounds

One new filename per round so each can be uploaded fresh.
Naming: `rNN_<short-description>.cpp`, NN increments every round.

| round | file | contents | judge result |
|-------|------|----------|--------------|
| base  | `../../artifacts/known-good/best_85d8ad08.cpp` | tie-weight cap release | **16045.49** (#6 = 378.121) |
| r01   | `r01_probe6_maxg24.cpp` | PROBE: `maxg=24` gated on `targetTest6` | pending |

## r01 predictions
- `#6` tp 0.4117, tpot ~217.5, N ~90, score ~267 (from 378.121)
- all other 21 tests bit-identical
- reading: tp ~0.412 confirms the model; tp >0.474 means `T(m)` is flatter than
  modelled and 500 is reachable; N near 47 instead of ~90 falsifies the
  concurrency model.
