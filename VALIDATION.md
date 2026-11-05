# Publication validation — November 5, 2026

- `.venv/bin/python -m pytest -q gibs/tests nibs/tests`: **216 passed, 1 skipped**, completed in 557.05 seconds.
- `python3 demo_ui/verify_demo.py`: passed for both reference settings, all five real example claims, desktop/mobile layouts, direct offline opening and HTTP serving; no JavaScript errors.
- The UI validation matched every exported learned prediction, teacher mask and pair mapping to the corresponding saved source artifact: 8,456 MCS mappings for cap 5 and 20,102 for cap 17.
- The completed cap-5 baseline protection hashes passed verification.
- `node --check demo_ui/dist/assets/app.js`: passed.
- Credential checks and any publication-copy redactions are recorded in `PUBLICATION_AUDIT.json`.

These are software/artifact checks. Independent human review of step correctness remains pending.
