---
name: valuation-generate
description: Builds a baseline valuation workbook for a company that has NO valuation workbook yet, from its financial statements plus any analyst answers, using a generic EV-multiple template made entirely of Excel formulas; optionally compares the result with the analyst's real workbook and explains the gap. Use when the user uploads statements for a new company or asks to generate a valuation from statements. For a company that already has a workbook, use valuation-pipeline instead.
---

# Valuation generate (new company, no workbook)

`scripts/generate.py` does all the work. Run one command, act on its exit code, post what it prints.
Never read intermediate files, never run other scripts, never calculate or check numbers yourself.

## Commands (copy exactly)
| Job | Command |
|---|---|
| Build | `python scripts/generate.py build --statements <files...> --company "<name>"` |
| After the Excel step | `python scripts/generate.py compare --saved "<uploaded saved file>" [--actual "<analyst's real workbook>"]` |
| Self-test | `python tests/run_selftest.py` (show its output unchanged) |

Input files: pass uploads **by name** exactly as given. For pasted SharePoint links, call `sharepoint_get_doc` once per link
first. Never search or list SharePoint. Analyst answers the user already gave (units, multiples, weights, add-backs,
discount, ownership, claims) go in as `--answers - <<'JSON'` + the JSON + `JSON`, values copied exactly (format:
`references/analyst-questions.md`). Missing answers become listed assumptions; never ask during a run. When the user
corrects an answer, run build again with the updated answers.

## Exit codes
- **10 JUDGMENT NEEDED**: read `/app/created/judgment.json`, write the file it names (only the letters asked), re-run the SAME
  command. Choose only from the options shown; use `none` when no option clearly is that metric.
- **20 EXCEL STEP**: return the workbook with `references/excel-step.md` and end your turn.
- **3 CANNOT BUILD**: post the BLOCKER lines as one list (e.g. fewer than twelve months of statements).
- **0 DONE**: carry out every `SHAREPOINT:` line (`body` is the printed /app/created path, never content or base64), then
  post the printed report unchanged.
- **1 ERROR**: show the error lines and stop.

The generic template is a baseline, not the company's method: present differences as findings.
