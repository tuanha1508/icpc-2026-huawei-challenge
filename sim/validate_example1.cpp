#include "sim_core.hpp"
#include <cstdio>
#include <cmath>
int main() {
    // Example 1 from docs/statement/EXAMPLES.md
    sim::Model m;
    m.init(/*K=*/1, /*S=*/1.0, /*latency_ms=*/2.0, /*bw=*/1.0, /*bpt=*/125000);
    m.col[0].pts = {{1,3.0}};  m.col[1].pts = {{4,10.0}}; m.col[2].pts = {{1,2.0}};
    m.col[3].pts = {{1,1.0}};  m.col[4].pts = {{1,4.0}};  m.col[5].pts = {{1,1.0}};
    for (int i=0;i<6;++i) m.col[i].finalize();

    struct { const char* name; double got, want; } chk[16]; int n=0;
    double t = 0.0;
    t = m.edge.run(t, m.S, m.col[0].at(4));       chk[n++] = {"P PRE done",   t, 4.0};
    t = m.up.send(t, 4);                          chk[n++] = {"UP done",      t, 10.0};
    t = m.remote[0].run(t, m.S, m.col[1].at(4));  chk[n++] = {"P PROC done",  t, 21.0};
    t = m.down.send(t, 4);                        chk[n++] = {"DOWN done",    t, 27.0};
    t = m.edge.run(t, m.S, m.col[2].at(4));       chk[n++] = {"P POST done",  t, 30.0};
    t = m.edge.run(t, m.S, m.col[3].at(1));       chk[n++] = {"D PRE done",   t, 32.0};
    t = m.up.send(t, 1);                          chk[n++] = {"UP dec done",  t, 35.0};
    t = m.remote[0].run(t, m.S, m.col[4].at(1));  chk[n++] = {"D PROC done",  t, 40.0};
    t = m.down.send(t, 1);                        chk[n++] = {"DOWN dec done",t, 43.0};
    t = m.edge.run(t, m.S, m.col[5].at(1));       chk[n++] = {"D POST/token", t, 45.0};

    int bad = 0;
    for (int i=0;i<n;++i) {
        bool ok = std::fabs(chk[i].got - chk[i].want) < 1e-9;
        if (!ok) ++bad;
        printf("  %-14s got %8.3f  want %8.3f  %s\n",
               chk[i].name, chk[i].got, chk[i].want, ok ? "OK" : "MISMATCH");
    }
    printf("%s: %d/%d timestamps exact\n", bad ? "FAIL" : "PASS", n-bad, n);
    return bad ? 1 : 0;
}
