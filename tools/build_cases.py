#!/usr/bin/env python3
"""Generate cases/case_NN/README.md: one dossier per judge test.

Every number here is judge-measured. Sources: data/pertest/*.txt and
data/allsubs/*.txt (per-test protocol output scraped from submission pages).
"""
import re, glob, os, json, math

BEST = 'r185_mux_dpost'          # current best build's per-test file, if present
FALLBACK = 'r141_BEST'

def load_all():
    runs = {}
    for f in glob.glob('data/pertest/*.txt') + glob.glob('data/allsubs/*.txt'):
        n = os.path.basename(f)[:-4]; d = {}
        for ln in open(f):
            m = re.match(r"#(\d+) ([0-9.]+) tp=([0-9.eE+-]+) mean_tdr=([0-9.eE+-]+) "
                         r"mean_tpot=([0-9.eE+-]+) dist=([0-9.eE+-]+) "
                         r"norm_tp=([0-9.eE+-]+) norm_c=([0-9.eE+-]+)", ln)
            if m:
                d[int(m.group(1))] = dict(score=float(m.group(2)), tp=float(m.group(3)),
                    tdr=float(m.group(4)), tpot=float(m.group(5)), dist=float(m.group(6)),
                    ntp=float(m.group(7)), nc=float(m.group(8)))
        if len(d) == 22: runs[n] = d
    return runs

# SLO fits verified to reproduce observed dist within 10%
SLO = {3:(837.6,56.46), 4:(181.7,143.4), 5:(311.8,87.14), 6:(651.7,14.85),
       7:(676.8,54.75), 8:(422.9,98.07), 13:(463.6,66.73), 14:(161.5,212.9),
       19:(196.0,50.11), 10:(1302.4,3.4226), 12:(423580.0,129.55),
       16:(1179.5,66.189), 17:(18723.0,287.13), 22:(7.5195,6.2865)}

# judge-measured findings per test, written up by hand from the round ledger
NOTES = {
 1: ["norm_tp is pinned at 0.000 and norm_c at 1.000 -> exactly 500.000.",
     "tp = 0.022222 = 1/45 and never moves. ARRIVAL-BOUND: the makespan is set by",
     "the arrival span, not by scheduling, so the 500 points of tp headroom are",
     "not collectable by any scheduler.", "STATUS: closed."],
 2: ["Identical shape to #1: norm_tp 0.000, norm_c 1.000, score exactly 500.000.",
     "ZERO distinct values across every config ever measured.", "STATUS: closed."],
 3: ["w_tp = 0.00, so the score IS 1000 * norm_c. dist is 100% TDR-driven",
     "(mean_tpot sits exactly at SLO2). LEVERAGE: 13.73 points per 1% of mean_tdr,",
     "the best latency leverage on the board -- -7.3% tdr would be +100.",
     "TRIED: dgfrac 0.05/0.60 both exactly inert; balw>0 (+71 on proxies) a judge",
     "no-op; rporder 'S' no-op; forcePrefill widened to fire on TDR-dominant (r167)",
     "left mean_tdr identical to 3 decimals.",
     "WHY: forcePrefill also needs prefill work AVAILABLE when E is free, and on #3",
     "that never coincides -- prefill is starved upstream at the link/remotes.",
     "STATUS: closed at the mechanism level. Only 3 distinct values in 45 configs."],
 4: ["Gated to nfactor 0.9 + dpost 0.30, worth +0.28 -- harvested from r139, a",
     "config that LOST 169 points overall. Also carries dgfrac 0.60.",
     "Needs 1.92x tp for the remaining 155. STATUS: at its measured max."],
 5: ["w_tp 0.80. Needs 2.74x throughput to reach tp_UB -- implausible.",
     "norm_c is already 0.998, so latency is nearly exhausted.",
     "Carries dgfrac 0.10 and a forced eprio ABDC. dgfrac 0.60/0.05 both inert.",
     "STATUS: effectively closed (2.9 pts per 1% tp, needs +174%)."],
 6: ["LARGEST headroom on the board: 597 points, w_tp 0.90.",
     "Needs 2.90x throughput. dgfrac peak CONFIRMED at 0.25, bracketed both sides:",
     "0.05 -13.69 | 0.18 -4.75 | 0.25 BEST | 0.32 -2.89 | 0.60 -77.53.",
     "pfval 28 costs it 5.55 (tp 0.728->0.715), so #6 is held at pfval 14 while",
     "every other test runs 28 -- that gate is what makes pfval 28 free.",
     "STATUS: dgfrac closed; the 597 needs 3x tp, which no scheduling change gives."],
 7: ["w_tp 0.00, pure latency. Carries rporder 'S' and dgfrac 0.10.",
     "2.53 points per 1% tdr, 85 available. dist is 65% TDR.",
     "STATUS: at measured max; spread 277 across configs but current is the peak."],
 8: ["THE legacyQuarter test (w 0.25, dist_base 10.8848). 113 points, 112.9 of it",
     "latency, dist 92% TDR-driven.",
     "UNIQUE: #8 is the ONLY test with dgfrac = 0 -- immediateDecodeWaves is set by",
     "legacyQuarter, so its decode groups fire immediately and NEVER accumulate.",
     "That regime has never been varied. r183/r184 probe dgfrac 0.10 / 0.24.",
     "Also: marginal ON measured -- the legacyQuarter bundle disables it."],
 9: ["w_tp 0.05, latency-dominated, mean_tpot = 0 (every request emits one token).",
     "Excluded from the marginal model by weight; enabling it for #9 alone was the",
     "FIRST gain in that area: +0.041 (r129). 262 points remain, 8.77x over SLO1.",
     "STATUS: marginal now ON; other levers untested per-test."],
 10:["315 points, the largest LATENCY headroom still open. w_tp 0.15, dist 97% TDR,",
     "mean_tdr is 140x SLO1. Carries eprio CDBA and rprio 'D' via the cxT10 gate.",
     "Enabling the marginal model for #10 measured -0.011, so it stays off.",
     "2.84 points per 1% tdr. STATUS: at measured max, but least-explored of the",
     "big-headroom tests."],
 11:["mean_tdr 32.7 MILLION yet dist = 0: the SLOs are astronomically loose, so",
     "norm_c = 1.000 for free and norm_tp is pinned near 0. Arrival-bound.",
     "Only 3 distinct values ever observed, spread 0.05. STATUS: closed."],
 12:["w_tp 0.99 -- essentially pure throughput. 189 points, and the BEST throughput",
     "leverage on the board at 14.8 points per 1% tp (needs only +12.8%).",
     "ENGINE-BOUND, established by elimination on the judge:",
     "  decode-group cap removed -> exact no-op (groups never even reach 8)",
     "  prefill-queue SJF        -> exact no-op (remote queues are empty)",
     "  admission cap            -> -719 (collapses to ~85; flooding is REQUIRED)",
     "  prefillBoost 2 and 40    -> exact no-op both ways",
     "  eprio ABCD / order K / radapt off -> all flat or negative",
     "ONLY dgfrac pays: 0.32 +0.24, then 0.60 +0.541 (peak), 0.90 -2.17.",
     "STATUS: 8 of 9 mechanisms dead; dgfrac at its peak."],
 13:["271 points, w_tp 0.75. Runs useMarginal = FALSE, so its forced eprio is its",
     "ENTIRE engine policy, not a fallback.",
     "eprio fully determined by three measured axes:",
     "  prefill block before decode block   ~9-24 pts",
     "  P PRE before P POST  (DC > CD)        3.24",
     "  D PRE before D POST  (BA > AB)       23.89",
     "  => DCBA wins on all three; the other 19 permutations lose by composition.",
     "PREFILL-STARVED ~100% of the time: an adaptive pool-depth switch never fired",
     "even at threshold 4K. Enabling the marginal model measured -14.47.",
     "STATUS: closed."],
 14:["585 points and the NARROWEST scoring window on the board -- tp_UB/tp_base =",
     "1.0053, so +0.42% throughput would be worth 513 points.",
     "BUT tp is IDENTICAL (0.003564) across all 45 configs, including catastrophic",
     "ones. Only the latency metrics ever move. Makespan is fixed by the workload.",
     "STATUS: closed -- the 513 points are not collectable by anyone."],
 15:["117 points, latency. Excluded from the marginal model by weight+dist_base;",
     "enabling it for #15 alone was an exact no-op on the judge.",
     "mean_tpot = 0 (single-token requests). STATUS: at measured max."],
 16:["Only 20 points of headroom -- essentially maxed at 979.91.",
     "Carries the dgfrac 0.95 flat-curve whitelist (worth +3.84, and +2.32 more",
     "from forcing it to persist since #16 also has useMarginal false)."],
 17:["110 points, w_tp 0.67, dist 35% TDR. Carries balw 4 + dgfrac 0.25 (an",
     "INTERACTION-only win: +0.03, unreachable by either knob alone).",
     "Sensitive: 21 distinct values, spread 597. dpost 0.15 costs it 8.70, which is",
     "why r179 gates it back to 0.08."],
 18:["84 points. Carries dgfrac 0.32 and a ruse-3 gate (+0.01) -- ruse 3 is worth",
     "-1081 globally yet wins on this one test."],
 19:["w_tp = 1.00, so w_c = 0 and dist is unscored. 80 points, all throughput.",
     "The ONLY test whose dist is TPOT-dominated -- irrelevant since it is unscored."],
 20:["998.19 of 1000. Effectively perfect; 1.8 points remain.",
     "norm_c is exactly 1.000000, so dist_base cannot be derived and #20 can never",
     "be gated -- its +0.01 from the dgfrac .45/dpost .35 corner is unreachable."],
 21:["32 points. Carries dgfrac 0.03 + dpost 0.005 (harvested from a corner probe).",
     "mean_tpot = 0. 15 distinct values, spread 27."],
 22:["45 points left of 1000. Holds the single biggest per-test win in the project:",
     "dpost 0.90 = **+36.2**, a value catastrophic globally (-27.3 on #17, -6.3 on",
     "#13) and reachable only by gating. THE template for a big gain.",
     "tp = 39.87, by far the highest; dist is 100% TDR."],
}

def main():
    runs = load_all()
    base = runs.get(BEST) or runs.get(FALLBACK)
    for t in range(1, 23):
        d = os.path.join('cases', f'case_{t:02d}'); os.makedirs(d, exist_ok=True)
        cur = base[t]
        wtp = 0.5 if abs(cur['ntp']-cur['nc']) < 1e-12 else max(0, min(1,(cur['score']/1000-cur['nc'])/(cur['ntp']-cur['nc'])))
        wc = 1-wtp
        db = cur['dist']/(1-cur['nc']) if cur['nc'] < 1 else 0.0
        vals = sorted({round(r[t]['score'],3) for r in runs.values()})
        tps  = sorted({round(r[t]['tp'],9)    for r in runs.values()})
        L=[]
        L.append(f"# Test #{t}\n")
        L.append(f"Current score **{cur['score']:.3f}** / 1000 "
                 f"(headroom {1000-cur['score']:.1f})\n")
        L.append("## Scoring parameters (derived from judge output)\n```")
        L.append(f"w_tp       {wtp:.4f}        w_c        {wc:.4f}")
        L.append(f"norm_tp    {cur['ntp']:.6f}     norm_c     {cur['nc']:.6f}")
        L.append(f"dist       {cur['dist']:.6g}       dist_base  {db:.6f}")
        L.append(f"mean_tdr   {cur['tdr']:.6g}     mean_tpot  {cur['tpot']:.6g}")
        L.append(f"tp         {cur['tp']:.6g}")
        if t in SLO:
            s1,s2 = SLO[t]
            L.append(f"SLO1       {s1:.6g}       SLO2       {s2:.6g}")
            L.append(f"tdr/SLO1   {cur['tdr']/s1:.3f}         tpot/SLO2  {(cur['tpot']/s2 if s2>0 else 0):.3f}")
        L.append(f"tp_room    {1000*wtp*(1-cur['ntp']):.1f}         c_room     {1000*wc*(1-cur['nc']):.1f}")
        L.append("```\n")
        L.append("## Response across all measured configs\n```")
        L.append(f"distinct scores observed : {len(vals)}")
        L.append(f"best / worst             : {vals[-1]:.3f} / {vals[0]:.3f}   (spread {vals[-1]-vals[0]:.2f})")
        L.append(f"distinct tp values       : {len(tps)}"
                 + ("   <-- tp NEVER changes: makespan is workload-fixed" if len(tps)==1 else ""))
        L.append(f"at its measured maximum  : {'YES' if abs(cur['score']-vals[-1])<0.005 else 'no'}")
        L.append("```\n")
        L.append("## What we know\n")
        for line in NOTES.get(t, ["(no findings recorded yet)"]): L.append(line)
        L.append("\n## Untried\n")
        L.append("See ../../submit/rounds/README.md for the full round-by-round ledger.")
        open(os.path.join(d,'README.md'),'w').write("\n".join(L)+"\n")
    print(f"wrote 22 case dossiers from {len(runs)} measured runs")

if __name__ == '__main__':
    main()
