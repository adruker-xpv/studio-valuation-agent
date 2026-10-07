---
name: valuation-pipeline
description: Onboards a portfolio company's valuation workbook once into a reusable company file, then updates that workbook each quarter from new monthly financial statements (refresh), tests the company file (replay, backtest), recalculates the result in SharePoint and checks it, and records corrections, approvals and reviews. Use for any valuation workbook onboarding, quarterly update, replay, backtest, correction, approval, review or pipeline self-test.
---

# Valuation pipeline

`scripts/pipeline.py` does all the work. Run one command, then do exactly what its printed lines say.
Never open, read or summarise files; never run other scripts; never calculate, count or check numbers yourself.

## Input files
- Files the user uploads: pass them **by name** exactly as the user gave them (no folder path). The script finds them.
- SharePoint links the user pastes: call `sharepoint_get_doc` once per link, then pass the file names.
- Never search or list SharePoint to find files. If a file is missing the script names it: ask the user for it and stop.

## Commands
| Job | Command |
|---|---|
| Onboard | `python scripts/pipeline.py onboard --workbook "<name>" --statements "<name>" ... --company "<company name>"` |
| Re-onboard (layout or method changed) | same, plus `--bundle "<company_id>_company.zip" --fresh` |
| Quarterly update | `python scripts/pipeline.py run --mode refresh --workbook "<last quarter's final>" --statements "<name>" ... --bundle "<company_id>_company.zip" --period-end YYYY-MM-DD` |
| Test the company file | `run --mode replay` (onboarding quarter) or `run --mode backtest --actual "<real workbook for that quarter>"`, other arguments as above |
| After a correction, approval, review or values in words | `python scripts/pipeline.py amend --changes - <<'JSON'` then the JSON (format below) then `JSON` |
| Self-test | `python scripts/pipeline.py selftest` |

Always pass JSON with the `<<'JSON' ... JSON` form shown (it keeps apostrophes in the user's words safe).

## After each command (exit code)
- **0 Done**: carry out every `SHAREPOINT:` line, then post the printed report unchanged.
- **10 Judgment** (onboarding only, at most once): answer the printed questions from what is printed only, then re-run the SAME
  command adding `--answers - <<'JSON'` + your JSON + `JSON`. Use `uncertain` or `none` when what is shown does not settle it.
- **20 Recalc**: carry out the `SHAREPOINT:` lines, then the `RECALC:` line with the Run script from SharePoint library tool
  (file = the Id that Create file returned for that workbook; cells = the list printed), then run the printed `THEN:` command
  with the script result pasted exactly. If Run script fails, follow the `IF RUN SCRIPT FAILS:` line.
- **3 Stopped**: post the printed lines as one list. Do nothing else.
- **1 Error**: post the error lines and stop.

`SHAREPOINT:` lines: Create new folder / Create file with exactly the values printed. `body` is the printed /app/created
path itself; never file content, never base64. If a folder already exists, continue.

## Changes JSON (only what the user's latest message states)
```json
{"by": "<name the user gave, else null>", "said": "<the user's exact words>",
 "classifications": [{"id": "Inputs!B6", "type": "assumption", "changes_each_quarter": "yes"}],
 "rules": [{"cell": "Financial Summary!AJ9", "execution": {"operation": "sum_months", "months": 3,
            "source": {"sheet": "Income Statement", "label": "Total Revenue", "role": "current"}}}],
 "key_outputs": {"add": [{"cell": "Valuation Summary!F25", "reason": "XPV value"}], "remove": ["LP Report!D49"]},
 "controls": [{"cell": "Checks!C4", "reason": "balance check", "control": {"control_type": "numeric", "expected": 0,
               "absolute_tolerance": 1, "severity": "blocking"}}],
 "manual_inputs": {"Inputs!B3": 9.0},
 "approve_profile": true, "review_period": true}
```
Include only the keys the message needs; copy values exactly. Rule format: `references/profile-fields.md`.
`approve_profile` and `review_period` need `by`. Never change a control's `expected` to make it pass.

## Status codes
| Code | Meaning |
|---|---|
| READY / INPUT_REQUIRED / REVIEW_REQUIRED | profile complete / some values are entered by hand each quarter / some meaning unresolved (runs still work) |
| PLAN READY / BLOCKED / REFUSED | every cell has a value / a rule could not run (stop) / the workbook does not fit the company file (re-onboard) |
| REPLAY_PASS, BACKTEST_PASS (or _FAIL) | the company file reproduced the known workbook (or did not) |
| DRAFT_READY / DRAFT_READY_FOR_REVIEW / DRAFT_BLOCKED | refresh clean / clean with review items / a technical check failed |
