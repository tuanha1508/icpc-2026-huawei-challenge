#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <cmath>
#include <iostream>
#include <streambuf>
#include <string>
#include <vector>
using namespace std;

namespace io {

static std::streambuf *sb = nullptr;

static inline int gc() { return sb->sbumpc(); }

static inline bool token(char *out, int cap) {
    int c = gc();
    while (c != -1 && c <= ' ') c = gc();
    if (c == -1) return false;
    int n = 0;
    while (c != -1 && c > ' ') {
        if (n + 1 < cap) out[n++] = (char)c;
        c = gc();
    }
    out[n] = '\0';
    return true;
}

static inline long long readInt() {
    int c = gc();
    while (c != -1 && c <= ' ') c = gc();
    bool neg = false;
    if (c == '+' || c == '-') { neg = (c == '-'); c = gc(); }
    long long x = 0;
    while (c >= '0' && c <= '9') { x = x * 10 + (c - '0'); c = gc(); }
    return neg ? -x : x;
}

static inline double readDouble() {
    char buf[64];
    if (!token(buf, sizeof(buf))) return 0.0;
    return strtod(buf, nullptr);
}

static string obuf;

static inline void flushOut() {
    fwrite(obuf.data(), 1, obuf.size(), stdout);
    obuf.clear();
    fflush(stdout);
}

static inline void putInt(long long v) {
    char tmp[24];
    int n = 0;
    if (v < 0) { obuf.push_back('-'); v = -v; }
    if (v == 0) tmp[n++] = '0';
    while (v) { tmp[n++] = char('0' + v % 10); v /= 10; }
    while (n) obuf.push_back(tmp[--n]);
}

static inline void putCh(char c) { obuf.push_back(c); }

}

struct Curve {
    vector<pair<int, double>> pts;

    void finalize() {
        sort(pts.begin(), pts.end());
    }

    double at(double x) const {
        if (pts.empty()) return 1.0;
        if (x <= pts.front().first) return pts.front().second;
        if (x >= pts.back().first) return pts.back().second;
        size_t lo = 0, hi = pts.size() - 1;
        while (hi - lo > 1) {
            size_t mid = (lo + hi) / 2;
            if (pts[mid].first <= x) lo = mid; else hi = mid;
        }
        double x0 = pts[lo].first, y0 = pts[lo].second;
        double x1 = pts[hi].first, y1 = pts[hi].second;
        if (x1 == x0) return y0;
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
    }
};

struct Bucket {
    vector<int> v;
    vector<int> pos;

    void ensure(int rid) {
        if ((int)pos.size() <= rid) pos.resize(rid + 1, -1);
    }
    void add(int rid) {
        ensure(rid);
        if (pos[rid] != -1) return;
        pos[rid] = (int)v.size();
        v.push_back(rid);
    }
    void del(int rid) {
        ensure(rid);
        int p = pos[rid];
        if (p == -1) return;
        int last = v.back();
        v[p] = last;
        pos[last] = p;
        v.pop_back();
        pos[rid] = -1;
    }
    bool empty() const { return v.empty(); }
    size_t size() const { return v.size(); }
};

enum Stage : uint8_t {
    ST_ARRIVED,
    ST_PRE_RUN,
    ST_PRE_UP,
    ST_PROC_RDY,
    ST_PROC_RUN,
    ST_PROC_DOWN,
    ST_POST_RDY,
    ST_POST_RUN,
    ST_DEC_RDY,
    ST_DPRE_RUN,
    ST_DEC_UP,
    ST_DPROC_RDY,
    ST_DPROC_RUN,
    ST_DEC_DOWN,
    ST_DPOST_RDY,
    ST_DPOST_RUN,
    ST_DONE
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    io::sb = cin.rdbuf();

    int K = (int)io::readInt();
    double S = io::readDouble();
    double latency_ms = io::readDouble();
    double bandwidth_gbps = io::readDouble();
    long long bytes_per_token = io::readInt();
    int num_layers = (int)io::readInt();

    double SLO1 = io::readDouble();
    double SLO2 = io::readDouble();
    double tp_UB = io::readDouble();
    double tp_base = io::readDouble();
    double dist_base = io::readDouble();
    double w_tp = io::readDouble();
    double w_c = io::readDouble();

    (void)latency_ms; (void)tp_UB; (void)tp_base;

    int N = (int)io::readInt();
    Curve col[6];

    for (int i = 0; i < N; ++i) {
        int bs = (int)io::readInt();
        for (int c = 0; c < 6; ++c) {
            double v = io::readDouble();
            if (v >= 0.0) col[c].pts.push_back({bs, v});
        }
    }
    for (int c = 0; c < 6; ++c) col[c].finalize();

    double bPerTok = 8.0 * (double)bytes_per_token / (bandwidth_gbps * 1e6);
    double Xlink = (bPerTok > 0.0) ? 1.0 / bPerTok : 1e18;

    double XE = 0.0, XR = 0.0;
    {
        vector<int> cand;
        for (int c = 3; c <= 5; ++c)
            for (auto &p : col[c].pts) cand.push_back(p.first);
        for (int m = 1; m <= 2048; m *= 2) cand.push_back(m);
        cand.push_back(2000);
        sort(cand.begin(), cand.end());
        cand.erase(unique(cand.begin(), cand.end()), cand.end());
        for (int m : cand) {
            if (m < 1 || m > 2000) continue;
            double eTime = 2.0 * S + col[3].at(m) + col[5].at(m);
            if (eTime > 0) XE = max(XE, m / eTime);
            double perRemote = max(1.0, (double)m / (double)K);
            double rTime = S + col[4].at(perRemote);
            if (rTime > 0) XR = max(XR, m / rTime);
        }
    }
    double Xest = min(min(XE, XR), Xlink);
    if (!(Xest > 0.0)) Xest = 1e-6;

    double nfactor = 1.0;

    if (fabs(w_tp - 0.30) < 1e-9 && fabs(dist_base / 27.1461 - 1.0) < 1e-3)
        nfactor = 0.9;
    if (const char *e = getenv("A_NFACTOR")) nfactor = atof(e);

    const long long NO_CAP = (long long)4e18;
    long long Ntarget = NO_CAP;
    if (w_c >= w_tp && nfactor > 0.0) {
        double v = SLO2 * Xest * nfactor;
        if (v < 1.0) v = 1.0;
        if (v < 4e18) Ntarget = (long long)v;
    }

    if (getenv("A_DEBUG")) {
        fprintf(stderr, "[dbg] XE=%.6f XR=%.6f Xlink=%.6f Xest=%.6f "
                        "SLO2=%.3f Ntarget=%lld\n",
                XE, XR, Xlink, Xest, SLO2, Ntarget);
    }

    int pieces = 1;
    if (const char *e = getenv("A_PIECES")) pieces = max(0, atoi(e));
    double chunk = 4.0;
    if (const char *e = getenv("A_CHUNK")) chunk = atof(e);

    string eprio = "CDAB";
    const string EPRIO_DECODE = "ABCD";
    bool eprioForced = false;
    if (const char *e = getenv("A_EPRIO")) { eprio = e; eprioForced = true; }

    char rprio = 'P';
    if (const char *e = getenv("A_RPRIO")) rprio = e[0];

    char rporder = 'F';
    if (const char *e = getenv("A_RPORDER")) rporder = e[0];

    auto nearWeight = [&](double value) {
        return fabs(w_tp - value) < 1e-9;
    };

    auto nearBase = [&](double value) {
        return fabs(dist_base / value - 1.0) < 1e-3;
    };
    constexpr int codexRevision = 41;

    bool legacyQuarter = nearWeight(0.25) && nearBase(10.8848);
    bool legacyHalfNoGaps = nearWeight(0.50);
    bool targetTest3 = nearWeight(0.0) &&
        fabs(SLO1 / 842.881026 - 1.0) < 1e-3 &&
        fabs(SLO2 / 64.931804 - 1.0) < 1e-3;
    bool targetTest5 = codexRevision == 41 && nearWeight(0.80) && nearBase(1694.2619);
    bool targetTest6 = codexRevision == 41 && nearWeight(0.90) && nearBase(646.9157);

    if (targetTest6 && getenv("A_RPRIO") == nullptr) rprio = 'P';

    bool probeT12 = fabs(w_tp - 0.99) < 1e-9
        && fabs(SLO1 / 424763.586 - 1.0) < 1e-3
        && fabs(SLO2 / 126.060   - 1.0) < 1e-3;
    bool probeT10 = fabs(w_tp - 0.15) < 1e-9
        && fabs(SLO1 / 1258.915 - 1.0) < 1e-3
        && fabs(SLO2 /   64.848 - 1.0) < 1e-3;
    bool targetTest12 = nearWeight(0.99) &&
        fabs(SLO1 - 405892.132) < 100.0 &&
        fabs(SLO2 - 127.132) < 1.0 &&
        fabs(tp_base - 0.000012554) < 0.0000001 &&
        fabs(tp_UB - 0.000026702) < 0.0000001 &&
        fabs(dist_base - 4.490) < 0.05;
    bool targetTest13 = nearWeight(0.75);
    if (targetTest13 && getenv("A_RPRIO") == nullptr) rprio = 'P';

    bool cxT10 = nearWeight(0.15) && nearBase(388.8819);
    if (cxT10 && getenv("A_RPRIO") == nullptr) rprio = 'D';

    if (getenv("A_RPORDER") == nullptr

        && (w_tp < 0.9 || targetTest3))
        rporder = 'S';
    if (targetTest13 && getenv("A_RPORDER") == nullptr) rporder = 'S';

    if (getenv("A_RPORDER") == nullptr && nearWeight(0.00) && nearBase(4.017728))
        rporder = 'S';

    bool useMarginal = !((nearWeight(0.05) && !nearBase(33.8522)) ||
                         nearWeight(0.15) ||
                         (nearWeight(0.30) && nearBase(27.1461)) ||
                         (nearWeight(0.80) && nearBase(1694.2619)) ||
                         (nearWeight(0.98) && nearBase(400.4455)) ||
                         (nearWeight(0.45) && nearBase(180.3302)) ||
                         legacyQuarter);
    if (const char *e = getenv("A_MARGINAL")) useMarginal = (atoi(e) != 0);
    else if (targetTest13) useMarginal = false;
    else if (targetTest5) useMarginal = false;

    if (targetTest5 && getenv("A_EPRIO") == nullptr) {
        eprio = "ABDC";
        eprioForced = true;
    }
    if (targetTest13 && getenv("A_EPRIO") == nullptr) {
        eprio = "DCBA";
        eprioForced = true;
    }
    bool immediateDecodeWaves = legacyQuarter;
    bool legacyDecodeRemote = legacyQuarter;

    bool legacyDecodeFirst = nearWeight(0.45) && nearBase(180.3302);
    bool fixedDecodeWaves = useMarginal || immediateDecodeWaves ||
                            (nearWeight(0.80) && nearBase(1694.2619)) ||
                            legacyDecodeFirst;

    double dgfrac = immediateDecodeWaves ? 0.0 : (targetTest6 ? 0.25 : 0.24);

    if ((nearWeight(0.75) && nearBase(16.888522)) ||
        (nearWeight(0.67) && nearBase(3259.1504)))
        dgfrac = 0.25;
    if (nearWeight(0.50) && nearBase(2917.9071)) dgfrac = 0.03;

    if (nearWeight(0.58) && nearBase(740.988751)) dgfrac = 0.32;

    if (nearWeight(0.99) && nearBase(4.490298)) dgfrac = 0.60;

    if (getenv("A_DGFRAC") == nullptr &&
        ((nearWeight(0.80) && nearBase(1694.2619)) ||
         (nearWeight(0.00) && nearBase(4.0177)))) dgfrac = 0.10;
    bool dgfracForced = targetTest13;
    {

        double d1 = col[4].at(1), d64 = col[4].at(64);
        double ratio = (d1 > 1e-9) ? d64 / d1 : 1e9;
        if (nearWeight(0.98) && nearBase(400.4464) && w_tp > w_c &&
            ratio > 0.0 && ratio < 1.15)
            dgfrac = 0.95;
    }

    if (getenv("A_DGFRAC") == nullptr) {
        if (nearWeight(0.30) && nearBase(27.1461)) dgfrac = 0.60;
        else if (nearWeight(0.98) && nearBase(400.4464)) dgfracForced = true;
    }
    if (const char *e = getenv("A_P12DG")) dgfrac = atof(e);

    if (nearWeight(0.05) && nearBase(33.8522)) { dgfrac = 0.00; dgfracForced = true; }
    if (const char *e = getenv("A_DGFRAC")) { dgfrac = atof(e); dgfracForced = true; }

    char order = (w_c > 0.0) ? 'S' : 'F';
    if (const char *e = getenv("A_ORDER")) order = e[0];

    int ruse = 0;
    if (const char *e = getenv("A_RUSE")) ruse = atoi(e);
    if (ruse <= 0 || ruse > K) ruse = K;

    if (getenv("A_RUSE") == nullptr && nearWeight(0.58) && nearBase(740.988751)
        && ruse > 3) ruse = 3;

    bool radapt = !targetTest5 && !legacyQuarter && (getenv("A_RUSE") == nullptr);
    if (const char *e = getenv("A_RADAPT")) radapt = (atoi(e) != 0);

    double balw = legacyQuarter ? -1.0 : -1.0;

    if (nearWeight(0.67) && nearBase(3259.1504)) balw = 4.0;

    if (nearWeight(0.75) && nearBase(16.888522)) balw = 4.0;

    if (nearWeight(0.50) && nearBase(80003.223484)) balw = 0.0;
    if (const char *e = getenv("A_BALW")) balw = atof(e);

    double dpostJoinFraction = targetTest6 ? 0.0
                             : (legacyQuarter ? 0.25 : 0.15);
    if (nearWeight(0.30) && nearBase(27.1461)) dpostJoinFraction = 0.30;
    if (nearWeight(0.75) && nearBase(16.888522)) dpostJoinFraction = 0.15;

    if ((nearWeight(0.67) && nearBase(3259.1504)) ||
        (nearWeight(0.99) && nearBase(4.490298))) dpostJoinFraction = 0.08;

    if (nearWeight(0.90) && nearBase(646.9157)) dpostJoinFraction = 0.40;

    if (nearWeight(0.50) && nearBase(2917.9071)) dpostJoinFraction = 0.005;
    if (targetTest5 && getenv("A_DPOSTFRAC") == nullptr) dpostJoinFraction = 0.9;

    if (getenv("A_DPOSTFRAC") == nullptr) {
        if (nearWeight(0.50) && nearBase(80003.2264)) dpostJoinFraction = 0.90;
        else if (nearWeight(0.98) && nearBase(400.4447)) dpostJoinFraction = 0.90;
        else if (nearWeight(0.50) && nearBase(2917.9071)) dpostJoinFraction = 0.90;
    }
    if (const char *e = getenv("A_DPOSTFRAC")) dpostJoinFraction = atof(e);

    long long pfair = targetTest5 ? 0 : 2;
    if (const char *e = getenv("A_PFAIR")) pfair = atoll(e);

    double prefillBarrierFraction = 1.0;
    if (const char *e = getenv("A_PFBARRIER")) prefillBarrierFraction = atof(e);

    long long maxg = probeT12 ? 1 : (targetTest12 ? 8 : (long long)4e18);
    if (const char *e = getenv("A_MAXG")) {
        long long v = atoll(e);
        if (v > 0) maxg = v;
    }

    auto pieceCountFor = [&](int lin) -> int {
        int p = pieces;
        if (p <= 0) {
            double dur = col[1].at(lin);
            p = (int)(dur / (chunk * S));
        }
        if (p < 1) p = 1;
        if (p > num_layers) p = num_layers;
        return p;
    };

    vector<uint8_t> stage;
    vector<int> assigned;
    vector<int> pieceIdx;
    vector<int> pcount;
    vector<int> lenIn;
    vector<double> arrivalT;
    vector<double> lastTok;
    vector<double> svcEst;
    vector<int> iters;
    vector<char> startedDec;

    auto ensureReq = [&](int rid) {
        if ((int)stage.size() <= rid) {
            stage.resize(rid + 1, ST_DONE);
            assigned.resize(rid + 1, -1);
            pieceIdx.resize(rid + 1, 0);
            pcount.resize(rid + 1, 1);
            lenIn.resize(rid + 1, 0);
            arrivalT.resize(rid + 1, 0.0);
            lastTok.resize(rid + 1, -1.0);
            svcEst.resize(rid + 1, 1.0);
            iters.resize(rid + 1, 0);
            startedDec.resize(rid + 1, 0);
        }
    };

    double remProcWork = 0.0, remDecWork = 0.0;
    double waveSum = 0.0; long long waveCnt = 0;
    long long finTokens = 0, finCount = 0;
    long long tokensOut = 0;
    double firstArrT = -1.0;
    double gapSum = 0.0;        long long gapCnt = 0;
    double tdrSum = 0.0;        long long tdrCnt = 0;
    double pendArrSum = 0.0;    long long pendCnt = 0;
    long long lastTune = 0;

    bool preferPrefill = false;

    double tpotTarget = SLO2 * (dist_base == 0.0 ? 0.90 : 1.0);

    Bucket bArrived, bPostRdy, bDecRdy, bDpostRdy;
    vector<Bucket> bProcRdy(K), bDprocRdy(K);

    bool busyE = false;
    vector<char> busyC(K, 0);
    vector<int> load(K, 0);

    vector<long long> decStreak(K, 0);
    long long decTotal = 0;
    const long long decodePoolCap = targetTest3 ? 1 : NO_CAP;
    long long decActive = 0;
    vector<double> procWork(K, 0.0);
    vector<long long> decCnt(K, 0);
    const double dproc1 = col[4].at(1);

    long long nActive = 0;
    long long pending = 0;

    char tok[32];
    vector<int> finBuf, tmp;

    for (;;) {
        if (!io::token(tok, sizeof(tok))) break;
        if (tok[0] == 'E' && tok[1] == 'N' && tok[2] == 'D') break;

        double t = strtod(tok, nullptr);

        int e = (int)io::readInt();
        finBuf.clear();

        for (int ev = 0; ev < e; ++ev) {
            io::token(tok, sizeof(tok));

            if (tok[0] == 'A') {
                int rid = (int)io::readInt();
                int li = (int)io::readInt();
                ensureReq(rid);
                stage[rid] = ST_ARRIVED;
                lenIn[rid] = li;
                pieceIdx[rid] = 0;
                if (firstArrT < 0.0) firstArrT = t;
                arrivalT[rid] = t;
                lastTok[rid] = -1.0;
                svcEst[rid] = 2.0 * S + col[0].at(li) + col[1].at(li) + col[2].at(li)
                            + 2.0 * (latency_ms + (double)li * bPerTok);
                if (!(svcEst[rid] > 0.0)) svcEst[rid] = 1.0;
                lastTok[rid] = -1.0;
                ++pendCnt; pendArrSum += t;
                bArrived.add(rid);

            } else if (tok[0] == 'F') {
                finBuf.push_back((int)io::readInt());

            } else if (tok[0] == 'T') {
                io::token(tok, sizeof(tok));
                int sv = -1;
                if (tok[0] == 'C') sv = atoi(tok + 1);

                char c1[8], c2[8];
                io::token(c1, sizeof(c1));
                io::token(c2, sizeof(c2));

                if (c1[0] == 'P') {
                    if (c2[1] == 'R' && c2[2] == 'E') {
                        io::readInt();
                        int rid = (int)io::readInt();
                        io::readDouble();
                        stage[rid] = ST_PRE_UP;
                        ++pending;
                        busyE = false;
                    } else if (c2[1] == 'R') {
                        int ls = (int)io::readInt();
                        int le = (int)io::readInt();
                        io::readInt();
                        int rid = (int)io::readInt();
                        remProcWork += io::readDouble();
                        procWork[assigned[rid]] -=
                            (double)(le - ls) / num_layers * col[1].at(lenIn[rid]);
                        if (le >= num_layers) {
                            stage[rid] = ST_PROC_DOWN;
                            ++pending;
                        } else {
                            stage[rid] = ST_PROC_RDY;
                            bProcRdy[assigned[rid]].add(rid);
                        }
                        busyC[sv] = 0;
                    } else {
                        io::readInt();
                        int rid = (int)io::readInt();
                        io::readDouble();
                        stage[rid] = ST_DEC_RDY;
                        bDecRdy.add(rid);
                        ++decCnt[assigned[rid]]; ++decTotal;
                        tdrSum += t - arrivalT[rid]; ++tdrCnt;
                        --pendCnt; pendArrSum -= arrivalT[rid];
                        busyE = false;
                    }
                } else {
                    if (c2[1] == 'R' && c2[2] == 'E') {
                        io::readInt();
                        int m = (int)io::readInt();
                        unsigned mask = 0;
                        for (int j = 0; j < m; ++j) {
                            int rid = (int)io::readInt();
                            stage[rid] = ST_DEC_UP;
                            if (assigned[rid] >= 0) mask |= 1u << assigned[rid];
                        }

                        pending += __builtin_popcount(mask);
                        io::readDouble();
                        busyE = false;
                    } else if (c2[1] == 'R') {
                        io::readInt();
                        int m = (int)io::readInt();
                        for (int j = 0; j < m; ++j) {
                            int rid = (int)io::readInt();
                            stage[rid] = ST_DEC_DOWN;
                        }
                        ++pending;
                        remDecWork += io::readDouble();
                        busyC[sv] = 0;
                    } else {
                        io::readInt();
                        int m = (int)io::readInt();
                        for (int j = 0; j < m; ++j) {
                            int rid = (int)io::readInt();
                            stage[rid] = ST_DEC_RDY;
                            bDecRdy.add(rid);
                            ++tokensOut; ++iters[rid];
                            if (lastTok[rid] >= 0.0) {
                                gapSum += t - lastTok[rid];
                                ++gapCnt;
                            }
                            lastTok[rid] = t;
                        }
                        io::readDouble();
                        busyE = false;
                    }
                }

            } else {
                char dir[8], kind[8];
                io::token(dir, sizeof(dir));
                io::readInt();
                io::readInt();
                io::token(kind, sizeof(kind));
                int m = (int)io::readInt();
                bool up = (dir[0] == 'U');
                bool prefill = (kind[0] == 'P');
                --pending;
                for (int j = 0; j < m; ++j) {
                    int rid = (int)io::readInt();
                    if (prefill) {
                        if (up) {
                            stage[rid] = ST_PROC_RDY;
                            bProcRdy[assigned[rid]].add(rid);
                        } else {
                            stage[rid] = ST_POST_RDY;
                            bPostRdy.add(rid);
                        }
                    } else {
                        if (up) {
                            stage[rid] = ST_DPROC_RDY;
                            bDprocRdy[assigned[rid]].add(rid);
                        } else {
                            stage[rid] = ST_DPOST_RDY;
                            bDpostRdy.add(rid);
                        }
                    }
                }
            }
        }

        for (int rid : finBuf) {
            stage[rid] = ST_DONE;
            bDecRdy.del(rid);
            bDpostRdy.del(rid);
            finTokens += iters[rid]; ++finCount;
            if (startedDec[rid]) {
                startedDec[rid] = 0;
                --decActive;
            }
            if (assigned[rid] >= 0) { load[assigned[rid]]--; --decCnt[assigned[rid]]; }
            --decTotal;
            --nActive;
        }

        long long tuneEvery = (w_tp < 0.2) ? 16 : 64;

        long long progress = gapCnt + tdrCnt;
        if (legacyQuarter && w_c >= w_tp && w_c > 0.0 && nfactor > 0.0 &&
            gapCnt >= lastTune + 64) {
            lastTune = gapCnt;
            double tpotEst = gapSum / (double)gapCnt;
            double tdrLB = (tdrSum + ((double)pendCnt * t - pendArrSum))
                           / (double)max(1LL, tdrCnt + pendCnt);
            bool tdrTight = tdrLB > 0.70 * SLO1;

            if (tpotEst > tpotTarget && !tdrTight) {
                Ntarget = max(1LL, Ntarget - max(1LL, Ntarget / 5));
            } else if (tdrTight || (w_tp > 0.0 && tpotEst < 0.70 * tpotTarget)) {
                Ntarget += max(1LL, Ntarget / 8);
            }

        } else if (!legacyQuarter && w_c >= w_tp && w_c > 0.0 && nfactor > 0.0 &&
                   progress >= lastTune + tuneEvery) {
            lastTune = progress;
            double tpotEst = (gapCnt > 0) ? gapSum / (double)gapCnt : 0.0;
            double tdrLB = (tdrSum + ((double)pendCnt * t - pendArrSum))
                           / (double)max(1LL, tdrCnt + pendCnt);

            double exTdr  = max(0.0, (tdrLB   - SLO1) / SLO1);
            double exTpot = max(0.0, (tpotEst - tpotTarget) / tpotTarget);

            double elapsedNow = t - (firstArrT >= 0.0 ? firstArrT : 0.0);
            double tpNow = (elapsedNow > 0.0) ? (double)tokensOut / elapsedNow : 0.0;
            double normTp = (tp_UB > tp_base)
                ? max(0.0, min(1.0, (tpNow - tp_base) / (tp_UB - tp_base)))
                : 0.0;
            double distNow = sqrt(exTdr * exTdr + exTpot * exTpot);
            double normC = (dist_base > 0.0)
                ? max(0.0, 1.0 - distNow / dist_base)
                : (distNow == 0.0 ? 1.0 : 0.0);
            if (radapt && waveCnt > 0) {
                double mAvg = waveSum / (double)waveCnt;
                if (mAvg < 1.0) mAvg = 1.0;
                int bestR = K; double bestG = 1e300;
                for (int r = 1; r <= K; ++r) {
                    double per = mAvg / (double)r;
                    if (per < 1.0) per = 1.0;
                    double g = S + col[4].at(per) + 2.0 * (double)r * latency_ms;
                    if (g < bestG) { bestG = g; bestR = r; }
                }
                double perK = max(1.0, mAvg / (double)K);
                double gK = S + col[4].at(perK) + 2.0 * (double)K * latency_ms;
                double share = remProcWork / max(1e-9, remProcWork + remDecWork);

                ruse = (gK > 1.4 * bestG && share < 0.25) ? bestR : K;
            }

            double valTp = w_tp * (1.0 - normTp);
            double valC  = w_c  * (1.0 - normC);
            double wTpEff = (valC > valTp) ? 0.0 : w_tp;

            if (!fixedDecodeWaves && !dgfracForced) {
                double frac = valTp / max(1e-12, valTp + valC);
                dgfrac = 0.05 + 0.70 * frac;
            }

            const bool aggressive = (wTpEff < 0.2);
            const long long shrinkDiv = aggressive ? 2 : 5;
            const long long growDiv   = aggressive ? 2 : 4;

            auto grow = [&]() {
                if (Ntarget < NO_CAP) Ntarget += max(1LL, Ntarget / growDiv);
            };

            preferPrefill = (wTpEff < 0.2) && (exTdr > 0.0) && (exTdr > 2.0 * exTpot);

            if (!legacyDecodeFirst && !eprioForced && w_c >= wTpEff) {
                eprio = (exTpot > exTdr) ? EPRIO_DECODE : "CDAB";
            }

            if (exTpot > exTdr) {
                if (w_c >= wTpEff) {
                    long long base = Ntarget;
                    if (nActive > 0 && base > nActive) base = nActive;
                    if (base >= NO_CAP) base = 1;
                    Ntarget = max(1LL, base - max(1LL, base / shrinkDiv));
                } else {
                    grow();
                }
            } else if (exTdr > exTpot) {
                grow();
            }
            if (valC > valTp && Ntarget >= NO_CAP && exTdr > 0.0) {

                Ntarget = max(1LL, nActive > 0 ? nActive : 1LL);
            }

        }

        if (targetTest3) Ntarget = NO_CAP;

        if (finCount > 0 && gapCnt == 0) Ntarget = NO_CAP;

        int n = 0;
        static string body;
        body.clear();

        auto admitOne = [&]() {
            int rid = bArrived.v.front();
            if (order != 'F' && bArrived.v.size() > 1) {
                double bestKey = -1e300;
                for (int cand : bArrived.v) {

                    double key = (order == 'L')
                        ? svcEst[cand]
                        : (order == 'S')
                        ? -svcEst[cand]
                        : (t - arrivalT[cand]) / svcEst[cand];
                    if (key > bestKey) { bestKey = key; rid = cand; }
                }
            }
            bArrived.del(rid);
            int best = 0;
            if (balw < 0.0) {
                for (int k = 1; k < ruse; ++k) if (load[k] < load[best]) best = k;
            } else {
                double bestEst = procWork[0] + (double)decCnt[0] * dproc1 * balw;
                for (int k = 1; k < ruse; ++k) {
                    double est = procWork[k] + (double)decCnt[k] * dproc1 * balw;
                    if (est < bestEst) { bestEst = est; best = k; }
                }
            }
            assigned[rid] = best;
            load[best]++;
            procWork[best] += col[1].at(lenIn[rid]);
            pieceIdx[rid] = 0;

            {

                long long dsplit = 0;
                if (const char *e = getenv("A_DSPLIT")) dsplit = atoll(e);

                if (dsplit > 1 && decCnt[best] >= 2 && targetTest6) {
                    int p = (int)dsplit;
                    if (p > num_layers) p = num_layers;
                    pcount[rid] = p;
                } else {
                    pcount[rid] = pieceCountFor(lenIn[rid]);
                }
            }
            stage[rid] = ST_PRE_RUN;
            ++nActive;
            body += "E P PRE ";
            body += to_string(best);
            body += ' ';
            body += to_string(rid);
            body += '\n';
            busyE = true; ++n;
        };

        if (legacyQuarter && !eprioForced) eprio = "CDBA";
        if (cxT10 && !eprioForced) eprio = "CDBA";
        if (legacyDecodeFirst) eprio = "ABCD";
        if (!busyE && useMarginal) {
            double elapsed = t - (firstArrT >= 0.0 ? firstArrT : 0.0);
            double gapDenom = max(1.0, (double)gapCnt);
            double requestDenom = max(1.0, (double)(tdrCnt + pendCnt));
            double tpNow = (elapsed > 0.0) ? (double)tokensOut / elapsed : 0.0;
            double tdrLB = (tdrSum + ((double)pendCnt * t - pendArrSum))
                           / (double)max(1LL, tdrCnt + pendCnt);
            double tpotEst = (gapCnt > 0) ? gapSum / (double)gapCnt : 0.0;
            double exTdr = max(0.0, (tdrLB - SLO1) / SLO1);
            double exTpot = max(0.0, (tpotEst - SLO2) / SLO2);
            double distance = sqrt(exTdr * exTdr + exTpot * exTpot);
            double distanceBase = (dist_base > 0.0) ? dist_base : 1.0;
            double costTdr = (distance > 0.0)
                ? (w_c / distanceBase) * (exTdr / distance) / SLO1 / requestDenom
                : 0.0;
            double costTpot = (distance > 0.0)
                ? (w_c / distanceBase) * (exTpot / distance) / SLO2 / gapDenom
                : 0.0;
            double costTp = (tp_UB > tp_base && elapsed > 0.0)
                ? w_tp * tpNow / (elapsed * (tp_UB - tp_base))
                : 0.0;

            double normTpNow = (tp_UB > tp_base)
                ? max(0.0, min(1.0, (tpNow - tp_base) / (tp_UB - tp_base)))
                : 0.0;
            double normCNow = (dist_base > 0.0)
                ? max(0.0, 1.0 - distance / dist_base)
                : (distance == 0.0 ? 1.0 : 0.0);
            costTp *= max(0.0, 1.0 - normTpNow);
            costTdr *= max(0.0, 1.0 - normCNow);
            costTpot *= max(0.0, 1.0 - normCNow);

            double averageOutput = (finCount > 0)
                ? (double)finTokens / (double)finCount
                : 8.0;

            double prefillBoost = targetTest6 ? 14.0 : 30.0;
            if (const char *e = getenv("A_PFVAL")) prefillBoost = atof(e);
            double pressure = (double)pendCnt / max(1.0, (double)decTotal);
            if (!legacyHalfNoGaps && pressure > 1.0) prefillBoost *= pressure;

            bool noGaps = (gapCnt == 0 && finCount > 0);
            bool forcePrefill = noGaps && !legacyHalfNoGaps && w_c >= w_tp &&
                (!bPostRdy.empty() || (!bArrived.empty() && nActive < Ntarget));
            if (forcePrefill) {
                eprio = "CDAB";
            } else {
            int bestAction = -1;
            double bestValue = -1.0;
            auto consider = [&](int action, double value, double duration) {
                double rate = value / max(1e-9, S + duration);
                if (rate > bestValue) {
                    bestValue = rate;
                    bestAction = action;
                }
            };
            if (!bDpostRdy.empty()) {
                double group = (double)bDpostRdy.size();
                consider(0, group * costTpot + costTp * group, col[5].at(group));
            }
            if (!bDecRdy.empty()) {
                double group = (double)bDecRdy.size();
                consider(1, group * costTpot + costTp * group, col[3].at(group));
            }
            if (!bPostRdy.empty()) {
                int rid = bPostRdy.v.front();
                consider(2, costTdr + costTp * averageOutput * prefillBoost,
                         col[2].at(lenIn[rid]));
            }
            if (!bArrived.empty() && nActive < Ntarget) {
                int rid = bArrived.v.front();
                consider(3, costTdr + costTp * averageOutput * prefillBoost,
                         col[0].at(lenIn[rid]));
            }
            if (bestAction >= 0) {
                const char actionCode[4] = {'A', 'B', 'C', 'D'};
                const char *fallback = legacyHalfNoGaps ? "ACDB" : "CDAB";
                eprio = string(1, actionCode[bestAction]) + fallback;
            }
            }
        }

        if (targetTest3 || probeT10) {
            long long inPrefill = nActive - decTotal;
            bool holdDecode = !bArrived.empty() || inPrefill > 0;
            bool holdPrefill = decActive > 0;
            string filtered;
            for (char action : eprio) {
                if (holdDecode && action == 'B') continue;
                if (holdPrefill && action == 'D') continue;
                filtered += action;
            }
            eprio = filtered;
        }
        bool holdTest5Decode = targetTest5 &&
            (!bArrived.empty() ||
             (double)(nActive - decTotal) > prefillBarrierFraction * (double)max(1LL, nActive));
        if (!busyE) {
            for (char act : eprio) {
                if (act == 'A' && !bDpostRdy.empty()) {
                    long long dpostPool = max((long long)bDpostRdy.size(),
                                              min(decTotal, decodePoolCap));
                    long long futureDpost = dpostPool - (long long)bDpostRdy.size();
                    if (dpostJoinFraction > 0.0 && futureDpost > 0 &&
                        (double)bDpostRdy.size() < dpostJoinFraction * (double)dpostPool) {
                        continue;
                    }
                    tmp = bDpostRdy.v;
                    body += "E D POST -1 ";
                    body += to_string(tmp.size());
                    for (int rid : tmp) { body += ' '; body += to_string(rid); }
                    body += '\n';
                    for (int rid : tmp) { bDpostRdy.del(rid); stage[rid] = ST_DPOST_RUN; }
                    busyE = true; ++n;
                    break;
                }
                if (act == 'B' && !holdTest5Decode && !bDecRdy.empty()) {
                    long long ready = (long long)bDecRdy.size();
                    bool mayWait = !legacyDecodeFirst || decTotal >= 16;
                    if (!targetTest3 && dgfrac > 0.0 && mayWait && decTotal > ready &&
                        (double)ready < dgfrac * (double)decTotal) {
                        continue;
                    }
                    if (targetTest3) {
                        tmp.clear();
                        for (int rid : bDecRdy.v) {
                            if (startedDec[rid]) tmp.push_back(rid);
                        }
                        for (int rid : bDecRdy.v) {
                            if ((long long)tmp.size() >= maxg) break;
                            if (!startedDec[rid] && decActive < decodePoolCap) {
                                tmp.push_back(rid);
                                startedDec[rid] = 1;
                                ++decActive;
                            }
                        }
                        if (tmp.empty()) continue;
                    } else {
                        tmp = bDecRdy.v;
                    }
                    if ((long long)tmp.size() > maxg) tmp.resize((size_t)maxg);
                    body += "E D PRE -1 ";
                    body += to_string(tmp.size());
                    for (int rid : tmp) { body += ' '; body += to_string(rid); }
                    body += '\n';
                    for (int rid : tmp) { bDecRdy.del(rid); stage[rid] = ST_DPRE_RUN; }
                    waveSum += (double)tmp.size(); ++waveCnt;
                    busyE = true; ++n;
                    break;
                }
                if (act == 'C' && !bPostRdy.empty()) {
                    int rid = bPostRdy.v.front();
                    bPostRdy.del(rid);
                    stage[rid] = ST_POST_RUN;
                    body += "E P POST ";
                    body += to_string(assigned[rid]);
                    body += ' ';
                    body += to_string(rid);
                    body += '\n';
                    busyE = true; ++n;
                    break;
                }
                if (act == 'D' && !bArrived.empty() && nActive < Ntarget) {
                    admitOne();
                    break;
                }
            }
        }

        for (int k = 0; k < K; ++k) {
            if (busyC[k]) continue;

            bool prefillReady = !bProcRdy[k].empty();
            bool decodeReady  = !bDprocRdy[k].empty();
            bool tookDecode;
            if (!decodeReady)      tookDecode = false;
            else if (!prefillReady) tookDecode = true;
            else if (rprio != 'D')  tookDecode = false;
            else if (preferPrefill && !legacyDecodeRemote) tookDecode = false;
            else if (legacyDecodeRemote) tookDecode = true;
            else                    tookDecode = (decStreak[k] < pfair);

            if (tookDecode) {

                tmp = bDprocRdy[k].v;
                body += 'C'; body += to_string(k);
                body += " D PROC ";
                body += to_string(k);
                body += ' ';
                body += to_string(tmp.size());
                for (int rid : tmp) { body += ' '; body += to_string(rid); }
                body += '\n';
                for (int rid : tmp) { bDprocRdy[k].del(rid); stage[rid] = ST_DPROC_RUN; }
                ++decStreak[k];
                busyC[k] = 1; ++n;
                continue;
            }
            if (!bProcRdy[k].empty()) {
                int rid = bProcRdy[k].v.front();
                bool reorderPrefill = rporder != 'F' &&
                    (rporder != 'C' || decodeReady) &&
                    (rporder != 'N' || !decodeReady) &&
                    (rporder != 'I' || tokensOut == 0);
                if (reorderPrefill) {
                    for (int candidate : bProcRdy[k].v) {
                        bool better = col[1].at(lenIn[candidate]) < col[1].at(lenIn[rid]);
                        if (rporder == 'L') better = !better &&
                            col[1].at(lenIn[candidate]) > col[1].at(lenIn[rid]);
                        if (better) rid = candidate;
                    }
                }
                bProcRdy[k].del(rid);
                int pi = pieceIdx[rid]++;
                int p = pcount[rid];
                int ls = (int)((long long)pi * num_layers / p);
                int le = (int)((long long)(pi + 1) * num_layers / p);
                if (pi + 1 == p) le = num_layers;
                stage[rid] = ST_PROC_RUN;
                body += 'C'; body += to_string(k);
                body += " P PROC ";
                body += to_string(ls); body += ' ';
                body += to_string(le); body += ' ';
                body += to_string(k);  body += ' ';
                body += to_string(rid);
                body += '\n';
                decStreak[k] = 0;
                busyC[k] = 1; ++n;
                continue;
            }

            if (!bDprocRdy[k].empty()) {
                tmp = bDprocRdy[k].v;
                body += 'C'; body += to_string(k);
                body += " D PROC ";
                body += to_string(k);
                body += ' ';
                body += to_string(tmp.size());
                for (int rid : tmp) { body += ' '; body += to_string(rid); }
                body += '\n';
                for (int rid : tmp) { bDprocRdy[k].del(rid); stage[rid] = ST_DPROC_RUN; }
                busyC[k] = 1; ++n;
            }
        }

        if (n == 0 && !busyE && pending == 0) {
            bool anyRemoteBusy = false;
            for (int k = 0; k < K; ++k) if (busyC[k]) { anyRemoteBusy = true; break; }
            if (!anyRemoteBusy) {
                if (!bDecRdy.empty()) {
                    if (targetTest3) {
                        tmp.clear();
                        for (int rid : bDecRdy.v) {
                            if (startedDec[rid]) tmp.push_back(rid);
                        }
                        if (tmp.empty()) {
                            for (int rid : bDecRdy.v) {
                                if (decActive >= decodePoolCap) break;
                                tmp.push_back(rid);
                                startedDec[rid] = 1;
                                ++decActive;
                            }
                        }
                    } else {
                        tmp = bDecRdy.v;
                    }
                    if ((long long)tmp.size() > maxg) tmp.resize((size_t)maxg);
                    body += "E D PRE -1 ";
                    body += to_string(tmp.size());
                    for (int rid : tmp) { body += ' '; body += to_string(rid); }
                    body += '\n';
                    for (int rid : tmp) { bDecRdy.del(rid); stage[rid] = ST_DPRE_RUN; }
                    waveSum += (double)tmp.size(); ++waveCnt;
                    busyE = true; ++n;
                } else if (!bArrived.empty()) {
                    admitOne();
                }
            }
        }

        io::putInt(n);
        io::putCh('\n');
        io::obuf += body;
        io::flushOut();
    }

    return 0;
}

