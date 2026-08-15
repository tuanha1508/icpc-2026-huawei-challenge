# Worked examples — independent hand verification

Both official examples were re-derived from the cost model in
[`PROBLEM.md`](PROBLEM.md) without reading the expected timestamps first. **Every
timestamp and duration reproduces exactly.** The model below is therefore
confirmed, not assumed.

Machine-readable transcripts:

- `data/public/example1.interactor.txt` — the complete interactor stream (Test 1).
- `data/public/example1.participant.txt` — the matching participant responses.

Example 2 is a mid-run excerpt in the statement with no startup configuration, so
it is documented here but is not a replayable fixture.

## Shared cost model used in both examples

```text
S = 1 ms, latency_in_ms = 2, bandwidth_gbps = 1, bytes_per_token = 125000

busy interval of a task assigned at t  = [t, t + S + dur]
transfer_time(len) = 2 + 8 * (len * 125000) / 1e6 = 2 + len ms
    len = 1  ->  3 ms      (one decode member)
    len = 4  ->  6 ms      (prefill of L_in = 4)
```

## Example 1 — one request, end to end

Configuration: `K = 1`, `num_layers = 4`, request 0 has `L_in[0] = 4` and (revealed
only at `FIN`) `L_out[0] = 1`. Relevant durations: prefill `3, 10, 2`; decode
`1, 4, 1`. The scheduler uses one full input-stage piece.

| # | t (ms) | Interactor event | Response | Derivation |
|---|---|---|---|---|
| 1 | 0.000 | `ARR 0 4` | `E P PRE 0 0` | request arrives, local computer idle |
| 2 | 4.000 | `TDN E P PRE 0 0` dur 3 | `0` | `0 + S + 3 = 4`; input-stage `UP` queued at 4 |
| 3 | 10.000 | `XDN UP 0 500000 PRE 1 0` | `C0 P PROC 0 4 0 0` | `4 + transfer(4) = 4 + 6 = 10` |
| 4 | 21.000 | `TDN C0 P PROC 0 4 0 0` dur 10 | `0` | `10 + S + (4-0)/4 * 10 = 21`; last piece queues `DOWN` |
| 5 | 27.000 | `XDN DOWN 0 500000 PRE 1 0` | `E P POST 0 0` | `21 + 6 = 27` |
| 6 | 30.000 | `TDN E P POST 0 0` dur 2 | `E D PRE -1 1 0` | `27 + S + 2 = 30`; **TDR = 30 − 0 = 30** |
| 7 | 32.000 | `TDN E D PRE -1 1 0` dur 1 | `0` | `30 + S + 1 = 32`; one `UP`, len 1, queued |
| 8 | 35.000 | `XDN UP 0 125000 DEC 1 0` | `C0 D PROC 0 1 0` | `32 + 3 = 35` |
| 9 | 40.000 | `TDN C0 D PROC 0 1 0` dur 4 | `0` | `35 + S + 4 = 40`; `DOWN` len 1 queued |
| 10 | 43.000 | `XDN DOWN 0 125000 DEC 1 0` | `E D POST -1 1 0` | `40 + 3 = 43` |
| 11 | 45.000 | `TDN E D POST -1 1 0` dur 1, `FIN 0` | `0` | `43 + S + 1 = 45`; **token produced at 45** |
| — | — | `END` | exit | |

### Score of Example 1 = 500.000

```text
Sigma L_out = 1
total_elapsed = 45 - 0 = 45 ms
tp = 1 / 45 = 0.0222222222...

tp_base = 0.022222222   (the printed 9-decimal truncation of 1/45)
tp_UB   = 0.0625
output_rate_component = clamp(0.02222222222; 0.022222222, 0.0625) ~= 5.5e-9 ~= 0

tdr  = 30, SLO1 = 30  ->  excess_tdr  = max(0, (30-30)/30) = 0
L_out[0] = 1 -> no gaps -> tpot = 0
                        ->  excess_tpot = max(0, (0-15)/15) = 0
dist = sqrt(0 + 0) = 0
dist_base = 0 and dist = 0  ->  waiting_time_component = 1

Score = 1000 * (0.5 * 0 + 0.5 * 1) = 500.000
```

**This is the single most useful fact in the statement.** `tp_base` for this test
equals the rate of exactly the schedule shown — a one-request-at-a-time serial
walk. So a serial scheduler scores **0 on the output-rate component by
construction**, on every test. Half the score of Test 1 is free (the waiting-time
half, because the trivial schedule already meets both SLOs); the other half is
only reachable through genuine overlap. See
[`ANALYSIS.md`](ANALYSIS.md#the-baseline-is-defined-to-score-zero-on-throughput).

## Example 2 — grouping requests from two remote computers

Requests 0 and 1 are already assigned to `C0` and `C1` respectively and both become
ready for their first output step at `16.500`. This excerpt uses a different
task-time table from Example 1: `decode_pre(2) = 1.5`, `decode_proc(1) = 4`,
`decode_post(2) = 1.5`.

| # | t (ms) | Interactor event | Response | Derivation |
|---|---|---|---|---|
| 1 | 16.500 | `TDN E P POST 1 1` dur 1.25 | `E D PRE -1 2 0 1` | both ready; one group spans C0 and C1 |
| 2 | 19.000 | `TDN E D PRE -1 2 0 1` dur 1.5 | `0` | `16.5 + S + 1.5 = 19`; **two** `UP`s queued at 19, in increasing remote index (C0 then C1) |
| 3 | 22.000 | `XDN UP 0 125000 DEC 1 0` | `C0 D PROC 0 1 0` | `UP` link serial: `19 + 3 = 22` |
| 4 | 25.000 | `XDN UP 1 125000 DEC 1 1` | `C1 D PROC 1 1 1` | second `UP` waits for the link: `22 + 3 = 25` |
| 5 | 27.000 | `TDN C0 D PROC 0 1 0` dur 4 | `0` | `22 + S + 4 = 27`; `DOWN` queued at 27 |
| 6 | 30.000 | `TDN C1 D PROC 1 1 1` dur 4, `XDN DOWN 0 …` | `0` | C1: `25 + S + 4 = 30`; DOWN0: `27 + 3 = 30`. **Identical internal times coalesce into one frame.** DOWN1 queued at 30 |
| 7 | 33.000 | `XDN DOWN 1 125000 DEC 1 1` | `E D POST -1 2 0 1` | `DOWN` link free at 30: `30 + 3 = 33` |
| 8 | 35.500 | `TDN E D POST -1 2 0 1` dur 1.5, `FIN 0`, `FIN 1` | `0` | `33 + S + 1.5 = 35.5`; two tokens |
| — | — | `END` | exit | |

### What Example 2 pins down

1. **Each link direction is strictly serial FIFO.** The two `UP`s from one `D PRE`
   do not overlap: 19→22 then 22→25. Latency is paid per transfer, so spanning
   `r` remote computers in one `D PRE` costs `r` separate `UP` transfers and
   `r * latency` of serialized link time.
2. **The two directions do overlap.** `DOWN` is busy 27→30 while `UP` sits idle.
3. **Simultaneous events coalesce into one frame** (`t = 30` carries a `TDN` and an
   `XDN`), and the frame timestamp is the shared internal event time.
4. **`D PRE` queues one `UP` per distinct remote, in increasing remote index** —
   the ordering rule is deterministic and worth exploiting: the remote whose
   members you want to start first should have the lower index.
5. **`D POST` may combine members delivered by different `D PROC` groups and
   different `DOWN` transfers**, as long as each member's own `DOWN` `XDN` has
   arrived.
6. The local computer's decode tasks are **sublinear in group size** here:
   `decode_pre(1) = 1.0` but `decode_pre(2) = 1.5`, i.e. 0.75/member instead of
   1.0/member — and that is before amortizing `S = 1` across two members.

## Regression-test obligations

- [ ] Replay `example1.interactor.txt` against the solver; assert the response
      stream matches `example1.participant.txt` exactly.
- [ ] Local simulator, fed Example 1's configuration and the participant response
      stream, must emit the interactor stream byte-for-byte (all 11 frames).
- [ ] Local scorer must return exactly `500.000` for Example 1.
- [ ] Simulator must reproduce the Example 2 excerpt from `t = 16.5` given its
      stated table, including the coalesced frame at `t = 30`.
