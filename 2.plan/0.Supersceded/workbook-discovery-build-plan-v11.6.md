# Workbook discovery – build plan v11.6 (replaces v11.5 sections 3, 5 and the answer-key parts)

## Glossary
| Term | Meaning |
|---|---|
| The program | Reads one workbook (never changes it) and writes what it contains, how it connects and what it means |
| The checker | Compares the program's output with Excel's own export and with an analyst's answers; never imports program code |
| Export copy | A copy of the workbook in which `excel-export.ts` writes every cell and what each distinct formula uses |
| Answer form | The analyst's short form: five key numbers (sheet + number cell), two months, the method, labelled areas |
| Confidently wrong | The program claimed PROVEN and the independent answer disagrees: must be 0 |

## What changed from v11.5 and why
- **Excel is the independent answer for file contents**, for every cell, instead of counts plus a random sample. The two
  exports have the same columns, so they diff; Excel lists what each *distinct* formula uses (copies share one pattern),
  which covers all of the workbook's logic in a manageable number of checks.
- **The analyst answers only what Excel cannot:** the key numbers' cells, the months, the method, and area labels (one
  label covers hundreds of cells). About 20–30 minutes instead of 2 hours; the random 45-cell sample is gone.
- **No separate key-building step:** compare reads the export copy and the saved answers directly; fingerprints and the
  answers' own hash bind everything to one unchanged workbook (Python checks, no AI judgement).
- **Results arrive in stages**, so time is only spent where the previous stage passed: tests → demo → first look → Excel
  comparison (no analyst) → analyst comparison → more workbooks.

## Architecture
```
 WORKBOOK ──► PROGRAM ──► program_cells.csv, program_uses.csv, program_answers.xlsx/.json, map files
    │
    ├─► copy "… - export.xlsx" ──► excel-export.ts (Excel) ──► XLX Cells, XLX Uses, XLX Info
    │
    └─► ANALYST ──► answer form ──► check-form ──► save-answers ──► analyst answers.json
                                                                  │
                         CHECKER (compare) ◄──────────────────────┘ ◄── export copy ◄── program output
                         ──► comparison.xlsx, excel_cells.csv / program_cells.csv (diffable), result.json, BENCHMARK lines
```
Engineering standards from v11.5 §4 are unchanged (separation test, determinism, no silent truncation, fail fast, rules as
data, contracts tested, vendored code unchanged, gated releases, test-first fixes).

## Roadmap
| Build | Content | Exit criteria |
|---|---|---|
| 11.5 (done) | hardening, invariants, release gate | 37 tests |
| **11.6 (this)** | Excel export script, same-format exports, short answer form with checks, compare, demo, runbook | 39 tests; demo clean; runbook milestones 1–2 pass in the agent |
| 11.7 | first real workbooks: runbook milestones 3–5 on one workbook, then 6 on 2–4 more; every failure reproduced in a fixture before it is fixed | file contents match Excel; confidently wrong 0; key numbers and areas correct on all but the held-aside workbook |
| 11.8 | the held-aside workbook, then fixes | the same, on the held-aside workbook, with no regression |
| 12.0 (design only) | quarterly generation, using the decision registry and invariant registry (v11.5 §6) | design reviewed before any generation code |

## Risks specific to 11.6
| Risk | Mitigation |
|---|---|
| Excel's script may store formula text as live formulas in the export sheet | the script sets the columns to Text first; runbook milestone 4 step 3 checks it in one minute |
| `getDirectPrecedents` behaves differently in XPV's tenant (e.g. not listing other sheets) | each formula row says "Excel could not list" when it fails; such checks are reported separately, never as passes |
| Very large workbooks take many script runs | the script resumes; the runbook says to keep pressing Run until Finished |
| Analysts give a label cell instead of the number | the form says so with an example; check-form catches it and points to the likely number cell |
