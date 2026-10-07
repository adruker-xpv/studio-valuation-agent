# Context for a new chat – XPV valuation agent, continuing to build 11.3 (as of 7 October 2026)

**Attach to the new chat:** this file, `valuation-pipeline.zip` (build 11.2, the code baseline),
`valuation-build-plan-v11.1.md` (design reference), `valuation-agent-build-11.2-guide.md` (setup / tests / running),
`agent-instructions.txt`, `recalc-and-read.ts` (Office Script v4). Then say: "Continue with build 11.3 as planned."

---

## 1. Glossary
| Term | Meaning |
|---|---|
| Limited partner (LP) report | XPV's quarterly investor report; everything works back from each company's LP numbers |
| Enterprise value (EV) / equity value / value to XPV | Valuation chain: EV from multiple(s) × metric(s); equity = EV + cash − debt (+ bridge items); XPV's share via ownership or waterfall |
| Trailing twelve months (TTM) | Sum of the 12 months ending at the valuation month |
| EBITDA / adjusted EBITDA | Earnings before interest, tax, depreciation and amortization; adjusted adds approved one-time items (nine categories) |
| Copilot Studio agent | `valuation-pipeline-automate`, GitHub Copilot harness; runs the Python skill in a sandbox; has clearance for confidential files |
| Skill | `valuation-pipeline` zip: `SKILL.md` + Python scripts; plus `valuation-generate` (unchanged, for companies without a workbook) |
| Office Script | `recalc-and-read` (v4): recalculates a `__copy` / `__draft` file in SharePoint and returns requested cells; refuses originals because it saves the file |
| Knowledge sources | Valuation Workbooks, Company Financial Statements, Monthly Summaries (created by XPV), LP_reports – used only to fetch files into the sandbox |
| Company file | `Valuations/<company>/company/<company>_company.zip`: map, facts, evidence ledger, approvals |
| Mapping | Onboarding: how the approved workbook turns statements into the LP numbers |
| Build map | Parts the LP numbers depend on, in build order, each input with its next-quarter source |
| Liveness checks L1–L5 | L1 LP values are formulas; L2 no pasted calculations; L3 no external links / manual calc / errors / missing saved values; L4 Excel recalculation of a copy matches; L5 Python's identities and formula re-computation match Excel |
| Answer key | Private, analyst-approved expected results for one company and quarter, kept only in the authorised environment |
| Sanitised diagnostics | Output allowed to leave the authorised environment: test ID, failure category, period mismatch, dependency role, evidence status – no values, names, paths or contents |

## 2. Who, what, goal
- **Aria**, AI intern at XPV Water Partners, builds a conversational valuation agent in Microsoft Copilot Studio.
  Analysts (about 7, non-technical) onboard portfolio companies (about 10), then generate quarterly valuations from
  monthly statements; numbers feed the LP report and must be auditable (IPEV-style traceability).
- **Ideal end state:** input → extract → a live-formula draft workbook the analyst finishes and approves (~90% done);
  every downstream cell stays a formula; analysts do minimal work; AI judgement is used where helpful, always verified.
- **Working style:** be critical, push back, best practice with honest trade-offs; documentation has a glossary and
  terms in full before abbreviations; give only changed files; plans for coding are explicit (files, interfaces,
  printed lines, test IDs, done criteria); version everything as build 11.x.

## 3. Clearance boundary (current, binding)
- **Claude never receives real workbooks, statements, company names, numbers, paths or contents.**
- Build with **synthetic fixtures** that reproduce the structural challenges (section 8, WP7). Keep company-specific
  mappings **configurable**, never hardcoded.
- Real files are tested **only inside the authorised environment** (the Copilot Studio agent) by a `verify` runner
  against a **private analyst answer key**; only **sanitised diagnostics** come back.
- **No production-readiness claim** until both the synthetic suite and an authorised verify run pass.
- Earlier statements that anonymisation was unnecessary are superseded by this boundary.

## 4. Where things stand (build 11.2)
- **Package 11.2.0**, 51 synthetic tests pass (also with a read-only skill folder and `/app/workspace` temp, as in the
  agent sandbox). Deployed in the agent's Preview; **publishing is blocked** by a Power Platform data policy conflict
  ("Conflict details aren't available") – admin needed; testing continues in Preview.
- **Commands:** `selftest`, `gather` (choose files for company + quarter from knowledge-fetched files), `onboard`,
  `check-recalc`, `approve`, `explain`, `status`, `add` (files; facts into the company file), `reference` (on demand,
  structure of workbooks found for a feature), `census` (optional overview), `census-one` (internal).
- **Removed in 11.1:** portfolio register and its link. **11.2:** Excel step skipped automatically for workbooks with
  add-in cells, external-link formulas, >150,000 formulas or >8 MB (`L4 SKIPPED`); plain cell references for the
  script; "run once, never retry" rule; Office Script v4.
- **Standard request:** "Onboard <company> for <quarter>" → agent searches the four knowledge sources → `gather` →
  printed `THEN` onboard command → follow printed lines → report → one message for NEED items + approval.

### Package layout (scripts/)
| File | Role |
|---|---|
| `pipeline.py` | CLI, printed-line protocol (`PREFIXES`), exit codes (0 done, 10 judgment, 20 waiting for tool step, 3 stopped, 1 error), assumptions register, reports, gather, add, reference, status |
| `analyze.py` | LP field candidates by label (`references/lp_fields.json`), identity solver (EV, adjusted EBITDA, equity, investor value, MOIC; blended weights; FX; formula re-computation fallback; AI-proposed calculations verified by Python), metric windows (static ranges and value-matched), periods/lag, input classes, pasted calculations, liveness, findings with severity, verdict |
| `workbook_model.py` | Streaming read (openpyxl read-only) into compact dicts; skips unreferenced formula-free sheets; labels, precedents (ranges, defined names), add-ins, external links, monthly/quarterly blocks, fingerprint |
| `formula_eval.py` | Re-computes one formula from saved precedent values (+ − × ÷ ^ %, SUM, AVERAGE, MIN, MAX, ABS, ROUND, IFERROR); unsupported → never guessed |
| `parts.py` | Build map: roles (`references/build_rules.json`), build order, next-quarter source per input, gaps, trace per LP field, learning from a previous quarter |
| `statements.py` | Statement reader (layouts, YTD), entity-keyed series, line map (all overlap months must match after scale/sign; quarterly sum-of-3 or quarter-end), period gate |
| `catalog.py` | File kinds, company names from file names, structure features/patterns |
| `company_file.py` | Deterministic zip, hash-chained ledger, manifest, method hash |
| `wbutil.py` | Helpers; `VERSION`; file resolution (`resolve(..., broad=False)` for company files) |
| `tests/fixtures.py`, `tests/run_selftest.py` | Synthetic workbooks with Excel-style saved values; CLI-level tests |
| `tools/check_package.py` | Release check (deny-list, junk, nested skills) and clean zip |

## 5. Settled decisions (keep)
- Work back from the LP outputs; only cells upstream are classified or written; everything else is counted.
- History comes from approved workbooks; statements prove; approved values win over later statements.
- The pipeline writes only raw inputs; every other cell stays a live formula.
- Excel computes the valuation; Python checks (never re-implements a waterfall).
- AI chooses between printed options and proposes calculations; Python keeps a proposal only if it reproduces
  Excel's value; numbers never come from the AI; analyst facts are recorded word for word.
- One company per conversation; files from knowledge; uploads (20 per conversation) only for files not in SharePoint.
- Approval stays pending until a named analyst approves (this held correctly on the real run – preserve it).

## 6. Real-file onboarding results (sanitised), confirmed vs hypotheses
| Item | Observed (confirmed) | Hypothesis (not yet confirmed) | Test to confirm |
|---|---|---|---|
| Wrong period slice | Metric windows Jan–Dec 2024 for a Q1 2026 request (15-month lag); identities still passed | Candidates were taken from an older period column because selection was not anchored to the requested date | Verify run with the answer key: compare mapped output cells' period headers to the requested date |
| Selected multiple | Mapped cell was an individual comparable's row | Label search + numeric coincidence instead of EV's formula | Answer key's selected-multiple cell vs mapped cell |
| Statements | Only the baseline workbook was registered; all line-map rows lacked statement evidence; trace showed downloads then failed recognition | Classification (company/entity) failed, not retrieval | Per-file stage log Found → Downloaded → Classified → Parsed → Registered → Reconciled |
| Excel recalculation | Tool call timed out (~60 s), several times; the agent retried instead of using the fallback; the cell list was re-quoted by the agent | Recalculation time, add-in refresh or link refresh exceeded the tool limit | Excel diagnostic (WP5) |
| External links | 18 active link formulas on the LP dependency graph; a much longer list of linked workbook names in metadata | Many names are stale link records | WP6 active-vs-stale split |

## 7. Agreed principle for 11.3
**Prove period and meaning first, then math, then evidence.** Every LP number: (1) is it the requested quarter's cell
in the right role (by its dependency role's own period rule)? (2) does its formula reproduce Excel's value? (3) are
the months behind it reconciled to statements (or carried from the approved baseline, explicitly labelled)?
Onboarding **describes and validates** the approved method; it never changes it.

## 8. Build 11.3 work packages (test-first)
**WP1 – Request-anchored periods and dependency roles** (`analyze.py`, `parts.py`)
- Valuation date comes from the request (`gather` passes `--period-end` derived from the quarter).
- Anchor on the LP outputs for that date (LP report / valuation summary cells whose period header matches); output
  fields must match the requested date.
- Dependency roles with their own period rules: period-end balance (at valuation date), monthly history (contiguous
  months ending at valuation month), TTM metric (exactly 12 consecutive months ending at valuation month, formula
  reconciles), historical investment cash flows (dates ≤ valuation date), valuation assumptions (current quarter),
  acquisition / pro forma adjustments (their stated period).
- Tests: wrong-period column side by side → rejected with `wrong_period`; correct column chosen; roles classified.

**WP2 – Method and multiple traced through formulas** (`analyze.py`)
- Trace EV's formula tree: direct multiplication, discounted or weighted multiples, blended methods, analyst-entered
  assumptions. Comparable rows may feed the selected multiple but are never the selected assumption.
- Tests: ambiguous multiples; comparable-row decoy; blended; discounted average of comparables.

**WP3 – Statement evidence pipeline** (`statements.py`, `catalog.py`, `pipeline.py`)
- Per file: Found → Downloaded → Classified → Parsed → Registered → Reconciled, with identity, detected entities
  (file name and content), months covered, status, rejection reason. Ambiguous entity → blocked, not guessed.
- Per month evidence status: newly reconciled / carried from approved baseline / unsupported / analyst-approved
  adjustment. Non-statement inputs (cap tables, investment records, comparables, add-back schedules) have their own
  evidence sources.
- Tests: duplicate and revised statements; missing historical coverage; ambiguous entity; consolidated vs entity.

**WP4 – Explicit decisions and a safe approval gate** (`pipeline.py`, `company_file.py`)
- Period conflicts classified: wrong cells selected / intentional lag or fiscal-year basis / workbook defect; each
  needs its own explicit decision; nothing becomes a convention by group approval; no methodology or formula change
  without explicit approval.
- `approve` refuses while any material exception lacks a decision; review groups repeated findings but keeps detail.
- Tests: approval attempt with unresolved blockers → refused; grouped findings keep evidence.

**WP5 – Excel diagnostic and verification statuses** (`recalc-and-read.ts` v5, `pipeline.py`) – see section 9.

**WP6 – Active vs stale external links** (`workbook_model.py`, `analyze.py`)
- Map each `[n]` reference in formulas to its external-link part; active = used by formulas on the LP dependency graph;
  stale records and metadata listed, never blocking; required-for-refresh flagged.
- Tests: active link unavailable → disclosed; stale link records → not blocking.

**WP7 – Synthetic fixture factory** (`tests/fixtures.py`)
- Toggleable challenges: several valuation periods side by side; actual, budget, variance, monthly, quarterly and TTM
  columns; consolidated and entity sheets; acquisition / pro forma adjustments with historical dependencies; external
  links and cached values; missing evidence; ambiguous labels; unsupported formulas.

**WP8 – Authorised verify loop** (`pipeline.py verify`, `references/answer_key_template.json`)
- `verify --key <private answer key>` runs onboarding silently in the agent and prints only sanitised lines, e.g.
  `OB-01 | FAIL | wrong_period | role ttm_metric | expected 2026-03 got 2024-12 | evidence not_reconciled`.
- A test asserts verify output contains no values, file names, sheet names or paths.
- Answer key template (filled privately in the authorised environment):
  ```json
  {"test_id": "OB-01", "valuation_date": "2026-03-31",
   "outputs": {"enterprise_value": "<sheet!cell>", "adjusted_ebitda": "<sheet!cell>",
               "selected_multiple": "<sheet!cell>", "value_to_xpv": "<sheet!cell>"},
   "ttm_window": ["2025-04", "2026-03"], "method": "ev_ebitda | blended | ...",
   "entities": 2, "statement_months_expected": ["2026-01", "2026-02", "2026-03"]}
  ```

**WP9 – Docs** (`SKILL.md`, `agent-instructions.txt`, guide 11.3): findings shown as observed evidence / hypothesis
/ test / fix; new printed lines documented (test T0.3 enforces).

**Done criterion for this stage:** for one company and quarter in the authorised environment, the agent reproduces
the answer key's requested-quarter outputs with traceable, period-correct evidence, discloses every unsupported
dependency, and cannot be approved while a failure is unresolved – shown by the synthetic suite and a sanitised verify
run. Out of scope: quarterly generation, backtest build, close, other companies, publishing.

## 9. Excel recalculation timeout – handling
**Now (11.2):** the Excel step is skipped automatically for workbooks with data-provider add-ins, formulas reading other
workbooks, >150,000 formulas or >8 MB (`L4 SKIPPED`; Python's L5 checks still run). Otherwise the agent runs the
script once with the printed cell list; on failure or timeout it runs the fallback (`L4 NOT RUN`); never retries.
Office Script v4 reads the cell list before calculating and returns only the requested cells.

**Planned (11.3, WP5) – diagnose before deciding:**
1. **Probe** (no recalculation): open the copy, read a small range → proves access, connection and file Id.
2. **Recalculate only**: full recalculation, return status and seconds only.
3. **Read critical outputs** in small groups after recalculation.
4. **Compare** with saved values.
Modes are passed inside the existing `cells` parameter as JSON (`{"mode": "probe|recalc|read", "cells": [...]}`), so
the tool configuration does not change. Results distinguish formula calculation, workbook-link refresh and add-in
refresh, and whether the ~60 s tool limit or the 120 s script limit was hit.

**Verification statuses kept separate:** *verified automatically* (L4 pass) / *analyst-attested* (desktop Excel
recalculation recorded with workbook fingerprint, analyst, time, refresh performed, unresolved links or add-ins,
outputs checked) / *not verified*. Attestation is an explicit decision, never an automatic pass.

## 10. Environment facts (checked October 2026)
- GitHub Copilot harness: skills run in a Python 3.12 sandbox, no network, temporary files; knowledge files are fetched
  whole into the sandbox and reused for the conversation (search-ranked, not exact lookup; titles matter).
- Uploads: 20 files per conversation, 16 MiB each; agent-created files 10 MB, kept 28 days.
- SharePoint *Create file* inline limit ~4 MB; the agent cannot read SharePoint by path (links via `sharepoint_get_doc`,
  which is optional and a suspect in the data-policy conflict).
- Office Scripts: 120 s limit, 1,600 runs per user per day, 5 MB request/response; the agent's tool call timed out at
  ~60 s in practice.
- Data policies: connectors must be in the same data group; preview's built-in test channel does not block publishing,
  but blocked connectors or channels do.

## 11. Open questions for Aria (structural only – no values)
1. Approve the answer-key fields (WP8) and who fills them in the authorised environment.
2. Are quarters side by side as columns, or separate sheets? Is there an LP Report sheet in every workbook?
3. Statements: one file per entity per month? Where does the company / entity name appear inside them?
4. Is desktop recalculation attestation acceptable evidence for complex workbooks?
5. Data-policy block: which component (remove `sharepoint_get_doc` first, then bisect) – admin to resolve.

## 12. Lessons to keep
- Don't state causes without a test; report observed evidence and hypotheses separately.
- Internal mathematical consistency does not prove semantic correctness: period and meaning first.
- The printed lines are the agent's interface; every new prefix goes into `PREFIXES` and `SKILL.md`.
- Never search all of `/app` for company files; tests set `VALUATION_FILE_ROOTS` to their own folder.
- The Office Script saves the file: copies and drafts only; run once, never retry.
- Test in the agent-like layout (non-root, read-only skill folder, `TMPDIR=/app/workspace`) before shipping.
