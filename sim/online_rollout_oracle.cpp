// Online one-step action-rollout oracle -- the REALISTIC counterpart of
// offline_rollout_oracle.cpp.
//
// The offline oracle cheats: at every contested E decision it reads the true
// L_out and every future arrival, completes each candidate exactly, and commits
// the best.  A contest solver sees NEITHER -- the interactor sends only
// "ARR rid lin" (no L_out) and reveals arrivals frame by frame.  This program
// answers the make-or-break question before any in-solver rewrite: does a
// one-step rollout still beat the baseline when it must ACT on beliefs?
//
// Mechanism: the REAL timeline runs on true data and is scored on true data.
// But at each contested frame, candidate actions are ranked on a BELIEF copy:
//   - future arrivals dropped (myopic) when --hide-arrivals,
//   - unfinished requests' L_out replaced by an online estimate when
//     --lout mean|priorN  (--lout true isolates arrival-only uncertainty).
// The action is fortified: the baseline action is kept unless another candidate
// is STRICTLY better in belief, so with an empty belief gap it reduces to
// baseline exactly (0 losses by construction on the belief metric).
//
// Build:  c++ -std=c++17 -O2 sim/online_rollout_oracle.cpp -o /tmp/online_oracle
// Run:    /tmp/online_oracle test.txt [--policy both|baseline|online]
//             [--eprio CDAB] [--rprio P|D] [--prefill-order fifo|sjf]
//             [--hide-arrivals] [--lout true|mean|priorN] [--max-rollouts N]
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
using namespace std;

struct Curve {
    vector<pair<int, double>> p;
    void done() { sort(p.begin(), p.end()); }
    double at(double x) const {
        if (p.empty()) return 0.0;
        if (x <= p.front().first) return p.front().second;
        if (x >= p.back().first) return p.back().second;
        size_t i = 1;
        while (i < p.size() && p[i].first < x) ++i;
        double x0 = p[i - 1].first, y0 = p[i - 1].second;
        double x1 = p[i].first, y1 = p[i].second;
        if (x0 == x1) return y0;
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
    }
};

enum Stage {
    FUTURE, ARRIVED, PRE_RUN, PRE_UP, PROC_RDY, PROC_RUN, PROC_DOWN,
    POST_RDY, POST_RUN, DEC_RDY, DPRE_RUN, DEC_UP, DPROC_RDY,
    DPROC_RUN, DEC_DOWN, DPOST_RDY, DPOST_RUN, DONE
};

enum Action { D_POST = 0, D_PRE = 1, P_POST = 2, P_PRE = 3 };
static const char *ACTION_NAME[4] = {"D_POST", "D_PRE", "P_POST", "P_PRE"};

enum EventKind { TASK_DONE, XFER_DONE, ARRIVAL };
enum TaskKind { TP_PRE, TP_PROC, TP_POST, TD_PRE, TD_PROC, TD_POST };

struct Request {
    int lin = 0, lout = 0, remote = -1, iters = 0;
    Stage stage = FUTURE;
    double arrival = 0.0, tdrDone = 0.0, firstTok = -1.0, lastTok = -1.0;
};

struct Event {
    double t = 0.0;
    int ord = 0;
    long long seq = 0;
    EventKind kind = ARRIVAL;
    TaskKind task = TP_PRE;
    int rid = -1, remote = -1;
    bool up = false, decode = false;
    vector<int> rids;
};

struct EventCmp {
    bool operator()(const Event &a, const Event &b) const {
        if (a.t != b.t) return a.t > b.t;
        if (a.ord != b.ord) return a.ord > b.ord;
        return a.seq > b.seq;
    }
};

struct Options {
    string policy = "both";
    string eprio = "CDAB";
    char rprio = 'P';
    bool sjf = false;
    bool hideArrivals = false;
    string loutMode = "true";   // true | mean | prior
    double loutPrior = 8.0;
    bool robust = false;        // override only if action wins under ALL priors
    long long maxRollouts = numeric_limits<long long>::max();
};

struct Score {
    double value = -numeric_limits<double>::infinity();
    double tp = 0.0, tdr = 0.0, tpot = 0.0, dist = 0.0, elapsed = 0.0;
};

struct Sim {
    int K = 1, layers = 1;
    double S = 0.0, lat = 0.0, bw = 0.0, perTok = 0.0;
    long long bpt = 0;
    double SLO1 = 0.0, SLO2 = 0.0, tpUB = 0.0, tpBase = 0.0;
    double distBase = 0.0, wTp = 0.0, wC = 0.0;
    Curve col[6];
    vector<Request> req;
    priority_queue<Event, vector<Event>, EventCmp> heap;
    long long seq = 0;
    bool busyE = false;
    vector<char> busyC;
    vector<int> load;
    double upFree = 0.0, downFree = 0.0, now = 0.0;
    string eprio = "CDAB";
    char rprio = 'P';
    bool sjf = false;

    void push(Event e, double t, int ord) {
        e.t = t;
        e.ord = ord;
        e.seq = ++seq;
        heap.push(std::move(e));
    }

    void startTask(TaskKind task, int remote, vector<int> ids, double dur) {
        if (remote < 0) busyE = true;
        else busyC[remote] = 1;
        Event e;
        e.kind = TASK_DONE;
        e.task = task;
        e.remote = remote;
        e.rids = std::move(ids);
        push(std::move(e), now + S + dur, 0);
    }

    void transfer(bool up, int remote, long long tokens, bool decode,
                  const vector<int> &ids) {
        double &freeAt = up ? upFree : downFree;
        double start = max(now, freeAt);
        freeAt = start + lat + perTok * (double)tokens;
        Event e;
        e.kind = XFER_DONE;
        e.up = up;
        e.remote = remote;
        e.decode = decode;
        e.rids = ids;
        push(std::move(e), freeAt, 1);
    }

    void process(const Event &e) {
        if (e.kind == ARRIVAL) {
            req[e.rid].stage = ARRIVED;
            return;
        }
        if (e.kind == XFER_DONE) {
            for (int id : e.rids) {
                if (!e.decode) req[id].stage = e.up ? PROC_RDY : POST_RDY;
                else req[id].stage = e.up ? DPROC_RDY : DPOST_RDY;
            }
            return;
        }
        if (e.remote < 0) busyE = false;
        else busyC[e.remote] = 0;
        if (e.task == TP_PRE) {
            int id = e.rids[0];
            req[id].stage = PRE_UP;
            transfer(true, req[id].remote, req[id].lin, false, e.rids);
        } else if (e.task == TP_PROC) {
            int id = e.rids[0];
            req[id].stage = PROC_DOWN;
            transfer(false, req[id].remote, req[id].lin, false, e.rids);
        } else if (e.task == TP_POST) {
            int id = e.rids[0];
            req[id].stage = DEC_RDY;
            req[id].tdrDone = now;
        } else if (e.task == TD_PRE) {
            map<int, vector<int>> byRemote;
            for (int id : e.rids) {
                req[id].stage = DEC_UP;
                byRemote[req[id].remote].push_back(id);
            }
            for (const auto &kv : byRemote)
                transfer(true, kv.first, (long long)kv.second.size(), true, kv.second);
        } else if (e.task == TD_PROC) {
            for (int id : e.rids) req[id].stage = DEC_DOWN;
            transfer(false, e.remote, (long long)e.rids.size(), true, e.rids);
        } else {
            for (int id : e.rids) {
                Request &r = req[id];
                ++r.iters;
                if (r.firstTok < 0.0) r.firstTok = now;
                r.lastTok = now;
                if (r.iters >= r.lout) {
                    r.stage = DONE;
                    --load[r.remote];
                } else {
                    r.stage = DEC_RDY;
                }
            }
        }
    }

    bool advanceFrame() {
        if (heap.empty()) return false;
        now = heap.top().t;
        vector<Event> batch;
        while (!heap.empty() && heap.top().t == now) {
            batch.push_back(heap.top());
            heap.pop();
        }
        for (const Event &e : batch) process(e);
        return true;
    }

    vector<int> withStage(Stage st, int remote = -1) const {
        vector<int> ids;
        for (int id = 0; id < (int)req.size(); ++id)
            if (req[id].stage == st && (remote < 0 || req[id].remote == remote))
                ids.push_back(id);
        return ids;
    }

    int choosePrefill(const vector<int> &ids) const {
        int best = ids.front();
        if (!sjf) return best;
        auto cost = [&](int id) {
            const Request &r = req[id];
            return col[0].at(r.lin) + col[1].at(r.lin) + col[2].at(r.lin);
        };
        for (int id : ids)
            if (cost(id) < cost(best)) best = id;
        return best;
    }

    vector<int> legalE() const {
        vector<int> out;
        if (busyE) return out;
        if (!withStage(DPOST_RDY).empty()) out.push_back(D_POST);
        if (!withStage(DEC_RDY).empty()) out.push_back(D_PRE);
        if (!withStage(POST_RDY).empty()) out.push_back(P_POST);
        if (!withStage(ARRIVED).empty()) out.push_back(P_PRE);
        return out;
    }

    int baselineE() const {
        vector<int> legal = legalE();
        if (legal.empty()) return -1;
        for (char c : eprio) {
            int a = c == 'A' ? D_POST : c == 'B' ? D_PRE : c == 'C' ? P_POST : P_PRE;
            if (find(legal.begin(), legal.end(), a) != legal.end()) return a;
        }
        return legal.front();
    }

    void takeE(int action) {
        if (action == D_POST) {
            vector<int> ids = withStage(DPOST_RDY);
            for (int id : ids) req[id].stage = DPOST_RUN;
            startTask(TD_POST, -1, ids, col[5].at((double)ids.size()));
        } else if (action == D_PRE) {
            vector<int> ids = withStage(DEC_RDY);
            for (int id : ids) req[id].stage = DPRE_RUN;
            startTask(TD_PRE, -1, ids, col[3].at((double)ids.size()));
        } else if (action == P_POST) {
            vector<int> ids = withStage(POST_RDY);
            int id = choosePrefill(ids);
            req[id].stage = POST_RUN;
            startTask(TP_POST, -1, {id}, col[2].at(req[id].lin));
        } else if (action == P_PRE) {
            vector<int> ids = withStage(ARRIVED);
            int id = choosePrefill(ids);
            int remote = 0;
            for (int k = 1; k < K; ++k)
                if (load[k] < load[remote]) remote = k;
            req[id].remote = remote;
            req[id].stage = PRE_RUN;
            ++load[remote];
            startTask(TP_PRE, -1, {id}, col[0].at(req[id].lin));
        }
    }

    void takeRemote(int k, bool decode) {
        if (decode) {
            vector<int> ids = withStage(DPROC_RDY, k);
            for (int id : ids) req[id].stage = DPROC_RUN;
            startTask(TD_PROC, k, ids, col[4].at((double)ids.size()));
        } else {
            vector<int> ids = withStage(PROC_RDY, k);
            int id = choosePrefill(ids);
            req[id].stage = PROC_RUN;
            startTask(TP_PROC, k, {id}, col[1].at(req[id].lin));
        }
    }

    void scheduleFrame(int forcedE = -1) {
        if (!busyE) {
            int action = forcedE >= 0 ? forcedE : baselineE();
            if (action >= 0) takeE(action);
        }
        for (int k = 0; k < K; ++k) {
            if (busyC[k]) continue;
            bool p = !withStage(PROC_RDY, k).empty();
            bool d = !withStage(DPROC_RDY, k).empty();
            if (p && d) takeRemote(k, rprio == 'D');
            else if (p) takeRemote(k, false);
            else if (d) takeRemote(k, true);
        }
    }

    bool finished() const {
        for (const Request &r : req)
            if (r.stage != DONE) return false;
        return true;
    }

    Score score() const {
        Score z;
        if (!finished() || req.empty()) return z;
        long long totalTok = 0, gaps = 0;
        double firstArr = numeric_limits<double>::infinity();
        double last = -numeric_limits<double>::infinity();
        double tdrSum = 0.0, span = 0.0;
        for (const Request &r : req) {
            totalTok += r.lout;
            firstArr = min(firstArr, r.arrival);
            last = max(last, r.lastTok);
            tdrSum += r.tdrDone - r.arrival;
            gaps += r.lout - 1;
            if (r.lout > 1) span += r.lastTok - r.firstTok;
        }
        z.elapsed = last - firstArr;
        z.tp = z.elapsed > 0.0 ? (double)totalTok / z.elapsed
                               : numeric_limits<double>::infinity();
        z.tdr = tdrSum / (double)req.size();
        z.tpot = gaps > 0 ? span / (double)gaps : 0.0;
        double exT = max(0.0, (z.tdr - SLO1) / SLO1);
        double exP = max(0.0, (z.tpot - SLO2) / SLO2);
        z.dist = sqrt(exT * exT + exP * exP);
        double ctp;
        if (tpUB == tpBase) ctp = z.tp == tpUB ? 1.0 : 0.0;
        else ctp = max(0.0, min(1.0, (z.tp - tpBase) / (tpUB - tpBase)));
        double cc = distBase > 0.0 ? max(0.0, 1.0 - z.dist / distBase)
                                  : (z.dist == 0.0 ? 1.0 : 0.0);
        z.value = 1000.0 * (wTp * ctp + wC * cc);
        return z;
    }
};

struct OracleStats {
    long long decisionFrames = 0, contestedFrames = 0, rolloutFrames = 0;
    long long candidates = 0, overrides = 0, selected[4] = {0, 0, 0, 0};
};

static Score completeBaseline(Sim s, int firstAction = -1) {
    s.scheduleFrame(firstAction);
    while (s.advanceFrame()) s.scheduleFrame();
    return s.score();
}

static Score runBaseline(Sim s) {
    while (s.advanceFrame()) s.scheduleFrame();
    return s.score();
}

// Build the belief the online rollout is allowed to act on. loutEstOverride>=0
// forces a specific L_out estimate (used by the robust multi-prior filter).
static Sim makeBelief(const Sim &real, const Options &opt, double meanLout,
                      double loutEstOverride = -1.0) {
    Sim b = real;
    bool applyEst = loutEstOverride >= 0.0 || opt.loutMode != "true";
    if (applyEst) {
        double est = loutEstOverride >= 0.0
                         ? loutEstOverride
                         : ((opt.loutMode == "mean" && meanLout > 0.0)
                                ? meanLout
                                : opt.loutPrior);
        int e = (int)llround(est);
        if (e < 1) e = 1;
        for (Request &r : b.req) {
            if (r.stage != DONE && r.stage != FUTURE) {
                r.lout = max(e, r.iters + 1);
            }
        }
    }
    if (opt.hideArrivals) {
        vector<Event> keep;
        while (!b.heap.empty()) {
            Event e = b.heap.top();
            b.heap.pop();
            if (e.kind != ARRIVAL) keep.push_back(e);
        }
        for (Event &e : keep) b.heap.push(e);
        // Neutralize not-yet-arrived requests: constant contribution across all
        // candidate actions at this frame, so belief ranking is unaffected.
        for (Request &r : b.req) {
            if (r.stage == FUTURE) {
                r.stage = DONE;
                r.lout = 1;
                r.iters = 1;
                r.arrival = b.now;
                r.tdrDone = b.now;
                r.firstTok = b.now;
                r.lastTok = b.now;
            }
        }
    }
    return b;
}

static Score runOnline(Sim s, const Options &opt, OracleStats &stats) {
    double loutSum = 0.0;
    long long loutCnt = 0;
    vector<char> counted(s.req.size(), 0);
    while (s.advanceFrame()) {
        for (int i = 0; i < (int)s.req.size(); ++i)
            if (!counted[i] && s.req[i].stage == DONE) {
                counted[i] = 1;
                loutSum += s.req[i].lout;   // known once the request completes
                ++loutCnt;
            }
        vector<int> legal = s.legalE();
        int chosen = -1;
        if (!legal.empty()) {
            ++stats.decisionFrames;
            if (legal.size() > 1) ++stats.contestedFrames;
        }
        if (legal.size() > 1 && stats.rolloutFrames < opt.maxRollouts) {
            ++stats.rolloutFrames;
            double meanL = loutCnt ? loutSum / (double)loutCnt : opt.loutPrior;
            int base = s.baselineE();
            chosen = base;
            if (!opt.robust) {
                Sim b0 = makeBelief(s, opt, meanL);
                double best = completeBaseline(b0, base).value;
                ++stats.candidates;
                for (int action : legal) {
                    if (action == base) continue;
                    Sim b = makeBelief(s, opt, meanL);
                    double v = completeBaseline(b, action).value;
                    ++stats.candidates;
                    if (v > best + 1e-9) { best = v; chosen = action; }
                }
            } else {
                // Robust filter: an override must beat the baseline under EVERY
                // L_out estimate in the set. A choice that only wins for one
                // guessed L_out is a belief artifact and is rejected.
                double priors[3] = {meanL * 0.5, meanL, meanL * 2.0};
                double bestMargin = 0.0;
                for (int action : legal) {
                    if (action == base) continue;
                    double worst = numeric_limits<double>::infinity();
                    for (double pr : priors) {
                        Sim bb = makeBelief(s, opt, meanL, pr);
                        double vb = completeBaseline(bb, base).value;
                        Sim ba = makeBelief(s, opt, meanL, pr);
                        double va = completeBaseline(ba, action).value;
                        stats.candidates += 2;
                        worst = min(worst, va - vb);
                    }
                    if (worst > 1e-9 && worst > bestMargin) {
                        bestMargin = worst;
                        chosen = action;
                    }
                }
            }
            if (chosen != base) ++stats.overrides;
            ++stats.selected[chosen];
        } else if (!legal.empty()) {
            chosen = s.baselineE();
            ++stats.selected[chosen];
        }
        s.scheduleFrame(chosen);
    }
    return s.score();
}

static Sim readTest(const string &path, const Options &opt) {
    ifstream in(path);
    if (!in) throw runtime_error("cannot open test: " + path);
    Sim s;
    in >> s.K >> s.S >> s.lat >> s.bw >> s.bpt >> s.layers;
    in >> s.SLO1 >> s.SLO2 >> s.tpUB >> s.tpBase >> s.distBase >> s.wTp >> s.wC;
    int n;
    in >> n;
    for (int i = 0; i < n; ++i) {
        int x;
        in >> x;
        for (int c = 0; c < 6; ++c) {
            double y;
            in >> y;
            if (y >= 0.0) s.col[c].p.push_back({x, y});
        }
    }
    for (Curve &c : s.col) c.done();
    int rcount;
    in >> rcount;
    s.req.resize(rcount);
    for (int id = 0; id < rcount; ++id) {
        Request &r = s.req[id];
        in >> r.arrival >> r.lin >> r.lout;
        Event e;
        e.kind = ARRIVAL;
        e.rid = id;
        s.push(e, r.arrival, 2);
    }
    if (!in) throw runtime_error("malformed test: " + path);
    s.perTok = 8.0 * (double)s.bpt / (s.bw * 1e6);
    s.busyC.assign(s.K, 0);
    s.load.assign(s.K, 0);
    s.eprio = opt.eprio;
    s.rprio = opt.rprio;
    s.sjf = opt.sjf;
    return s;
}

static void printScore(const char *label, const Score &s) {
    cout << fixed << setprecision(3) << label << " score=" << s.value
         << setprecision(6) << " tp=" << s.tp << " tdr=" << s.tdr
         << " tpot=" << s.tpot << setprecision(4) << " dist=" << s.dist
         << setprecision(3) << " elapsed=" << s.elapsed << '\n';
}

int main(int argc, char **argv) {
    try {
        if (argc < 2) {
            cerr << "usage: " << argv[0]
                 << " test [--policy both|baseline|online] [--eprio CDAB]"
                    " [--rprio P|D] [--prefill-order fifo|sjf] [--hide-arrivals]"
                    " [--lout true|mean|priorN] [--max-rollouts N]\n";
            return 2;
        }
        Options opt;
        for (int i = 2; i < argc; ++i) {
            string a = argv[i];
            auto value = [&](const string &name) -> string {
                if (i + 1 >= argc) throw runtime_error("missing value for " + name);
                return argv[++i];
            };
            if (a == "--policy") opt.policy = value(a);
            else if (a == "--eprio") opt.eprio = value(a);
            else if (a == "--rprio") opt.rprio = value(a).at(0);
            else if (a == "--prefill-order") opt.sjf = value(a) == "sjf";
            else if (a == "--hide-arrivals") opt.hideArrivals = true;
            else if (a == "--lout") {
                string v = value(a);
                if (v == "true" || v == "mean") opt.loutMode = v;
                else if (v.rfind("prior", 0) == 0) {
                    opt.loutMode = "prior";
                    opt.loutPrior = stod(v.substr(5));
                } else throw runtime_error("--lout must be true|mean|priorN");
            } else if (a == "--robust") opt.robust = true;
            else if (a == "--max-rollouts") opt.maxRollouts = stoll(value(a));
            else throw runtime_error("unknown option: " + a);
        }
        Sim initial = readTest(argv[1], opt);
        if (opt.policy == "both" || opt.policy == "baseline")
            printScore("baseline", runBaseline(initial));
        if (opt.policy == "both" || opt.policy == "online") {
            OracleStats stats;
            Score result = runOnline(initial, opt, stats);
            printScore("online  ", result);
            cout << "actions decisions=" << stats.decisionFrames
                 << " contested=" << stats.contestedFrames
                 << " rollout_frames=" << stats.rolloutFrames
                 << " overrides=" << stats.overrides
                 << " candidates=" << stats.candidates;
            for (int a = 0; a < 4; ++a)
                cout << ' ' << ACTION_NAME[a] << '=' << stats.selected[a];
            cout << '\n';
        }
    } catch (const exception &e) {
        cerr << "error: " << e.what() << '\n';
        return 2;
    }
    return 0;
}
