# Real trajectory graph examples

Each linked file shows the **same recorded trajectory twice**: its original
dependency graph, then the separate state/context graph ablation. Nodes/events
and operation/result text are preserved. Edge selection changes. Mermaid diagrams
and corresponding JSON are available.

| Task | Failed attempt | Successful attempt |
|---|---|---|
| 3 (additional case) | [2710c03e](task3_failed_2710c03e.md) | [0ab1d7a2](task3_success_0ab1d7a2.md) |
| 25 | [51d355a9](task25_failed_51d355a9.md) | [0f0f7358](task25_success_0f0f7358.md) |
| 40 (additional case) | [13e45831](task40_failed_13e45831.md) | [3d7bf865](task40_success_3d7bf865.md) |
| 48 | [058388c8](task48_failed_058388c8.md) | [07ec0bf6](task48_success_07ec0bf6.md) |

Cases are selected by task, outcome and smallest UUID, not by whether a method
scores well. A failed trajectory need not contain a verifier-labelled incorrect
executed action: failure can involve omissions or unverified policy/message
errors. These diagrams illustrate representation, not accuracy.

The new graph prefers the latest prior non-error tool observation containing an
argument value and gives messages links to the latest user turn and observation.
It does not infer complete causal reasoning. Only predictor adjacency changes;
the original C4 matcher and supervision are preserved.

In the core test, this ablation improves tool-step macro AUROC from approximately
0.628 to 0.727, while reducing top-1 error localization from 0.725 to 0.608.
It should therefore remain a separately reported experiment rather than be
declared an unconditional improvement.
