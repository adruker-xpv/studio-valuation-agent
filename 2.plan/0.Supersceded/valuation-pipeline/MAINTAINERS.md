# Maintainer notes (not read by the agent)

## Glossary
| Term | Meaning |
|---|---|
| Company bundle | `<company_id>_company.zip`: everything learned about one company. Uploaded with every run. |
| company_id | Fixed folder and file name for a company, derived once from its name ("LuminUltra Technologies" -> `luminultra`). Never re-decided at run time. |
| Key output | A valuation cell the pipeline traces backwards from (enterprise value, equity value, fund value, multiple, EBITDA used, controls). Inputs that feed none are not material. |
| Control | A workbook check cell (a difference that should be 0, or a TRUE/FALSE test). |
| Concept | One input with one rule (for example quarterly revenue = sum of three monthly Net Sales). |
| Replay | Rebuild the onboarding quarter from its own statements; proves the bundle reproduces the workbook. |
| Backtest | Roll last quarter forward with new statements and compare with the analyst's real workbook. |
| Refresh | The production quarterly update. |
| Decisions log | `decisions` in company_profile.json: every correction, approval and AI proposal, with who, when and the user's words. |
| Judgment | The only AI step inside onboarding: one printed question at the end (key-output ties + unclear inputs); the agent re-runs with `--answers`. |

## Flow
```
onboard  : workbook + statements -> key outputs (rule; AI only if a core metric is ambiguous) -> trace inputs
           -> classify (rule; AI only for inputs evidence cannot settle) -> discover statement rules by reproduction
           -> company bundle
run      : bundle + statements + last workbook -> plan every cell (rules, roll-forward, carry-forward, manual)
           -> draft (only input cells change; formulas, charts and links untouched) -> saved to SharePoint
           -> RECALC: the Office Script recalc-and-read recalculates it in Excel for the web and returns key values
              and error cells (fallback: desktop Excel + upload, check --saved)
check    : script result (or saved workbook) -> inputs landed, formulas unchanged, recalculated, no new Excel
           errors, controls pass, (replay/backtest) key outputs match -> run log + review list only when needed
amend    : changes.json -> decisions log -> re-onboard (company changes) or re-run (manual inputs) or record review
```
Compatibility routing is deterministic: a workbook whose structure fingerprint differs from the bundle is refused
with "re-onboard with --bundle --fresh"; a changed statement layout is a note; a missing source is an exception.

## Files
| Where | File | Purpose |
|---|---|---|
| bundle | company_profile.json | identity, profile_version, review (named approval), decisions log, open items, onboarding sources |
| bundle | input_map.json | key outputs, controls, input classifications, dependency paths |
| bundle | mapping_profile.json | executable statement rules, period offsets, evidence (lineage) |
| per run | `<id>_<quarter>_<mode>_draft.xlsx` | the draft for the Excel step |
| per run | `<id>_<quarter>_<mode>_run_log.json` | every write with its source (file / sheet!cell, period, rule), check result, review, reviewer |
| per run | `<id>_<quarter>_valuation.xlsx` | refresh only: the saved final |
SharePoint: `Valuations/<company_id>/company/` (bundle) and `Valuations/<company_id>/<quarter>/` (final + run log).
Scratch files live in `/tmp/valuation_work/<company_id>/`; `--debug` keeps them in `/app/created/debug/<company_id>/`.

## Copilot Studio tools the agent uses
| Tool | Used for | Fixed inputs |
|---|---|---|
| SharePoint Create new folder, Create file | `SHAREPOINT:` lines | site AIInterns-AriaDruker |
| Excel Online (Business) Run script from SharePoint library | `RECALC:` lines | site, library (drive) and script `Valuations/Scripts/recalc-and-read.osts`; the agent fills file (Create file's Id) and cells |
| sharepoint_get_doc (built in) | SharePoint links pasted by the user | none; it only works from a pasted link or a search result |
Files are always passed to the scripts by name; `find_file` matches chat uploads ("-1a2b3c4d") and SharePoint
downloads ("_1", " (1)"). JSON arguments are passed with a quoted heredoc (`--answers - <<'JSON'`) so apostrophes
in the user's words cannot break the command.

## Scripts
`pipeline.py` orchestrates; stage scripts: extract_schema (structure, tracing), index_sources (statements),
match_values (rule discovery), apply_classifications, validate_input_map, build_profile, plan_writes, apply_writes,
check_result. `build_report.py` runs in `--debug` only.

## Tests
`python scripts/pipeline.py selftest` runs the engine test (22 cases: layouts, rules, roll-forward, chart
preservation) and the pipeline test (22 cases: onboarding, judgment, replay, refresh, amend, decisions re-applied,
Excel-error detection, old-bundle upgrade). Run it after any change.

## Changes from v5 (September 2026)
- Key outputs chosen by rule. Tied candidates are kept provisionally, onboarding finishes, then ONE printed question covers ties and
  unclear inputs; answers come back inline (`--answers`), corrections inline (`amend --changes`): no file reads or writes by the agent.
- Decisions log, named approval and period review replace the certification file; refresh is no longer gated.
- One bundle with a fixed company_id; older `_company_files.zip` bundles upgrade on first use.
- One correction path (changes.json + amend), re-applied on every re-onboarding (`--fresh` for changed workbooks).
- Check adds new-Excel-error detection and verifies the saved file's inputs; prints failures and review items only.
- Normal runs leave a draft and a run log; manifests, reports and schema files are gone or debug-only.
- Key-output cap raised from 15 to 25 (MAX_KEY_OUTPUTS in pipeline.py and extract_schema.py); up to 8 check cells as controls.
- A statement rule proven by a single number from a differently named line is listed for confirmation at onboarding.

## How rule discovery avoids coincidences
Each typed-in input is compared only with values built from ONE statement line (value at a month, sum of 3 or 12 months,
YTD difference) at a standard unit scale (1, thousands, millions) and sign. Workbook cells are never combined with each
other. Numbers under 100 are never matched. If two different lines fit equally well, no rule is chosen. A rule must fit
every period cell of a row it can test; the backtest (predicting a quarter it never saw) is the final proof.

## Future phases (noted, not built)
- Methodology changes in chat: the analyst states the change, the AI drafts the formula, Python writes it, logs it with a
  named approval and re-onboards, so the workbook and company knowledge change going forward.
- Comparables from PitchBook: suggest comparable sets and multiples for the analyst to approve (logged as decisions).
- If credits bite: run the deterministic steps outside Copilot Studio (Power Automate desktop flow with Python on a PC).
