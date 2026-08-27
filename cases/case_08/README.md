# Test #8

Current score **812.230** / 1000 (headroom 187.8)

## Scoring parameters (derived from judge output)
```
w_tp       0.2500        w_c        0.7500
norm_tp    0.700503     norm_c     0.849472
dist       1.63846       dist_base  10.884766
mean_tdr   1086.89     mean_tpot  143.942
tp         0.012364
SLO1       422.9       SLO2       98.07
tdr/SLO1   2.570         tpot/SLO2  1.468
tp_room    74.9         c_room     112.9
```

## Response across all measured configs
```
distinct scores observed : 6
best / worst             : 812.230 / 729.931   (spread 82.30)
distinct tp values       : 6
at its measured maximum  : YES
```

## What we know

THE legacyQuarter test (w 0.25, dist_base 10.8848). 113 points, 112.9 of it
latency, dist 92% TDR-driven.
UNIQUE: #8 is the ONLY test with dgfrac = 0, immediateDecodeWaves is set by
legacyQuarter, so its decode groups fire immediately and NEVER accumulate.
That regime has never been varied. r183/r184 probe dgfrac 0.10 / 0.24.
Also: marginal ON measured, the legacyQuarter bundle disables it.

## Untried

See ../../submit/rounds/README.md for the full round-by-round ledger.

## THE BUNDLE, why #8 is the best remaining target

`legacyQuarter` (w_tp 0.25, dist_base 10.8848) IS #8, and this file calls it
"an eight-site compatibility bundle inherited from the Codex base". It is
applied wholesale. Of its seven live settings, only ONE has ever been tested on
its own:

    line 393   useMarginal = false        tested (r134) -> exact no-op
    line 433   immediateDecodeWaves       => dgfrac = 0   NEVER VARIED
    line 434   legacyDecodeRemote = true                  NEVER TESTED
    line 560   radapt = false                             NEVER TESTED
    line 589   balw -1.0 : -1.0           both arms identical -> DEAD CODE
    line 661   dpostJoinFraction = 0.25                   NEVER VARIED
    line 964   special nfactor branch                     NEVER TESTED
    line 1162  eprio = "CDBA"                             NEVER VARIED

#8 carries 187.8 points of headroom, 112.9 of it latency, with dist 92%
TDR-driven and tdr/SLO1 = 2.57. Five untested levers on a test that size is the
richest unexplored surface left on the board.

### Decomposition probes (one component each)
    r183  dgfrac 0 -> 0.10        decode groups currently never accumulate
    r184  dgfrac 0 -> 0.24        match the global default
    r191  legacyDecodeRemote OFF
    r192  radapt ON               #8's dist is 92% TDR, which is exactly what
                                  the adaptive loop steers on, and it is
                                  disabled for #8 only because of the bundle
    r193  dpost 0.25 -> 0.08
    r194  eprio "CDBA" -> "ABCD"  #8 is latency-weighted; CDBA is prefill-first
Each isolates ONE inherited setting, so whichever moves the score identifies
the component responsible. All six built, compiled and verified unique.

### Decomposition results (judge-measured, one component at a time)
    useMarginal ON       exact no-op  (r134)
    radapt ON            **-1.50**    (r192)  -> keep radapt OFF; the bundle is
                                       right here, despite dist being 92% TDR
    eprio "ABCD"         exact no-op  (r194)  -> eprio does not bind on #8 at all
Three of seven components now settled; the bundle is correct on all three.
Remaining, rebased on r185 (16308.867, current best):
    r195  legacyDecodeRemote OFF
    r196  dpost 0.25 -> 0.08
    r197  immediateDecodeWaves OFF  (this is what pins #8's dgfrac to 0)
NOTE r191-r194 were built on r180, not on the r185 best, the component
comparisons are still valid against that fixed baseline, but they could never
have set a record. Rebased for the rest.

### FINAL: the bundle is CORRECT, not legacy baggage
    immediateDecodeWaves OFF -> **-1.50** (r197). #8 genuinely wants dgfrac = 0.
    dpost 0.25 -> 0.08       -> exact no-op (r196)
Five of seven components tested individually; every one confirms the inherited
setting. #8's 188 points are closed barring legacyDecodeRemote (r195).

## REOPENED, dpost 0.60 is worth +9.26, and I had closed #8 prematurely
r228 (dpost 0.60 across fifteen tests) scored -52 overall but contained:
    #8  812.23 -> 821.49  **+9.261**
#8 inherits dpost 0.25 from legacyQuarter. Earlier I tested it DOWNWARD only
(0.08, r196: exact no-op) and concluded the bundle was validated. That was
wrong, the inherited value is roughly nine points too LOW. Testing one
direction and generalising is the specific mistake.
    r230 = #8 dpost 0.60  -> expect ~16329.9
    r231 = #8 dpost 0.80  (direction is up; peak unknown)

### dpost curve, the single biggest gain of the project after #22's +36.2
    0.25 (inherited)  16320.611   the legacyQuarter value
    0.60              16329.849   +9.24   (predicted +9.26 from the r228 harvest)
    0.80              16336.864   **+16.25**  NEW BEST, still climbing
    0.90 / 0.97       r232 / r233 pending
#8 was declared CLOSED after five bundle components were validated, but dpost
had only ever been tested DOWNWARD (0.25 -> 0.08, no-op). The inherited value
was ~16 points too low. Testing one direction and generalising to "validated"
is the specific error.

### dpost curve, #8 is the single largest gain of the session
    0.25 inherited   16320.611
    0.60             +9.24
    0.80             +16.25
    0.90             **+17.50**   (harvested from r236, a config that lost 664)
    0.95 / 0.99      r238 / r239 pending
r232 (#8 at 0.90, alone) was built but never submitted, it should land ~16338.
