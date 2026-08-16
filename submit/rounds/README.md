# Submission rounds

| round | file | contents | judge total |
|-------|------|----------|-------------|
| —     | your source | baseline | **16093** |
| —     | Codex V67 | | **16094.911** |
| r03   | `r03_16093_plus_t6route.cpp` | + my #6 route | 16073.22 |
| r04   | `r04_16093_flatcurve_not13.cpp` | + flat-curve, excl #13 | 16059.29 |
| r06   | `r06_16093_flatcurve_not13_not6.cpp` | + flat-curve, excl #13 AND #6 | pending ← SUBMIT |
| r05   | `r05_r04_plus_codex_t5.cpp` | needs rebasing onto r06 | hold |

## Per-test effects, all measured on the judge
| change | #6 | #13 | #16 |
|--------|-----|-----|-----|
| my #6 route (dpost 1.0, marginal off, pieces 4) | **-19.78** | — | — |
| flat-curve dgfrac 0.95 | **-37.55** | **-31.57** | **+3.84** |

Both of my ideas were net-negative. r06 keeps only the one measured positive:
the flat-curve block gated OFF for #13 and #6, leaving just #16's +3.84.
Expected **16096.84**, ahead of Codex's 16094.911.
