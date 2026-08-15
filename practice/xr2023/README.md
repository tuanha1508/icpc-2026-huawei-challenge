# 2023 XR scheduling mock challenge

An isolated reconstruction of Codeforces 1885A,
[Deterministic Scheduling for Extended Reality over 5G and Beyond](https://codeforces.com/problemset/problem/1885/A).

This is training infrastructure only. It must not be copied blindly into the 2026
solution because the new task's model and I/O are not yet known.

## Included

- A strict parser for the historical instance format.
- A local feasibility checker and scorer implementing formulas (5)–(7).
- Seven deterministic completion-oriented baseline policies.
- Optional minimal-power trimming for a selected request.
- A deterministic synthetic/adversarial instance generator.
- A bounded exact completion oracle for tiny instances under the baseline family's
  one-user-per-TTI/full-resource action restriction.
- Official-sample and invariant tests.
- Parameter-sweep configuration.

## Build and run

```sh
cmake --preset release
cmake --build --preset release -j

./build/release/xr_generator --seed 1 --users 8 --cells 2 \
  --ttis 30 --rbgs 3 --frames 30 > /tmp/xr.in

./build/release/xr_solver --policy slack < /tmp/xr.in > /tmp/xr.out
./build/release/xr_scorer /tmp/xr.in /tmp/xr.out --details

# Tiny instances only: emits an exact restricted-family schedule and diagnostics.
./build/release/xr_oracle --max-nodes 2000000 < /tmp/xr.in > /tmp/oracle.out
```

Supported policies:

- `idle`: valid reject-all/no-allocation baseline.
- `fifo`: lowest frame ID.
- `edf`: earliest deadline first.
- `srf`: smallest remaining frame size first.
- `slack`: least estimated service slack first.
- `admission-srf`: estimated-finishable frames first, then smallest remaining size.
- `admission-slack`: estimated-finishable frames first, then least future-capacity
  slack.
- `completion`: frames completable now first, then least slack.

Each policy assigns all cells/RBGs in a TTI to one user. This intentionally simple
restriction avoids interference and gives a trustworthy baseline, not a competitive
upper bound. By default, the solver binary-searches for the minimum uniform power
that completes the chosen frame during the current TTI when possible. Pass
`--no-trim` for fixed power 1.

The no-argument mock submission defaults to `admission-srf`, selected only after it
won on both tuning and held-out generated suites.

The oracle is exact for completion count within the same action family used by all
mock policies: at most one selected user receives every cell/RBG at unit power in a
TTI. It is not an upper bound for unrestricted multi-user/interference-aware
allocations and deliberately refuses large instances.

Create the historical one-file mock submission with:

```sh
python3 tools/package_submission.py \
  --source practice/xr2023/submission_entry.cpp \
  --include-dir practice/xr2023/include \
  --label xr2023-admission-srf \
  --parameters '{"policy":"admission-srf","trim_power":true}'
```

## Known reconstruction boundary

The public statement specifies the formulas and power limits but does not state the
checker's numerical comparison tolerance. This local checker uses `1e-7` only for
power-sum feasibility; scheduling is defined by strict `p > 0`, as in the statement.
This uncertainty is documented rather than inferred.
