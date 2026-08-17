// Exact replica of the judge's cost model (tools/interactor.py), for in-solver
// forward simulation. The point of this component: our proxies fail because we
// INVENT the workload. A simulator driven by the real observed arrivals/L_in and
// the real cost table has a completely different error profile -- only the
// future is unknown, and on many tests the arrivals are already all in.
//
// Model (docs/statement/EXAMPLES.md, verified against Example 1):
//   E / C task assigned at t occupies [t, t + S + dur]
//   transfer(len)  = latency_ms + len * (8 * bytes_per_token / (bandwidth_gbps * 1e6))
//   UP and DOWN are independent FIFO links, each strictly serial.
#pragma once
#include <vector>
#include <queue>
#include <algorithm>

namespace sim {

struct Cost {                       // piecewise-linear cost curve, as interactor.Curve
    std::vector<std::pair<int,double>> pts;
    void finalize() { std::sort(pts.begin(), pts.end()); }
    double at(double x) const {
        if (pts.empty()) return 0.0;
        if (x <= pts.front().first) return pts.front().second;
        if (x >= pts.back().first)  return pts.back().second;
        size_t i = 1; while (i < pts.size() && pts[i].first < x) ++i;
        double x0 = pts[i-1].first, y0 = pts[i-1].second;
        double x1 = pts[i].first,   y1 = pts[i].second;
        if (x1 == x0) return y0;
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
    }
};

struct Machine {                    // one serial resource (the edge, or a remote)
    double freeAt = 0.0;
    double run(double now, double S, double dur) {   // returns completion time
        double start = std::max(now, freeAt);
        freeAt = start + S + dur;
        return freeAt;
    }
};

struct Link {                       // strictly serial FIFO transfer channel
    double freeAt = 0.0;
    double lat = 0.0, perTok = 0.0;
    double send(double now, long long lenTokens) {
        double start = std::max(now, freeAt);
        freeAt = start + lat + perTok * (double)lenTokens;
        return freeAt;
    }
};

struct Model {
    int K = 1;
    double S = 0.0;
    Cost col[6];                    // P PRE, P PROC, P POST, D PRE, D PROC, D POST
    Link up, down;
    Machine edge;
    std::vector<Machine> remote;
    void init(int K_, double S_, double latency_ms, double bandwidth_gbps,
              long long bytes_per_token) {
        K = K_; S = S_;
        double perTok = 8.0 * (double)bytes_per_token / (bandwidth_gbps * 1e6);
        up.lat = down.lat = latency_ms;
        up.perTok = down.perTok = perTok;
        remote.assign(K, Machine());
    }
    // One request, alone, end to end -- the serial floor used by the floor proofs.
    double soloPrefill(long long lin) const {
        double perTok = up.perTok;
        return (S + col[0].at((double)lin))
             + (up.lat + perTok * lin)
             + (S + col[1].at((double)lin))
             + (down.lat + perTok * lin)
             + (S + col[2].at((double)lin));
    }
    double soloDecodeStep() const {
        double perTok = up.perTok;
        return (S + col[3].at(1.0))
             + (up.lat + perTok)
             + (S + col[4].at(1.0))
             + (down.lat + perTok)
             + (S + col[5].at(1.0));
    }
};

} // namespace sim
