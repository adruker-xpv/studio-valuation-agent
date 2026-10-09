# XPV onboarding - changelog

## 13.0.0 - bounded, checkpointed AI-led investigation across any number of workbooks
Prompted by Test2 (five real workbooks: the reading was right; the extractor timed out before saving anything).
- **Reader (`xlsx_evidence.py`, replaces `read_workbook.py`):** streams each sheet's XML and keeps only populated cells, so inflated used
  ranges and formatted-empty cells cost nothing (the 12.0 reader did not finish a synthetic inflated sheet in 25 s; the new one reads
  five workbooks in under 1 s). Formulas and saved values together; shared, array and data-table formulas; hidden and very-hidden
  sheets, hidden rows/columns, merged ranges, comments, defined names; links to other files resolved to source ids (unsupplied files get
  X ids, with their cached values). Targeted commands: `cells` (with headers and row labels), `sheet`, `find` (a match is not a link),
  `refs --from/--to` across workbooks. Time budget per call with an explicit STOPPED line; per-sheet cache.
- **Checkpoints (`checkpoint.py`):** seven stages (sources, roles, chain, upstream, downstream, questions, validation), validated,
  append-only, with size and item caps; `extraction.json` rebuilt after every save (provisional from stage 3); `status` names the next
  stage, its goal and its budget; a fresh call resumes exactly.
- **Schema 3:** sources with roles and fingerprints, the chain, the 12-month window wherever it really is, key provenance and downstream
  edges with one of seven evidence classes, discrepancies, rejected rivals, deferred areas, open questions, material inputs.
- **verify (`verify.py`, replaces `referee.py`):** narrow claim checks across workbooks - integrity, chain arithmetic, window, every edge
  by its class (numeric equality never promoted to a link), discrepancies confirmed as real, the fund link (a preserved discrepancy
  passes). The 12.0 exhaustive coverage gate is removed; untraced typed inputs are reported for information only.
- **Reviewer:** phase 1 bottom-up and staged, capped (20 key edges, 12 challenges); phase 2 settles reconcile's contested list with typed
  findings and checkable claims.
- **Reconcile:** compares by fingerprint and cell; `--compare-only` for phase 2; measures reviewer value (different path, missed rivals,
  weak provenance, unsupported assumptions, evidence-backed contradictions, reviewer claims that failed); new analyst workbook tabs.
- **Extractor runs in two passes** (EXTRACTION = stages 1-3, RESUME = the rest); the same RESUME recovers from any timeout.
- **Docs:** `MANUAL_RUN_PROMPTS.md`, `TEST2_REGRESSION.md`; playbook adds multi-workbook provenance, evidence classes, materiality,
  discrepancies as results.
- **Test bench:** synthetic five-workbook set T1 (deterministic generator), the four 12.0 trial references migrated to schema 3, decoy
  tests kept; tests 38 -> 84.


## 12.0.0 - two providers, everything that uses the valuation, file integrity
- **Models:** Extractor on Claude Opus 5; Reviewer on GPT-6 Astra (a different provider, so mistakes are less likely to
  coincide), to be confirmed against Opus 5 in the trial. Models pinned, never "Default". GPT-5.6 Sol is not offered for
  Canada in the GitHub Copilot harness (only GPT-5.6 Reasoning, experimental, US early access).
- **Referee 12.0:** coverage now also requires every formula that uses the chain (sensitivity tables, comps cross-checks,
  MOIC, report rows, quarter-on-quarter changes) to be explained, and every comparables sheet to be described; new
  integrity check (the extraction names the fingerprint of the file the referee checks); VERIFIED requires it.
- **Extraction schema 2:** `workbook_sha256`, `comparables` (peers, statistics, applied versus comps), `uses`.
- **Reader:** prints the workbook fingerprint and warns when a workbook arrives without formulas (values-only copies).
- **Reconcile 12.0:** both agents must have read the file checked (else CHECKS FAILED); optional extractor response
  round (`--response`): concede or contest each dispute with cells; status REFEREE FAILED renamed CHECKS FAILED.
- **Working notes** (`notes.md`) in every agent run.
- Tests 29 -> 38 (integrity, the new coverage rules, the response round, the values-only guard).

## 11.9.0 - two independent agents in a workflow; comprehensive extraction
- Extractor + blind-then-review Reviewer, files only between them; referee coverage check; reconcile; playbook; test bench.

## 11.8.0 - direct-reading trial
