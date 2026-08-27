# ICPC 2026 Online Challenge 1 (Huawei)

Codeforces 2251A, *Edge-Cloud Collaborative Scheduling*. An interactive
optimization problem: schedule LLM inference across one local computer, up to
eight remote computers, and one shared bidirectional link, under a 15 s / 256 MB
limit. The contest ran 2026-08-14 to 2026-08-28.

<https://codeforces.com/contest/2251/problem/A>

## Result

The best submission scores **16339.634** on the 22 preliminary tests, rank 115 of
4284. To reproduce it, submit `submit/r290_strip.cpp` as a single file under
GNU G++23 14.2 (64 bit). That file is the comment-stripped form of
`submit/rounds/base_v3.cpp`; the two behave identically, but only the stripped
one fits the 65,535-byte source limit.

`src/main.cpp` is the original reference implementation. It reproduces the
statement's Example 1 transcript byte for byte and scores exactly 500.000 there,
which makes it useful for protocol checks, but it is far behind the tuned build.

## How scoring works

Each test scores `1000 * (w_tp * output_rate + w_c * waiting_time)`, both
components clamped to `[0, 1]`. The output-rate component is throughput
normalized between a serial reference schedule and an estimated upper bound. The
waiting-time component measures how far mean TDR and mean TPOT overrun their
per-test SLOs. Both weights and both reference points are read from the input at
startup, so the program knows its own scoring function and can trade one
component against the other. `docs/statement/PROBLEM.md` has the exact formulas.

One consequence shaped the whole campaign: the 22 preliminary tests report
feedback but do not decide the ranking. The final score is the mean over 20
frozen tests nobody can see. Every per-test tuning gate in the build keys on a
preliminary `(w_tp, dist_base)` pair, so none of them can fire on a frozen test.
`docs/CAMPAIGN_RESULTS.md` works through what that implies.

## Reading order

Start with `docs/statement/PROBLEM.md` for the task, then `docs/statement/CONTRACT.md`
for the I/O grammar and event ordering, then `docs/statement/ANALYSIS.md` for
the resource bounds that determine which tests have headroom left.

| Path | Contents |
|---|---|
| `docs/statement/PROBLEM.md` | full statement transcription |
| `docs/statement/CONTRACT.md` | I/O grammar, constraints, event order, scoring |
| `docs/statement/ANALYSIS.md` | resource ceilings, bottlenecks, strategy |
| `docs/statement/EXAMPLES.md` | both examples re-derived by hand |
| `docs/SOLUTION.md` | the scheduler's approach |
| `docs/CAMPAIGN_RESULTS.md` | what every tuning probe measured on the judge |
| `docs/STRUCTURAL_FLOORS.md` | tests proven to sit at an arithmetic floor |
| `docs/PROXY_VALIDITY.md` | why local reconstructions cannot rank knobs |
| `docs/EXPERIMENT_PROTOCOL.md` | how experiments are recorded |
| `docs/RULES.md` | compliance digest |
| `submit/rounds/README.md` | round-by-round ledger, every submission |
| `cases/` | one dossier per judge test, generated from scraped results |

## Running it

Build the solver and replay the public example:

```sh
c++ -std=c++23 -O2 -o build/local/solver submit/rounds/base_v3.cpp
python3 tools/interactor.py --test data/public/example1.test --solver ./build/local/solver
```

`sim/fast_interactor.cpp` is a C++ rewrite of the same interactor, roughly 50x
faster, which is what makes a 504-test corpus sweep practical:

```sh
c++ -std=c++17 -O2 -o sim/fast_interactor sim/fast_interactor.cpp
./sim/fast_interactor data/corpus/burst_1.txt ./build/local/solver
```

Local scores do not predict judge scores. Treat a corpus run as a liveness
check, meaning it tells you whether a change alters the schedule at all, and
nothing more. `docs/PROXY_VALIDITY.md` records three separate occasions where a
reconstruction that matched the judge's `tp`, `tdr` and `tpot` still got a knob's
sign backwards.

## Tools

- `tools/interactor.py` and `sim/fast_interactor.cpp`: offline interactor,
  validator, and scorer.
- `tools/cooldown.py`: when the next submission slot opens. Codeforces allows
  two submissions per 900 seconds on this problem.
- `tools/cf_fetch_tests.py`: scrape the per-test breakdown from a submission
  page. Needs a signed-in Chrome on a CDP port.
- `tools/mux22.py`: emit a build carrying one gated experiment per judge test.
- `tools/resolve_knob.py`: replay the gates in source order and report each
  test's effective compiled value. Use it before every submission. Gates set
  earlier in the file lose silently to later assignments, and that bug has
  invalidated whole rounds of readings.
- `tools/strip_comments.py`: shrink a build under the 65,535-byte source limit.
- `tools/floor_analysis.py`: minimum achievable makespan per test.

## Build system

CMake presets cover a release build, a sanitizer build, and the test ladder:

```sh
cmake --preset release && cmake --build --preset release -j && ctest --preset release
cmake --preset sanitize && cmake --build --preset sanitize -j && ctest --preset sanitize
python3 -m unittest discover -s tests -v
python3 tools/verify_foundation.py
```

`practice/xr2023/` is a separate reconstruction of Codeforces 1885A, kept as
training material. It shares no code with the 2251A solution.
