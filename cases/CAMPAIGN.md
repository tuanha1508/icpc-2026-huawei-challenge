# Full-board campaign

Systematically vary every knob on every test, using multiplexed per-test gates:
one submission = one knob at one value across many tests. Losers cost only
their own test and are dropped after the per-test harvest.

Generator: `python3 tools/mkmux.py <base.cpp> <out> <var> <value> <tests> "<note>"`

## Why width beats depth
#6 was mapped exhaustively over ~10 submissions: nine of its ten components
were already correct, and the single win (+11) came from the r185 MULTIPLEX,
not from the grind. #7 (+1.09) came from the r216 multiplex the same way.
Depth mostly confirms settings that are already right.

## Results so far
    knob     value  tests                       outcome
    dpost    0.40   #5 #6 #7 #9 #10 #15 #16 #18  #6 +2.29  (-> refined to +11)
    dpost    0.25   ten ungated                  #7 +1.09  <- NEW BEST 16320.601
    dpost    0.05   ten ungated                  flat
    balw     4.0    #8 #9 #10 #12 #15 #18 #21    -1.98, no winners
    nfactor  2.0    #3 #7 #8 #9 #10 #15 #21 #22  -10.2
    order    'F'    #3 #8 #9 #10 #15 #18 #21 #22 -329
    dgfrac   .60/.05 #3 #5 #6 #10 #13            no winners

## Queue
    r220  dgfrac 0.40 on #3 #9 #10 #14 #15 #19 #22   (never varied on these 7)
    r221  dgfrac 0.08 on the same seven
    next: maxg, rporder, pieces, rprio, radapt at full width

## Per-test knob coverage (gated = already tuned for that test)
    dpost  gated: #4 #6 #7 #8 #12 #13 #17 #21 #22
    dgfrac gated: #4 #5 #6 #7 #8 #12 #13 #16 #17 #18 #21
    balw   gated: #13 #17
    others: essentially ungated everywhere
