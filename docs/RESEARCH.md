# Pre-contest research

Last updated: **2026-08-11**. Everything below is public pre-contest research.
Claims about the 2026 task are hypotheses until the official statement is released.

## What previous Huawei/ICPC challenges teach us

The relevant historical contests are long-form, one-problem optimization contests,
usually with standard I/O, strict time/memory limits, provisional public evaluation,
and hidden final evaluation.

| Contest | Domain | Reusable lesson |
|---|---|---|
| [2020 Cloud Scheduling](https://codeforces.com/blog/entry/85241) | Multi-objective cloud scheduling | Build custom datasets; test crossover/hybrid heuristics; explicitly study objective trade-offs. |
| [2021 Communication Routing](https://codeforces.com/blog/entry/94906) | Large inter-satellite routing with resource limits | Separate feasibility from optimization; preprocess topology; make candidate evaluation scale-aware. |
| [2022 Problem 1](https://codeforces.com/blog/entry/105097) | Graph partitioning for fast routing | Reduce the instance through meaningful domains/coarsening before expensive routing decisions. |
| [2022 Problem 2](https://codeforces.com/blog/entry/105097) | Online topology-aware VM placement | Preserve scarce multidimensional capacity for unknown future requests; treat hierarchy and constraints explicitly. |
| [2023 Spring](https://codeforces.com/blog/entry/112838) | Shared buffer management for database tenants | Stateful online policies need isolation, fairness, recency/frequency signals, and robust eviction behavior. |
| [2023 XR scheduling](https://codeforces.com/problemset/problem/1885/A) | Radio-resource scheduling with frame deadlines | Partial work may have zero value; prioritize finishability and deadline slack, not merely raw utilization. |
| [2024 Summation](https://codeforces.com/contest/1953) | Accuracy/speed trade-off in mixed-precision summation | Reproduce the checker exactly, keep large runtime margin, and remember final scoring may use the last positive-score submission. |
| [2025 OXC](https://codeforces.com/contest/2177/problem/A) | Dynamic routing and reconfiguration | Precompute feasible mappings, track congestion incrementally, reuse stable state, and price reconfiguration explicitly. |

Huawei's published guidance for the VM-placement challenge recommends hierarchical
top-down selection, reserving room for future group growth, avoiding per-test
overfitting, and preferring simple general algorithms with clear intuition and few
parameters. That is a strong prior for this project as well.

### Historical failure modes to expect

- A locally attractive choice fragments a resource needed by later requests.
- Weighted sums accidentally violate a lexicographic scoring priority.
- Work spent on a request earns nothing because the request misses its deadline.
- The visible set rewards an overfit parameter or case distinction that fails final
  tests.
- Floating-point, rounding, indexing, event-order, or tie-breaking differences make
  the local scorer disagree with the judge.
- A solution near the time/memory limit loses heavily on hidden tests.
- The "best public score" is not the artifact selected for final judging.

## Edge–cloud LLM inference: likely model components

Do not implement these until confirmed. Extract the released statement into this
model checklist:

- Requests: arrival time, prompt length, expected/known output length, priority,
  model/adapter, and one or more latency SLOs.
- Latency: end-to-end deadline, time to first token (TTFT), time per output token
  (TPOT), inter-token latency, or a task-specific substitute.
- Compute: heterogeneous edge/cloud workers, phase-dependent processing rates,
  batch-size effects, parallelism, and context-length effects.
- Memory: model weights, adapter residency, activation/KV-cache growth, capacity,
  fragmentation, and eviction/recomputation cost.
- Network: edge/cloud latency and bandwidth, transferred activations/KV state,
  contention, and whether communication overlaps computation.
- Decisions: admission/rejection, placement/offload, partition point, batching,
  ordering/preemption, migration, cache policy, and resource allocation.
- Objective: accepted/completed requests, generated tokens, throughput/goodput,
  SLO attainment, utilization, cost/energy, or a lexicographic combination.

## Research-backed algorithmic toolbox

These are candidates, not a proposed solution:

1. **Admission by finishability.** Estimate earliest completion under current
   queues and reject or deprioritize requests that cannot meet a hard SLO. Use
   deadline slack and marginal resource cost rather than FIFO alone.
2. **Deadline scheduling.** Compare earliest-deadline-first, least-slack-time,
   shortest-remaining-processing-time, and density/value-per-resource policies.
   Protect urgent decode work from long prefills if the SLO distinguishes phases.
3. **Continuous/token-budget batching.** Fill spare capacity without waiting for a
   whole batch. Bucket compatible requests by phase, length, model, or adapter.
4. **Chunked prefill.** [Sarathi-Serve](https://www.usenix.org/conference/osdi24/presentation/agrawal)
   splits long prefills into chunks to prevent decode stalls and improve the
   throughput/latency trade-off.
5. **Prefill/decode separation.** [DistServe](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin)
   assigns compute-heavy prefill and memory-bandwidth-heavy decode to different
   resources and places them with network transfer cost in mind.
6. **Dynamic migration/load balancing.** [Llumnix](https://www.usenix.org/conference/osdi24/presentation/sun-biao)
   shows that rescheduling live requests can reduce queue imbalance, fragmentation,
   and tail latency when migration cost is controlled.
7. **KV-cache-aware routing.** Reuse cached prefixes/state and avoid migrations whose
   transfer or recomputation cost exceeds their queueing benefit. [Mooncake](https://www.usenix.org/conference/fast25/presentation/qin)
   makes cache state a first-class scheduling resource.
8. **Edge/cloud placement and model partition.** [EdgeShard](https://arxiv.org/abs/2405.14371)
   jointly selects devices and model partitions using dynamic programming;
   [PerLLM](https://arxiv.org/abs/2405.14636) treats personalized deadlines,
   heterogeneous resources, and edge/cloud allocation jointly.
9. **Robust online choice.** Maintain multiple simple policies or parameter sets and
   select using observable instance features. Do not use test IDs or brittle
   hand-authored exceptions.
10. **Local improvement.** Start from a valid greedy schedule, then use bounded
    swaps, reinsertions, batch regrouping, or large-neighborhood repair while an
    explicit time budget remains.

## Baseline ladder after release

Implement and freeze each level before moving upward:

1. Valid no-op/reject-all output if permitted.
2. Simple valid FIFO placement on one resource.
3. Greedy earliest-finish placement across all resources.
4. Deadline/slack-aware admission and ordering.
5. Batch- and cache-aware placement.
6. Edge/cloud transfer-aware phase or model partitioning.
7. Bounded local search/repacking.
8. Instance-class policy selection and carefully validated parameter tuning.

Every step needs an ablation against the prior frozen version across public,
synthetic, adversarial, and held-out generated tests.

## High-value tests to generate

- All requests arrive together; arrivals just before/after resource release.
- Deadlines exactly equal predicted completion and differ by one time unit.
- Very short prompts with long decode, and very long prompts with short decode.
- Edge is faster only until communication is included; cloud is faster only for
  certain batch sizes.
- Bandwidth bottleneck, high round-trip latency, zero/huge transfer sizes.
- KV memory exactly full; one-token overflow; fragmentation despite enough totals.
- Alternating models/adapters that cause cache thrashing.
- Heavy-tailed request lengths and bursts followed by idle periods.
- Multiple equal candidates to expose unstable tie-breaking.
- Near-overflow integers and rounding boundaries.
- Maximum dimensions, maximum number of events, and worst-case candidate counts.

## Source policy

Use primary problem pages, organizer posts, papers, and official project
repositories where possible. Record URL, access date, license, and what was reused.
Research may inspire an independently implemented method; do not copy unlicensed
contest code.

