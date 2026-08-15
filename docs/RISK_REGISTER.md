# Risk register

| Risk | Early signal | Mitigation |
|---|---|---|
| Wrong interpretation of formula/event order | Official sample or clarification disagrees | Literal simulator, minimal clarification, regression test |
| Invalid output | Zero score or first checker rejection | Central validator; validate flattened artifact before upload |
| Visible-test overfitting | Gain disappears on generated held-out set | Fixed tuning/held-out split; simple policies; ablations |
| Hopeless work consumes resources | High utilization but few completed requests | Finishability/admission estimates; adversarial deadline tests |
| Runtime or memory failure | Stress case near limit | Active sets, precomputation, deltas, compact I/O, safety margin |
| Numerical mismatch | Boundary cases flip success | Exact formula audit; high precision; tolerance clarification |
| Wrong final artifact | Best local version not final-tested | Immutable package, hash, submission ledger, early final upload |
| Nondeterminism | Same build produces different scores | Fixed seeds and stable tie-breaks; replay tests |
| Rule/clarification changes | Announcement or statement revision | Daily checks; timestamped clarification log and regression updates |
| Third-party IP issue | Unknown snippet/dependency origin | Provenance/license ledger; independently implement methods |
| Data loss | Device/worktree failure | Recoverable encrypted backup consistent with confidentiality |
| Low local disk space | Less than 20 GiB free or failed builds/material downloads | Run `tools/preflight.py`; free space before opening day without deleting contest artifacts |
