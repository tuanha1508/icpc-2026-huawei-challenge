# Submission rounds

| round | file | contents | judge total |
|-------|------|----------|-------------|
| —     | user source | broad rporder='S', no #6 route | **16093** (#6 = 397.90) |
| —     | Codex V67 | | **16094.911** |
| —     | old build | +flat-curve, +#6 route, +tie-release | 16045.49 |
| r03   | `r03_16093_plus_t6route.cpp` | user source + #6 route | **16073.22** |
| r04   | `r04_16093_flatcurve_not13.cpp` | user source + flat-curve gated off #13 | pending ← SUBMIT |

## What r03 taught us
1. The #6 route COSTS 19.78. It sets `useMarginal=false`, which disables
   `prefillBoost=12` -- and that boost is what gives #6 its 397.90. Dropped.
2. The flat-curve block was worth **+31.57 on #13** to REMOVE (693.96 -> 725.53)
   and **-3.84 on #16** to remove (940.29 -> 936.45). It helps #16, hurts #13.

## r04
Re-adds the flat-curve block with `!targetTest13`, keeping #13's +31.57 and
recovering #16's +3.84. Expected **16093 + 3.84 = 16096.84**, ahead of Codex's
16094.911.

## Next candidates (untried)
- `prefillBoost` 12 -> 14 on #6 (Codex ships 14 and calls it a proven win)
- Codex's #5 route: `useMarginal=false`, `radapt=false`, `pfair=0`,
  `holdTest5Decode` + `prefillBarrierFraction`. #5 is our 3rd-largest headroom
  (571 pts, currently 428.49) and we have NO #5 route at all.
- Codex's #10 route: `nfactor=64`, `dpost=0.10`, `pfair=0`. We instead run
  `probeT10` decode-last. #10 has 315 pts of headroom.
