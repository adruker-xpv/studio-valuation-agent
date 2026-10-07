## Plan: Evidence-First Company Workbook Automation

**TL;DR** — Keep the existing company-bundle pipeline, but make every input, formula, assumption, and approval auditable. Phase 1 establishes a trustworthy Opus Q1 baseline; Phase 2 refreshes it from Q2 statements; Phase 3 adds human review and LP reporting. The approved Q1 workbook is the replay baseline, and the approved Q2 workbook is a post-generation comparison target, not a Q2 input source.

### Phase 1: build a trustworthy Opus Q1 baseline
1. **Correct the Opus profile state**
   - Replace the placeholder Q1 profile status with a non-approved state until the baseline passes replay.
   - Correct the period metadata to the actual Q1 reporting end and retain the exact workbook and statement file hashes.
   - Record the file provenance, workbook version, statement dates, units, and layout fingerprint in the company bundle.
   - Dependencies: approved Q1 workbook and Q1 statements.

2. **Add a persistent evidence registry**
   - Add `source_registry.json` as the fourth bundle artifact beside `company_profile.json`, `input_map.json`, and `mapping_profile.json`.
   - Record for each material cell: source workbook or statement, sheet, label, period, unit, sign, rule, formula, confidence, owner, and status.
   - Add `evidence_hash` and `provenance_version` fields so later edits are visible and every approved record is immutable.
   - Source statuses must be mutually exclusive: `proven`, `historical`, `assumption`, `manual_input`, `manual_review`, or `exception`.
   - Dependencies: step 1; parallel with step 3.

3. **Make unsupported classifications non-default**
   - Treat `EXECUTABLE` as valid only when a runnable rule reproduces the workbook.
   - Keep a single-number match as `EXECUTABLE_UNVERIFIED` until it is independently confirmed.
   - Require either a source line or an explicitly approved assumption for every unknown value; otherwise keep it as `manual_review` and block the refresh.
   - Never convert an unresolved value into an assumption merely because a classification heuristic suggests one.
   - Dependencies: step 2.

4. **Add formula and cell-origin tracing**
   - Record each key-output formula, referenced cells, statement inputs, and calculation path.
   - Extend the validation report to distinguish formula changes, added or deleted formulas, mismatched references, changed precedents, and value mismatches.
   - Require formula preservation and key-output equality before approving the workbook.
   - Dependencies: steps 2–3.

5. **Run the Q1 replay gate**
   - Rebuild Q1 from the approved Q1 statements and bundle.
   - Compare every written input, formula, control, key output, and exception with the approved Q1 workbook.
   - Require all blocking controls, formula checks, and key-output matches to pass.
   - Require every remaining unresolved item to be approved by a named reviewer or explicitly documented as a known limitation.
   - Create the signed Q1 baseline only after this gate passes, with approval recorded against the exact profile version.
   - Dependencies: steps 1–4.

### Phase 2: refresh from Q2 statements
6. **Use the approved Q1 baseline as the only input bundle**
   - Use the approved Q1 workbook only to validate replay and establish prior-period values.
   - Use the approved Q1 bundle as the starting point for Q2 generation.
   - Do not use the approved Q2 workbook as a Q2 generation input.
   - Dependencies: Phase 1 Q1 replay approval.

7. **Generate the Q2 draft from verified rules**
   - Apply only rules whose source lineage is proven or explicitly approved for the new period.
   - Record the Q2 source file, sheet, label, rule, calculation, value, and status for each written cell.
   - If a required source is missing, stop with a `BLOCKED` result and an evidence request rather than carrying forward an unknown value.
   - Dependencies: step 6.

8. **Run the Q2 backtest**
   - After Excel recalculation, compare the generated workbook against the approved Q2 workbook.
   - Report mismatches by cell, concept, formula, and input source; do not collapse them into a single variance.
   - Require exact formula preservation, all blocking control passes, and all key-output matches before acceptance.
   - Dependencies: step 7 and approved Q2 workbook.

9. **Persist quarterly history**
   - Create a company history archive containing approved bundles, workbook hashes, run logs, source registries, and signed decisions for each quarter.
   - Store each quarter as a versioned snapshot rather than overwriting prior state.
   - Use the archive to answer what source was used and what changed since the last quarter.
   - Dependencies: steps 2 and 7; it becomes mandatory on final Q2 acceptance.

### Phase 3: human review and LP reporting
10. **Introduce tiered review**
   - Tier A: material valuation and source-evidence changes.
   - Tier B: non-material presentation or formatting changes.
   - Tier C: informational items that require acknowledgment, not approval.
   - Every review item must include impact, uncertainty, affected cells, source, reviewer, deadline, and status.
   - Dependencies: Phase 1 and Phase 2.

11. **Separate approval from execution**
   - The agent may generate and validate a draft independently.
   - A named reviewer approves the material assumptions, formula changes, profile version, and final workbook.
   - Approval must reference the exact bundle and workbook versions; stale approvals are rejected.
   - Dependencies: step 10.

12. **Defer LP aggregation until company workbooks are reliable**
   - Use approved company bundles and historical snapshots as the input to fund-level aggregation.
   - Keep company-source evidence separate from LP-level summaries and roll-up logic.
   - Record the LP model’s source companies, periods, assumptions, calculations, overrides, and manual adjustments.
   - Dependencies: steps 10–11 and successful Opus Q1/Q2 validation.

### Relevant artifacts
- `2.plan/Agent_Build/agent-instructions.txt` — current agent routing and restrictions.
- `2.plan/Agent_Build/valuation-pipeline/SKILL.md` — company bundle workflow and status model.
- `2.plan/Agent_Build/valuation-pipeline/scripts/pipeline.py` — company onboarding, refresh, check, amendment, and self-test orchestration.
- `2.plan/Agent_Build/valuation-pipeline/scripts/check_result.py` — deterministic technical validation and review-list generation.
- `2.plan/Agent_Build/valuation-pipeline/tests/run_pipeline_selftest.py` — existing end-to-end regression coverage.
- `2.plan/Agent_Build/lp-output-contract-build-spec (1).md` — LP-report registry and phase targets after company automation is proven.
- `2.plan/Agent_Build/valuation-pipeline-automate (3).yaml` — current Microsoft Copilot Studio agent definition and tools.

### Verification
1. Run `python scripts/pipeline.py selftest` after each evidence-registry, provenance, approval, and archive change; preserve the complete output as the release record.
2. Run a fresh Q1 replay using the approved Q1 bundle and workbook. Require all blocking controls, key-output matches, formula-preservation checks, input rebuilds, and unresolved items to pass or be approved.
3. Run a fresh Q2 refresh using the approved Q1 bundle and Q2 statements. Require every missing source to be explicit rather than silently carried forward.
4. Run a Q2 backtest against the approved Q2 workbook. Require all key-output matches and no unresolved formula changes.
5. Inspect the generated run log and source registry to confirm that each material cell has a source, rule, or explicit human approval.
6. Require a human review record before final workbook approval or LP publication.

### Decisions and required inputs
- **Decision:** Company onboarding and quarterly refresh are the first production milestone; LP reporting is the second milestone.
- **Decision:** The approved Q1 bundle is the authoritative baseline for Q2 generation; the approved Q2 workbook is the comparison baseline.
- **Decision:** A materially important rule cannot be accepted from one source line alone; it must be confirmed or independently traced.
- **Required input:** The exact approved Opus Q1 workbook and Q1 statement files.
- **Required input:** The exact Opus Q2 statements and approved Q2 workbook for validation.
- **Required input:** The named company reviewer and approval authority, plus the final LP reviewers when Phase 3 begins.
- **Required input:** The SharePoint location and access path for the company archive and final workbooks.
- **Explicit exclusion:** No unsupported assumptions, defaults, or silent carry-forwards for material sources; the run stops when evidence is missing.

### Further considerations
1. **Profile approval integrity:** The current Opus profile has an approval record that does not match the current profile version; approval metadata must be corrected before Q1 replay.
2. **Historical archive location:** Choose whether the archive is stored only in SharePoint, in the company bundle, or in both locations.
3. **Production trigger:** Decide whether a new quarterly run starts from upload, SharePoint change, or an explicit chat command.
4. **Opus source completion:** The exact source lines for EBITDA adjustments, cash, debt, and IRR inputs must be obtained before production refresh can be trusted.
