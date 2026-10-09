# Manual run prompts (build 13.0)

For running the agents by hand while the Copilot Studio workflow is paused. Each prompt goes in a **new conversation** with the agent
named, with the workbooks attached. Replace everything in angle brackets.

## Legend
| Term | Meaning |
|---|---|
| Pass A / pass B | The extractor's two bounded sittings: stages 1-3 (core chain, first usable extraction) / stage 4 to the end |
| RESUME | Continue from the last saved checkpoint; the same prompt is used for pass B and to recover after any timeout |
| Run folder | The SharePoint folder for this run, e.g. `Onboarding/<Company>-test3` |
| Checkpoint files | `checkpoints/*.json` in the run folder: the saved stages; small JSON files |
| READ line | The line the reader prints for each workbook: sheets, cells, formulas, links, SHA-256 fingerprint |

## Before you start
- Use a **new run folder** for build 13.0 (for example `Onboarding/<Company>-test3`). Keep the Test2 folder and its failed trace as they are.
- Attach the **same workbooks to every conversation** of the run, in any order: source ids follow the file names, so every pass and both
  agents get the same ids. Five workbooks plus up to seven small checkpoint files stays within the 20-files-per-conversation cap.
- After the first reply, check the READ lines: every calculation workbook shows formulas (no `READ WARNING: ... no formulas`), and the
  fingerprints are the same in every later pass.
- If a reply dies (StreamInactivityTimeout or anything else), do not resend in the same conversation: open a new one and send prompt 2.

## 1. Extractor - pass A (stages 1-3)
```
ONBOARDING EXTRACTION
Company: <company as the fund workbook names it>
Quarter end: 2026-06-30
Run ID: <COMPANY>-Q2-2026-TEST3
Model: Claude Opus 5
Run folder: Onboarding/<Company>-test3

Use ONLY the <n> attached workbooks as source evidence. Treat them as immutable.
Follow the xpv-onboarding-extractor skill, pass A: stages 1-3. Upload the files each save lists to the run folder as you go.
Stop after stage 3 and end with your JSON line.
```
Expect: the inventory, stage 2 (roles), stage 3 (chain) and a quick verify, ending with `"next_stage": 4` and `"extraction": "provisional"`.
`extraction.json` in the run folder is already usable at this point.

## 2. Extractor - pass B, and RESUME after any timeout
```
ONBOARDING RESUME
Company: <company>
Quarter end: 2026-06-30
Run ID: <COMPANY>-Q2-2026-TEST3
Model: Claude Opus 5
Run folder: Onboarding/<Company>-test3

Use ONLY the <n> attached workbooks as source evidence. Treat them as immutable.
Copy the run folder's checkpoints/*.json and notes.md into your run dir first. Then follow the xpv-onboarding-extractor skill from the
NEXT stage that checkpoint.py status names, through stage 7. Upload after every save. End with your JSON line.
```
If the agent cannot read from the run folder, also attach the run folder's `checkpoints/*.json` and `notes.md` and add the line
`The checkpoint files are attached; put them in run/checkpoints/.` Expect `"next_stage": null` and `"extraction": "final"` at the end.
If it stops early again, send this prompt again in a new conversation; it continues where the last save left off.

## 3. Reviewer - phase 1 (blind)
A new conversation with the **reviewer** agent. Attach the workbooks only - never the extraction or anything from the run folder.
```
ONBOARDING REVIEW - PHASE 1 (BLIND)
Company: <company>
Quarter end: 2026-06-30
Run ID: <COMPANY>-Q2-2026-TEST3
Model: <reviewer model>
Run folder: Onboarding/<Company>-test3

Use ONLY the <n> attached workbooks as source evidence. Treat them as immutable.
Follow the xpv-onboarding-reviewer skill, phase 1: work bottom-up from the source financials to the fund-reported value, save each
stage as you go, and upload to the run folder's reviewer/ subfolder.
Do not open or use extraction outputs, previous runs, prior reviewer outputs, or prior conclusions.
Mark anything the supplied evidence does not establish as unresolved rather than inferring it.
```
Resuming phase 1 after a timeout: the same prompt plus `Copy reviewer/checkpoints/*.json from the run folder into rev/checkpoints/ first.`

## 4. Reviewer - phase 2 (review)
A new conversation with the reviewer. Attach the workbooks, the run folder's `extraction.json` and `reviewer/reviewer_blind.json`.
```
ONBOARDING REVIEW - PHASE 2 (REVIEW)
Company: <company>
Quarter end: 2026-06-30
Run ID: <COMPANY>-Q2-2026-TEST3
Model: <reviewer model>
Run folder: Onboarding/<Company>-test3

The attachments are the <n> workbooks, extraction.json and your fixed phase 1 answer reviewer_blind.json.
Follow the xpv-onboarding-reviewer skill, phase 2: run reconcile --compare-only, settle every contested item from the workbooks with a
typed finding and a checkable claim where one exists, save the findings, run reconcile, and upload review.json, checkpoints_review/ and
out/ to the run folder.
```
The analyst's file is `out/onboarding_review.xlsx` (the same content as `out/onboarding_review.md`).

## 5. Extractor - response (only if phase 2 found something)
A new conversation with the extractor. Attach the workbooks, `extraction.json`, `review.json`, `reviewer/reviewer_blind.json` and
`out/reconcile.json`.
```
ONBOARDING RESPONSE
Company: <company>
Quarter end: 2026-06-30
Run ID: <COMPANY>-Q2-2026-TEST3
Model: Claude Opus 5
Run folder: Onboarding/<Company>-test3

Follow the xpv-onboarding-extractor skill, ONBOARDING RESPONSE: concede or contest every finding that is not "confirmed", with cells
and a checkable claim where you can; run reconcile with --response into out-final/; upload extractor_response.json and out-final/.
```
