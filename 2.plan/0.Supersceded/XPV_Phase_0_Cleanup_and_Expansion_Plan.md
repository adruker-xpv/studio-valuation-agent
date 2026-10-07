# XPV Valuation Agent: Build Plan

*Status as of 28 Sept 2026*

## Goal

Generate each quarter's valuation workbook from a company's new financial statements. Every value should be traceable to its source, and an analyst signs off before anything is used.

## Architecture

One Copilot Studio agent (`valuation-structure-initialize`) running on the GitHub Copilot harness. Each capability is a Skill: a set of instructions plus reviewed Python scripts that run in the agent's sandbox.

Work is split three ways, and the split holds at every step:

| Who | Does | Why |
|---|---|---|
| **Python scripts** | Reading workbooks, tracing dependencies, merging, validating, value matching, writing reports | Exact and repeatable; the model never does arithmetic or bulk reading |
| **Agent (LLM)** | Choosing key outputs, classifying inputs, grouping concepts, short explanations | Judgment calls, each written to a small decision file the scripts check |
| **Analyst** | Confirming classifications, approving mappings, signing off outputs | Nothing becomes "confirmed" without a named person |

Runs are autonomous. The agent completes the whole workflow without stopping, then reports every decision it made for the analyst to confirm or correct.

**Sandbox constraints:**

- There is no network access.
- Files are deleted after each conversation.
- The sandbox can read workbooks but cannot recalculate them (no LibreOffice, `formulas` or `pycel`).

As a result, files must be saved out (as downloads), and recalculation has to happen in Excel.

## Pipeline

| Phase | Skill | Output | Status |
|---|---|---|---|
| 1. Structure initialization | `valuation-workbook-schema` | Schema, input map, run report | **Built; tested on Opus Water (about 8.5/10)** |
| 2. Mapping profile | `valuation-mapping-profile` | Concept registry with source lineage from value matches, refresh rules, approvals | **Built; tested on demo files only** |
| 3. Replay test | Not built | Refill the current quarter, recalculate in Excel, compare key outputs | Next |
| 4. Quarterly refresh | Not built | Draft new workbook, reconciliation report, exceptions list | Later |
| Support | `sandbox-env-check` | Environment report | Done: no recalculation available |

Phases 1–3 run once per company and again whenever its workbook template changes. Phase 4 runs every quarter. Later the agent can be split in two: a Setup agent for phases 1–3 and a Quarterly agent for phase 4.

## Accomplished

- **Deterministic extraction.** Every sheet, input, formula and output, with dependency paths from each input to the key outputs. Handles hidden sheets, merged headers, whole-column references, named ranges and external links.
- **Materiality from key outputs.** On Opus Water, this cut 930 referenced input cells to the 235 that feed the 13 selected outputs, with full reconciliation.
- **Honest status reporting.** Technical status is kept separate from business review. Low- and medium-confidence items, unconfirmed cadence, and inputs marked non-material automatically are always shown in the report.
- **Reuse and corrections.** The saved input map lets a later run skip the judgment steps. Corrections and confirmations are applied through decision files, never edited by hand.
- **Evidence-based lineage (Phase 2).** Each input value is matched to the source statements (direct, scaled, sign-flipped, 3-month or 12-month sums). Where values are shared across lines, the source that explains the whole row wins.

## Next

1. Replace both skills with the latest zips and re-run Opus Water with its saved input map.
2. Get Opus Water's Q1 source statements (Excel or CSV) and run Phase 2 against them.
3. Hold a 30-minute session with the analyst to set refresh rules and approve concepts, using the profile review file as the agenda.
4. Build the replay test (Phase 3). The agent writes the inputs; the analyst opens the file in Excel, saves it and re-uploads it; the agent compares the outputs.
5. Connect the SharePoint Create file tool, with one folder per company as the record of each run.
6. Build the quarterly refresh (Phase 4). Later, move recalculation to Excel Online ("Run script") so the manual step goes away.

## Open risks

- **Roll-forward structure.** Adding a period column is harder than filling fixed cells. Confirm which approach the XPV workbooks need before building Phase 4.
- **PDF statements.** Not yet parsed. `pdfplumber` is available, so this is feasible.
- **Heuristic labels.** Row and column labels are still inferred from nearby text. Confidence ratings and analyst review are the safeguard.
