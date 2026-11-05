# Phase 2 results demo — both reference settings

Open `dist/index.html` in Chrome/Safari, or double-click **Open Demo.command**.
There is also a launcher on your Desktop: **Open Stepwise Demo.command**.
The complete demo runs from local files. No server, VPN, model API or internet
connection is required after export. It makes no new model predictions.

The default page compares **3–5 and 3–17 references** on the same frozen dataset.
Use **Active experiment** at the top to switch every result, run score, reference
set, MCS target, diagnostic and training curve. Each setting has 24 checkpoints;
there are 48 across both experiments. The cap-17 training bank actually contains
3–16 eligible successful references per query, not a fixed 17.

## Demonstration route

1. **3–5 vs 3–17:** show both metric tables and the main findings. GIBS tool
   localization increases from 34.1% to 40.7%; C4 decreases from 52.2% to 49.3%.
   The page provides five genuine seed-7 cases: a GIBS success, a NIBS win, a
   GIBS miss under both settings, a GIBS improvement, and a C4 regression.
2. **Results overview:** show all 50 tasks and 1,000 trajectories; switch between
   AUROC and first-error Top-1, tool/all-agent scope, shared/all-learned coverage,
   and individual seeds or means. Undefined metrics remain N/A.
3. **Trajectory explorer:** select a task/run or a suggested illustrative case.
   Inspect actual saved scores, the first verifier-labelled tool error, graph,
   transcript, successful reference graphs and genuine MCS target masks.
   Each selected step has a table comparing both settings' saved predictions.
   MCS inspection compares both targets and their actual support counts, and
   displays the query and successful reference graphs. Switch the active
   experiment to change reference sets while staying on the same execution.
   Preset descriptions use tool-only first-error rankings at seed 7; the step
   table also includes messages. These post-hoc cases do not replace full metrics.
4. **Why these results?:** distinguish measured protocol/target facts from
   hypotheses. Inspect the 860-query direct-teacher diagnostic and saved loss
   curves. This diagnostic is a separate population from the primary 911-query
   comparison; teachers have reference access and are not independent truth.
5. **Method walkthrough:** six plain-English steps, the 1,000/860/911 counts,
   metric definitions and an interactive, clearly illustrative MCS calculation.
   Copy the concise summary for your presentation.

The same page includes a 15-stage detailed explanation, also available in
`GIBS_WORKED_EXAMPLE.md`. Its names, match decisions and predictions are clearly
illustrative; the explorer and diagnostic panels use actual recorded artifacts.
That detailed teaching example retains explicitly labelled historical cap-5
numbers; the active experiment controls the actual explorer and diagnostics.

`DEMO_REPORT.md` provides the comparison, main insights, five real case IDs,
exact first-error scores/ranks and MCS targets. It is downloadable in the UI.

## What the UI does and does not establish

All displayed model scores come from saved held-out predictions of the completed
experiment. GCNs were trained, and their checkpoint histories are genuine.
Reference-based target inspection is post-hoc; reference graphs did not enter
the held-out forward pass. No scores or test labels are changed by this UI.

This is a read-only benchmark-results prototype. It is not a deployed live
airline assistant or a completed human-in-the-loop review system. Independent
review is pending, and most steps are unverified. Cosine and learned support
scores are not demonstrated calibrated correctness probabilities. C4 and the
automatic verifier share structured-field assumptions.

## Rebuild from the completed artifacts

From the project root:

```bash
.venv/bin/python demo_ui/export_data.py
.venv/bin/python demo_ui/build_comparison.py
python3 demo_ui/build_walkthrough.py
node --check demo_ui/dist/assets/app.js
python3 demo_ui/verify_demo.py
```

The exporter reads only the fresh experiment, whitelists transcript fields,
checks the frozen input hash, and scans for known local credential values.
It does not export raw provider settings or read unrelated historical results.
The static assets support direct offline opening as well as an ordinary web host.

`dist/data/cap5/` and `dist/data/cap17/` each contain a separately labelled
`diagnostics.json`, `dashboard.json`, reports and lazy-loaded run assets.
Each dashboard has the source summary/hashes, 24 histories, 50 tasks and 1,000
run records. The main comparison and verified case evidence are in
`dist/data/comparison.json`; its downloadable report is `COMPARISON_REPORT.md`.
Each run's lazy-loaded
`.js` asset contains whitelisted messages, step scores, its graph and MCS maps.

Browser QA uses the system Python's existing Playwright/Chromium installation.
The demo itself needs only a browser. The core experiment and saved artifacts
are unchanged. This UI has not been published to a hosting service.

Verification compares every exported learned prediction, teacher mask and MCS
pair with its saved source, validates the five example ranking claims, checks
the protected original experiment, and exercises both settings in desktop,
mobile, offline and HTTP modes.
