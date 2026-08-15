#!/usr/bin/env python3
"""Offline replica of the Problem A interactor, plus validator and scorer.

The problem is fully deterministic and the cost model is published in full, so a
local replica lets us measure a policy without spending a submission. This file
is deliberately literal: it follows docs/statement/CONTRACT.md sentence by
sentence rather than being clever.

Test file format (see tools/gen_test.py):

    K S latency_in_ms bandwidth_gbps bytes_per_token num_layers
    SLO1 SLO2 tp_UB tp_base dist_base w_tp w_c
    N
    <N rows of 7 values>
    R
    <R lines: arrival_time L_in L_out>

Usage:
    python3 tools/interactor.py --test t.txt --solver ./build/release/solver
    python3 tools/interactor.py --test t.txt --solver ... --dump-stream out.txt
"""

from __future__ import annotations

import argparse
import heapq
import math
import subprocess
import sys
from bisect import bisect_left
from dataclasses import dataclass, field


class ProtocolError(Exception):
    """Raised on any participant rule violation. Scores the test 0."""


def fmt(x: float) -> str:
    return f"{x:.9f}"


# --------------------------------------------------------------------- curves


class Curve:
    """One task-time column with the statement's clamped piecewise-linear rule."""

    def __init__(self) -> None:
        self.xs: list[int] = []
        self.ys: list[float] = []

    def add(self, bs: int, v: float) -> None:
        self.xs.append(bs)
        self.ys.append(v)

    def finalize(self) -> None:
        order = sorted(range(len(self.xs)), key=lambda i: self.xs[i])
        self.xs = [self.xs[i] for i in order]
        self.ys = [self.ys[i] for i in order]

    def at(self, x: float) -> float:
        if not self.xs:
            raise ProtocolError("task-time column has no listed entry")
        if x <= self.xs[0]:
            return self.ys[0]
        if x >= self.xs[-1]:
            return self.ys[-1]
        i = bisect_left(self.xs, x)
        if self.xs[i] == x:
            return self.ys[i]
        x0, y0 = self.xs[i - 1], self.ys[i - 1]
        x1, y1 = self.xs[i], self.ys[i]
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


# ---------------------------------------------------------------- token reader


class Tokens:
    """Whitespace tokenizer over a subprocess pipe."""

    def __init__(self, stream) -> None:
        self.s = stream
        self.buf = b""
        self.pos = 0

    def next(self) -> str:
        while True:
            while self.pos < len(self.buf) and self.buf[self.pos : self.pos + 1].isspace():
                self.pos += 1
            if self.pos < len(self.buf):
                start = self.pos
                while self.pos < len(self.buf) and not self.buf[self.pos : self.pos + 1].isspace():
                    self.pos += 1
                if self.pos < len(self.buf):
                    return self.buf[start : self.pos].decode()
                self.buf = self.buf[start:]
                self.pos = 0
            chunk = self.s.readline()
            if not chunk:
                if self.buf[self.pos :].strip():
                    tokv = self.buf[self.pos :].strip().decode()
                    self.buf, self.pos = b"", 0
                    return tokv
                raise ProtocolError("solver closed its output stream early")
            self.buf = self.buf[self.pos :] + chunk
            self.pos = 0

    def int(self) -> int:
        t = self.next()
        try:
            return int(t, 10)
        except ValueError as exc:
            raise ProtocolError(f"expected an integer, got {t!r}") from exc


# ------------------------------------------------------------------- requests


# Lifecycle stages, mirroring docs/statement/CONTRACT.md.
ARRIVED, PRE_RUN, PRE_UP, PROC_RDY, PROC_RUN, PROC_DOWN = range(6)
POST_RDY, POST_RUN, DEC_RDY, DPRE_RUN, DEC_UP = range(6, 11)
DPROC_RDY, DPROC_RUN, DEC_DOWN, DPOST_RDY, DPOST_RUN, DONE = range(11, 17)


@dataclass
class Req:
    rid: int
    arrival: float
    lin: int
    lout: int
    stage: int = ARRIVED
    remote: int = -1
    next_ls: int = 0
    iters: int = 0
    tdr_done: float = -1.0
    tokens: list[float] = field(default_factory=list)


# ----------------------------------------------------------------- interactor


class Interactor:
    def __init__(self, test_path: str) -> None:
        vals = open(test_path).read().split()
        i = 0

        def nxt() -> str:
            nonlocal i
            v = vals[i]
            i += 1
            return v

        self.K = int(nxt())
        self.S = float(nxt())
        self.lat = float(nxt())
        self.bw = float(nxt())
        self.bpt = int(nxt())
        self.layers = int(nxt())

        self.SLO1 = float(nxt())
        self.SLO2 = float(nxt())
        self.tp_UB = float(nxt())
        self.tp_base = float(nxt())
        self.dist_base = float(nxt())
        self.w_tp = float(nxt())
        self.w_c = float(nxt())

        self.N = int(nxt())
        self.rows: list[list[float]] = []
        self.col = [Curve() for _ in range(6)]
        for _ in range(self.N):
            bs = int(nxt())
            vs = [float(nxt()) for _ in range(6)]
            self.rows.append([bs] + vs)
            for c in range(6):
                if vs[c] >= 0.0:
                    self.col[c].add(bs, vs[c])
        for c in self.col:
            c.finalize()

        R = int(nxt())
        self.reqs: list[Req] = []
        for rid in range(R):
            at = float(nxt())
            lin = int(nxt())
            lout = int(nxt())
            self.reqs.append(Req(rid, at, lin, lout))

        # utilization accounting
        self.useE = 0.0
        self.useC = [0.0] * self.K
        self.useUP = 0.0
        self.useDOWN = 0.0
        self.latUP = 0.0      # per-transfer latency component
        self.latDOWN = 0.0
        self.nUP = 0
        self.nDOWN = 0
        self.remPre = 0.0     # remote busy split
        self.remDec = 0.0
        # Gap decomposition: where does the time between two tokens of the SAME
        # request actually go? Serving time is irreducible; waiting is not.
        self.gapBuckets = {k: 0.0 for k in
            ("wait_E_dpre","run_dpre","wait_up","run_dproc_q","run_dproc",
             "wait_down","wait_E_dpost","run_dpost")}
        self.stageT = {}      # rid -> (stage, since)

        # resources
        self.busyE = False
        self.busyC = [False] * self.K
        self.up_free = 0.0
        self.down_free = 0.0

        # event heap of (time, order, seq, kind, payload)
        self.heap: list[tuple] = []
        self.seq = 0
        self.taskseq = 0
        self.stream_lines: list[str] = []

    # -- cost model ------------------------------------------------------
    def transfer_time(self, ln: int) -> float:
        return self.lat + 8.0 * (ln * self.bpt) / (self.bw * 1e6)

    def push(self, t: float, order: int, kind: str, payload) -> None:
        self.seq += 1
        heapq.heappush(self.heap, (t, order, self.seq, kind, payload))

    # Emission order inside a frame: TDN, XDN, ARR, FIN.
    ORD_TDN, ORD_XDN, ORD_ARR, ORD_FIN = 0, 1, 2, 3

    def enqueue_transfer(self, t: float, up: bool, remote: int, ln: int,
                         kind: str, rids: list[int]) -> None:
        tt = self.transfer_time(ln)
        if up:
            start = max(t, self.up_free)
            done = start + tt
            self.up_free = done
        else:
            start = max(t, self.down_free)
            done = start + tt
            self.down_free = done
        if up:
            self.useUP += tt; self.latUP += self.lat; self.nUP += 1
        else:
            self.useDOWN += tt; self.latDOWN += self.lat; self.nDOWN += 1
        size = ln * self.bpt
        self.push(done, self.ORD_XDN, "XDN", (up, remote, size, kind, list(rids)))

    # -- run -------------------------------------------------------------
    now = 0.0

    def run(self, solver_cmd: list[str], dump_path: str | None = None,
            verbose: bool = False) -> dict:
        proc = subprocess.Popen(
            solver_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            bufsize=0,
        )
        tk = Tokens(proc.stdout)

        def send(line: str) -> None:
            self.stream_lines.append(line)
            proc.stdin.write((line + "\n").encode())

        # startup configuration
        send(f"{self.K} {fmt(self.S)} {fmt(self.lat)} {fmt(self.bw)} "
             f"{self.bpt} {self.layers}")
        send(f"{fmt(self.SLO1)} {fmt(self.SLO2)} {fmt(self.tp_UB)} "
             f"{fmt(self.tp_base)} {fmt(self.dist_base)} {fmt(self.w_tp)} "
             f"{fmt(self.w_c)}")
        send(str(self.N))
        for row in self.rows:
            send(str(int(row[0])) + " " + " ".join(fmt(v) for v in row[1:]))
        proc.stdin.flush()

        for r in self.reqs:
            self.push(r.arrival, self.ORD_ARR, "ARR", r.rid)

        frames = 0
        err: str | None = None
        try:
            while self.heap:
                t = self.heap[0][0]; self.now = t
                batch = []
                while self.heap and self.heap[0][0] == t:
                    batch.append(heapq.heappop(self.heap))
                batch.sort(key=lambda x: (x[1], x[2]))

                lines = []
                for _, _, _, kind, payload in batch:
                    if kind == "ARR":
                        r = self.reqs[payload]
                        lines.append(f"ARR {r.rid} {r.lin}")
                    elif kind == "TDN":
                        spec, dur, effect = payload
                        lines.append(f"TDN {spec} {fmt(dur)}")
                        extra = effect(t)
                        if extra:
                            lines.extend(extra)
                    elif kind == "XDN":
                        up, remote, size, xkind, rids = payload
                        d = "UP" if up else "DOWN"
                        lines.append(
                            f"XDN {d} {remote} {size} {xkind} {len(rids)} "
                            + " ".join(str(x) for x in rids)
                        )
                        self.apply_xdn(up, xkind, rids)

                frames += 1
                send(fmt(t))
                send(str(len(lines)))
                for ln in lines:
                    send(ln)
                proc.stdin.flush()

                self.read_response(tk, t)

                if not self.heap and any(r.stage != DONE for r in self.reqs):
                    raise ProtocolError(
                        "stuck state: unfinished requests but no future event"
                    )

            self.stream_lines.append("END")
            proc.stdin.write(b"END\n")
            proc.stdin.flush()
        except ProtocolError as exc:
            err = str(exc)
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()

        if dump_path:
            with open(dump_path, "w") as fh:
                fh.write("\n".join(self.stream_lines) + "\n")

        if err:
            return {"ok": False, "error": err, "score": 0.0, "frames": frames}

        unfinished = [r.rid for r in self.reqs if r.stage != DONE]
        if unfinished:
            return {"ok": False, "error": f"unfinished requests {unfinished[:5]}",
                    "score": 0.0, "frames": frames}

        res = self.score()
        res.update({"ok": True, "frames": frames})
        if verbose:
            print(res, file=sys.stderr)
        return res

    # -- transfer arrival -------------------------------------------------
    def mark(self, rid, stage, t):
        prev = self.stageT.get(rid)
        if prev is not None:
            pstage, since = prev
            if pstage in self.gapBuckets:
                self.gapBuckets[pstage] += t - since
        self.stageT[rid] = (stage, t)

    def apply_xdn(self, up: bool, xkind: str, rids: list[int]) -> None:
        for rid in rids:
            r = self.reqs[rid]
            if xkind == "PRE":
                r.stage = PROC_RDY if up else POST_RDY
            else:
                if up:
                    r.stage = DPROC_RDY; self.mark(rid, "run_dproc_q", self.now)
                else:
                    r.stage = DPOST_RDY; self.mark(rid, "wait_E_dpost", self.now)

    # -- response ---------------------------------------------------------
    def read_response(self, tk: Tokens, t: float) -> None:
        n = tk.int()
        if n < 0 or n > self.K + 1:
            raise ProtocolError(f"assignment count {n} outside [0, K+1]")

        used_E = False
        used_C = set()

        for _ in range(n):
            sv = tk.next()
            if sv == "E":
                if used_E:
                    raise ProtocolError("two tasks assigned to E in one response")
                if self.busyE:
                    raise ProtocolError("assigned a task to a busy E")
                used_E = True
                svidx = -1
            elif sv.startswith("C"):
                k = int(sv[1:])
                if not (0 <= k < self.K):
                    raise ProtocolError(f"unknown server {sv}")
                if k in used_C:
                    raise ProtocolError(f"two tasks assigned to C{k} in one response")
                if self.busyC[k]:
                    raise ProtocolError(f"assigned a task to a busy C{k}")
                used_C.add(k)
                svidx = k
            else:
                raise ProtocolError(f"unknown server token {sv!r}")

            fam = tk.next()
            step = tk.next()
            if fam not in ("P", "D") or step not in ("PRE", "PROC", "POST"):
                raise ProtocolError(f"unknown task {fam} {step}")

            if fam == "P":
                self.assign_prefill(t, svidx, step, tk)
            else:
                self.assign_decode(t, svidx, step, tk)

    def start_task(self, t: float, svidx: int, dur: float, spec: str, effect) -> None:
        if dur <= 0:
            raise ProtocolError("non-positive task duration")
        if svidx < 0:
            self.busyE = True
            self.useE += self.S + dur
        else:
            self.busyC[svidx] = True
            self.useC[svidx] += self.S + dur
            if spec.find(" P PROC ") >= 0:
                self.remPre += self.S + dur
            else:
                self.remDec += self.S + dur
        self.taskseq += 1
        done = t + self.S + dur
        self.push(done, self.ORD_TDN, "TDN", (spec, dur, effect))

    def assign_prefill(self, t: float, svidx: int, step: str, tk: Tokens) -> None:
        if step == "PRE":
            remote = tk.int()
            rid = tk.int()
            r = self.req(rid)
            if not (0 <= remote < self.K):
                raise ProtocolError(f"P PRE remote {remote} outside [0, K)")
            if svidx != -1:
                raise ProtocolError("P PRE must run on E")
            if r.stage != ARRIVED:
                raise ProtocolError(f"P PRE on request {rid} in wrong stage")
            r.remote = remote
            r.stage = PRE_RUN
            r.next_ls = 0
            dur = self.col[0].at(r.lin)

            def effect(tt: float, r=r) -> list[str]:
                r.stage = PRE_UP
                self.busyE = False
                self.enqueue_transfer(tt, True, r.remote, r.lin, "PRE", [r.rid])
                return []

            self.start_task(t, -1, dur, f"E P PRE {remote} {rid}", effect)

        elif step == "PROC":
            ls = tk.int()
            le = tk.int()
            remote = tk.int()
            rid = tk.int()
            r = self.req(rid)
            if svidx != remote:
                raise ProtocolError("P PROC ran on the wrong server")
            if r.remote != remote:
                raise ProtocolError(f"P PROC remote {remote} != assigned {r.remote}")
            if r.stage != PROC_RDY:
                raise ProtocolError(f"P PROC on request {rid} in wrong stage")
            if not (0 <= ls < le <= self.layers):
                raise ProtocolError(f"illegal piece [{ls}, {le})")
            if ls != r.next_ls:
                raise ProtocolError(f"piece [{ls}, {le}) not gap-free; expected ls={r.next_ls}")
            r.stage = PROC_RUN
            dur = (le - ls) / self.layers * self.col[1].at(r.lin)

            def effect(tt: float, r=r, le=le) -> list[str]:
                self.busyC[r.remote] = False
                r.next_ls = le
                if le == self.layers:
                    r.stage = PROC_DOWN
                    self.enqueue_transfer(tt, False, r.remote, r.lin, "PRE", [r.rid])
                else:
                    r.stage = PROC_RDY
                return []

            self.start_task(t, svidx, dur,
                            f"C{remote} P PROC {ls} {le} {remote} {rid}", effect)

        else:  # POST
            remote = tk.int()
            rid = tk.int()
            r = self.req(rid)
            if svidx != -1:
                raise ProtocolError("P POST must run on E")
            if r.remote != remote:
                raise ProtocolError(f"P POST remote {remote} != assigned {r.remote}")
            if r.stage != POST_RDY:
                raise ProtocolError(f"P POST on request {rid} in wrong stage")
            r.stage = POST_RUN
            dur = self.col[2].at(r.lin)

            def effect(tt: float, r=r) -> list[str]:
                self.busyE = False
                r.stage = DEC_RDY
                r.tdr_done = tt
                return []

            self.start_task(t, -1, dur, f"E P POST {remote} {rid}", effect)

    def assign_decode(self, t: float, svidx: int, step: str, tk: Tokens) -> None:
        if step in ("PRE", "POST"):
            marker = tk.int()
            if marker != -1:
                raise ProtocolError(f"D {step} must use the -1 marker, got {marker}")
            if svidx != -1:
                raise ProtocolError(f"D {step} must run on E")
        else:
            marker = tk.int()  # remote index
            if svidx != marker:
                raise ProtocolError("D PROC ran on the wrong server")

        m = tk.int()
        if m < 1:
            raise ProtocolError(f"group size {m} < 1")
        rids = [tk.int() for _ in range(m)]
        if len(set(rids)) != m:
            raise ProtocolError("duplicate request ids in a group")
        reqs = [self.req(x) for x in rids]

        if step == "PRE":
            for r in reqs:
                if r.stage != DEC_RDY:
                    raise ProtocolError(f"D PRE on request {r.rid} in wrong stage")
            for r in reqs:
                r.stage = DPRE_RUN; self.mark(r.rid, "run_dpre", t)
            dur = self.col[3].at(m)

            def effect(tt: float, reqs=reqs) -> list[str]:
                self.busyE = False
                by_remote: dict[int, list[int]] = {}
                for r in reqs:
                    r.stage = DEC_UP; self.mark(r.rid, "wait_up", tt)
                    by_remote.setdefault(r.remote, []).append(r.rid)
                for rem in sorted(by_remote):
                    ids = by_remote[rem]
                    self.enqueue_transfer(tt, True, rem, len(ids), "DEC", ids)
                return []

            self.start_task(t, -1, dur,
                            f"E D PRE -1 {m} " + " ".join(str(x) for x in rids),
                            effect)

        elif step == "PROC":
            for r in reqs:
                if r.stage != DPROC_RDY:
                    raise ProtocolError(f"D PROC on request {r.rid} in wrong stage")
                if r.remote != marker:
                    raise ProtocolError(
                        f"D PROC member {r.rid} assigned to C{r.remote}, not C{marker}"
                    )
            for r in reqs:
                r.stage = DPROC_RUN; self.mark(r.rid, "run_dproc", t)
            dur = self.col[4].at(m)

            def effect(tt: float, reqs=reqs, rem=marker) -> list[str]:
                self.busyC[rem] = False
                for r in reqs:
                    r.stage = DEC_DOWN; self.mark(r.rid, "wait_down", tt)
                self.enqueue_transfer(tt, False, rem, len(reqs), "DEC",
                                      [r.rid for r in reqs])
                return []

            self.start_task(t, svidx, dur,
                            f"C{marker} D PROC {marker} {m} "
                            + " ".join(str(x) for x in rids), effect)

        else:  # D POST
            for r in reqs:
                if r.stage != DPOST_RDY:
                    raise ProtocolError(f"D POST on request {r.rid} in wrong stage")
            for r in reqs:
                r.stage = DPOST_RUN; self.mark(r.rid, "run_dpost", t)
            dur = self.col[5].at(m)

            def effect(tt: float, reqs=reqs) -> list[str]:
                self.busyE = False
                fins = []
                for r in reqs:
                    r.iters += 1
                    r.tokens.append(tt)
                    if r.iters >= r.lout:
                        r.stage = DONE
                        fins.append(f"FIN {r.rid}")
                    else:
                        r.stage = DEC_RDY; self.mark(r.rid, "wait_E_dpre", tt)
                return fins

            self.start_task(t, -1, dur,
                            f"E D POST -1 {m} " + " ".join(str(x) for x in rids),
                            effect)

    def req(self, rid: int) -> Req:
        if not (0 <= rid < len(self.reqs)):
            raise ProtocolError(f"unknown request id {rid}")
        r = self.reqs[rid]
        if r.stage == DONE:
            raise ProtocolError(f"request {rid} already finished (FIN)")
        return r

    # -- scoring ----------------------------------------------------------
    def score(self) -> dict:
        total_tokens = sum(r.lout for r in self.reqs)
        first_arrival = min(r.arrival for r in self.reqs)
        last_token = max(r.tokens[-1] for r in self.reqs)
        elapsed = last_token - first_arrival
        tp = total_tokens / elapsed if elapsed > 0 else float("inf")

        tdr = sum(r.tdr_done - r.arrival for r in self.reqs) / len(self.reqs)

        gaps = sum(r.lout - 1 for r in self.reqs)
        if gaps > 0:
            span = sum(r.tokens[-1] - r.tokens[0] for r in self.reqs)
            tpot = span / gaps
        else:
            tpot = 0.0

        ex_tdr = max(0.0, (tdr - self.SLO1) / self.SLO1)
        ex_tpot = max(0.0, (tpot - self.SLO2) / self.SLO2)
        dist = math.sqrt(ex_tdr * ex_tdr + ex_tpot * ex_tpot)

        def clamp(x, base, target):
            if target == base:
                return 1.0 if x == target else 0.0
            return max(0.0, min(1.0, (x - base) / (target - base)))

        comp_tp = clamp(tp, self.tp_base, self.tp_UB)
        if self.dist_base > 0:
            comp_c = max(0.0, 1.0 - dist / self.dist_base)
        else:
            comp_c = 1.0 if dist == 0 else 0.0

        norm = self.w_tp * comp_tp + self.w_c * comp_c
        tot = sum(self.gapBuckets.values())
        if tot > 0:
            print("  gap decomposition (share of all inter-token time):", file=sys.stderr)
            for k, v in sorted(self.gapBuckets.items(), key=lambda kv: -kv[1]):
                print(f"     {k:<14} {100*v/tot:6.2f}%   {v:14.1f} ms", file=sys.stderr)
        span = last_token - first_arrival
        util = {
            "E": self.useE / span if span > 0 else 0.0,
            "UP": self.useUP / span if span > 0 else 0.0,
            "DOWN": self.useDOWN / span if span > 0 else 0.0,
            "REMOTE_avg": (sum(self.useC) / self.K) / span if span > 0 else 0.0,
            "REMOTE_max": (max(self.useC)) / span if span > 0 else 0.0,
            "UP_lat_frac": self.latUP / self.useUP if self.useUP > 0 else 0.0,
            "DOWN_lat_frac": self.latDOWN / self.useDOWN if self.useDOWN > 0 else 0.0,
            "nUP": self.nUP, "nDOWN": self.nDOWN,
            "rem_pre_frac": self.remPre / max(1e-9, self.remPre + self.remDec),
        }
        return {
            "util": util,
            "score": 1000.0 * norm,
            "tp": tp, "tdr": tdr, "tpot": tpot, "dist": dist,
            "comp_tp": comp_tp, "comp_c": comp_c,
            "ex_tdr": ex_tdr, "ex_tpot": ex_tpot,
            "SLO1": self.SLO1, "SLO2": self.SLO2,
            "dist_base": self.dist_base, "w_tp": self.w_tp,
            "elapsed": elapsed, "tokens": total_tokens,
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--dump-stream")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    it = Interactor(args.test)
    res = it.run([args.solver], dump_path=args.dump_stream)

    if not res["ok"]:
        print(f"INVALID  score=0  reason: {res['error']}")
        return 1
    if not args.quiet:
        u = res["util"]
        print(f"  util: E={u['E']:.3f} UP={u['UP']:.3f} DOWN={u['DOWN']:.3f} "
              f"remote_avg={u['REMOTE_avg']:.3f} remote_max={u['REMOTE_max']:.3f}"
              f"   BOTTLENECK={max(['E','UP','DOWN','REMOTE_max'], key=lambda k: u[k])}")
        print(f"  link: UP latency-fraction={u['UP_lat_frac']:.3f} "
              f"({u['nUP']} transfers)  DOWN={u['DOWN_lat_frac']:.3f} ({u['nDOWN']})"
              f"   remote prefill-fraction={u['rem_pre_frac']:.3f}")
        print(
            f"score={res['score']:.3f}  tp={res['tp']:.6f} (comp {res['comp_tp']:.3f})  "
            f"tdr={res['tdr']:.3f}  tpot={res['tpot']:.3f}  dist={res['dist']:.4f} "
            f"(comp {res['comp_c']:.3f})  frames={res['frames']}  "
            f"elapsed={res['elapsed']:.3f}"
        )
    else:
        print(f"{res['score']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
