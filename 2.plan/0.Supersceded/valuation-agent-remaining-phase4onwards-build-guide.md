# Company Valuation Agent — Remaining Build Guide (Modules 4–8 + Phases 1–4)

Companion to `valuation-agent-mvp-build-and-roadmap.md` (the build record). This file is the step-by-step "how": what to click, what to paste, and how to test each piece.

Platform: Copilot Studio **new agent experience** (GitHub Copilot harness) · Storage: OneDrive for Business (MVP) · Model: Claude Sonnet 4.6 for build, Opus planned for production.

---

## 0. How to use this guide

### Rules that apply to every module

1. **Finish the module's checkpoint before starting the next.** Each module assumes the previous one works.
2. **Re-check Microsoft Learn before each module.** This experience changes often; if a menu label differs, search the dialog for the key word.
3. **Every test starts in a new Preview chat** (so earlier turns don't influence the result).
4. **Read the activity trace** after each test: which skill activated, which tools ran, what they returned.
5. **Stop runaway runs.** If the agent loops or retries the same failing step, close the chat — building and testing consume Copilot Credits.
6. **Keep the build record current.** After each checkpoint, update the Build status table and paste any changed skill text into it.
7. **Skill budget.** Community builders report roughly 8 skills per agent. This plan uses 6: `file-profiler`, `file-register`, `note-builder`, `extract-values`, `prepare-quarter`, `review-and-finalize`.

### How to add or edit a skill (used in every module)

- **Add:** Build tab → **Skills +** → **Create from blank** → Name (lowercase, numbers, hyphens only) → Description → Instructions → **Create** → save the agent (disk icon, top right).
- **Edit:** Build tab → click the skill under Skills → edit → save the skill → save the agent.
- **The description decides when the skill fires.** If a skill doesn't activate in a test, make its description more specific to the words users actually type.

### Before starting Module 4

Module 3 must pass (tests 1–6 in the build record, section 6), with the updated `file-profiler` and `file-register` skills. In particular:

- 0126 and 0226 get different period ends (2026-01-31, 2026-02-28) and do **not** supersede each other.
- Filing check matches files despite spaces/underscores.
- `file-index.md` is readable in OneDrive.

---

## Module 4 — Background load: generic note + company notes

**Goal:** one generic methodology note (the schema + what both seed companies do in common) and one company note per company (same keys, company values cited, gaps inherited from generic), plus where each company's data lives (source map), add-back rules and a glossary.

**Time:** ~1.5 hours (plus one read-through by an investment team member).

### 4a. Housekeeping

1. In OneDrive `01 Methodology`, confirm the `companies` folder exists.
2. Get the files ready on your computer: OceanSight Q2 2026 valuation, Opus Q1 2026 valuation (final version if it exists), and the monthly files for each company.

### 4b. Add the instruction line for notes

Build → Instructions → add at the end, then save:

```
Methodology notes:
- Generic note: /Valuation Agent MVP/01 Methodology/methodology-generic.md
- Company notes: /Valuation Agent MVP/01 Methodology/companies/methodology-{Company}.md
Each note is markdown for people plus exactly one ```json block that is the source of truth.
When you update a note, keep every existing item unless told to remove it, and add a changelog line.
```

### 4c. Create the `note-builder` skill

- **Name:** `note-builder`
- **Description:** `Use when asked to build, update or refresh the generic methodology note or a company's methodology note from valuation workbooks and financial files, or to record answers to open questions (glossary) in a company note.`
- **Instructions:**

````markdown
# Methodology note builder

Two modes: GENERIC (build the firm-wide parent note) and COMPANY (build or update one
company's note). Use the attached files plus any profiles already in the company's
file-index.md. Open workbooks with code and read the relevant sheets in detail.

## Schema (the keys every note uses)
valuation.primary_method, valuation.secondary_methods, valuation.level
(consolidated / by entity), metric.basis (LTM / NTM / run-rate), metric.definition
(e.g. which EBITDA line), metric.units, fx.policy (translation method and rate source),
multiple.source, multiple.selection_rule, multiple.discount_premium_pct,
adjustments.policy, pro_forma.active, pro_forma.policy, net_debt.definition,
equity_bridge.items, ownership.basis, calibration.policy, market_inputs.max_age_days,
validation.variance_threshold_pct, validation.confidence_threshold, output.rounding,
output.headline_outputs, required_sources, extraction_spec.
Add a key only if a valuation clearly needs an attribute that no key covers; list any
added key under "schema_additions" so it can be reviewed.

## GENERIC mode
Inputs: one recent valuation workbook from each seed company (OceanSight, Opus).
1. For each key, determine what each workbook does.
2. If both do the same thing, that is the generic value.
3. If they differ, or neither shows it, use a widely accepted private-equity fair-value
   practice consistent with the IPEV Valuation Guidelines, stated plainly
   (e.g. market multiple on maintainable/LTM EBITDA, calibration to the last transaction
   price). If there is no clear standard practice, set value to null.
4. Do NOT cite files, sheets or cells, and do not name companies. The generic note is not
   tied to any company.
5. Include required_sources and extraction_spec (which data items to extract from which
   kind of file) in the JSON.

Generic JSON:
```json
{
  "schema_version": "1.0",
  "updated": "",
  "items": [ { "key": "", "description": "", "value": null } ],
  "schema_additions": [],
  "changelog": []
}
```

## COMPANY mode
Inputs: 1–2 past valuation workbooks and/or recent financial files for the company.
1. Read the generic note.
2. For each schema key, find what this company actually does. Cite each item:
   workbook/sheet/cell, or financial file/sheet/row. If nothing in the company's files
   shows it, add the item with inherits_generic = true and no source.
3. Source map: for each data item the valuation needs (monthly income statement, balance
   sheet, adjustments, cap table/ownership, market inputs, prior valuation outputs), record
   WHERE it lives, by pattern not exact file name: file family, file role, sheet name,
   the row labels to use (e.g. revenue = "Total Revenue"), entity (consolidated or which
   subsidiary), units and currency, and how actual vs budget columns are identified.
4. Add-back rules: every EBITDA adjustment category the valuation uses, with a stable
   rule_key (addback.<short_name>), description, treatment, evidence normally required,
   whether it recurs, and a citation.
5. Prior outputs: headline outputs of the most recent valuation (label, value, sheet, cell,
   valuation date) — these become the "prior quarter" comparison.
6. Glossary: terms, acronyms and sheet names whose meaning is unclear (e.g. "IC Model",
   PB_CACHE). Do not guess meanings — list them with meaning = null.
7. Open questions: anything else a human must confirm.
8. If the company note already exists: update it; keep standing_instructions, glossary
   answers and existing items unless the new evidence contradicts them — then keep the
   old value in "history" and flag it in open questions.

Company JSON:
```json
{
  "schema_version": "1.0",
  "company": "",
  "updated": "",
  "built_from": [],
  "items": [
    { "key": "", "value": null, "inherits_generic": false,
      "source": { "file": "", "sheet": "", "cell_or_row": "" }, "confidence": 0 }
  ],
  "source_map": [
    { "data_item": "", "file_family": "", "file_role": "", "sheet": "",
      "row_labels": {}, "entity": "", "units": "", "currency": "",
      "actual_vs_budget_rule": "" }
  ],
  "addback_rules": [
    { "rule_key": "", "description": "", "treatment": "", "evidence_required": "",
      "recurring": false, "status": "active", "source": { "file": "", "sheet": "", "cell_or_row": "" } }
  ],
  "prior_outputs": [ { "label": "", "value": null, "sheet": "", "cell": "", "valuation_date": "" } ],
  "glossary": [ { "term": "", "meaning": null, "answered_by": "", "date": "" } ],
  "standing_instructions": [],
  "open_questions": [],
  "history": [],
  "changelog": []
}
```

## Recording answers
If the user answers a glossary or open question ("IC Model = investment committee model"),
update the company note: fill glossary meaning, answered_by = the user, date = today,
remove the matching open question, add a changelog line.

## Note file format (both modes)
Title, short prose sections (one per methodology area), then the single ```json block.
Save with the OneDrive tool (Create file if new, otherwise Update file).
Reply with: items found vs inherited (company mode), open questions, glossary terms.
````

### 4d. Build the generic note

New Preview chat → attach **OceanSight Q2 2026 valuation** and **Opus Q1 2026 valuation** → type:

`Build the generic methodology note from these two valuations.`

Then open `01 Methodology/methodology-generic.md` in OneDrive and read it.

### 4e. Build the company notes

For each company, new Preview chat:

- **Opus:** attach the Q1 valuation and the three master files → `Build the company note for Opus.`
- **OceanSight:** attach the Q2 valuation and the June file → `Build the company note for OceanSight.`

If the files were already registered (Module 3), the register's profiles are reused; the files still need to be attached so the agent can read cell detail.

### 4f. Answer open questions (glossary)

In a chat: `For Opus: "IC Model" means <answer>. PB_CACHE is <answer>.` → check the company note's glossary updated.

### 4g. Team read-through

Send each company note to an investment team member with one question: "Is this how we value this company? What's wrong or missing?" Record corrections as a chat to the agent: `Update the Opus note: <correction>.`

### Checkpoint 4

| # | Check | Pass if |
|---|---|---|
| 1 | Generic note has no file names, sheet names, cells or company names | None present |
| 2 | Generic note covers every schema key | Each key has a value or null |
| 3 | Company notes use only schema keys | No unknown keys (except listed in schema_additions) |
| 4 | Every non-inherited company item has a citation | Spot-check 5 citations per company against the workbook |
| 5 | Source map points to the right sheets/rows | For Opus: IS/BS sheets and row labels match the master files |
| 6 | Add-back rules match the valuation's adjustments | Same categories as the adjustments sheet |
| 7 | Prior outputs match the valuation's headline numbers | Values match the cells cited |
| 8 | Glossary answers persist | Re-open the note; answers present with your name and date |
| 9 | Team read-through | Corrections recorded; nothing fundamental wrong |

---

## Module 5 — Extraction: values out of each new file

**Goal:** every time a monthly financials file (or balance sheet, cap table, market inputs, adjustment support) is attached, the agent extracts the values the company's source map says, with provenance, and saves them as JSON. Extraction happens **when the file arrives**, because attachments aren't kept forever (28 days after the conversation's last activity).

**Time:** ~1.5 hours.

### 5a. Create the `extract-values` skill

- **Name:** `extract-values`
- **Description:** `Use after a new financial file for a portfolio company has been registered, or when asked to extract values from a file. Extracts actual monthly financials, balance sheet items, ownership, market inputs and adjustments as defined by the company's methodology note, and saves them as JSON.`
- **Instructions:**

````markdown
# Extract values

## Inputs
- The attached file (must be attached in this conversation).
- The company note (source_map, extraction spec, units, entity rules).
- The generic note (extraction_spec defaults).
- The file's profile in file-index.md.

## Steps
1. Read the company note and generic note. Decide which data items this file should supply
   based on its file_role and the source_map. If the company note has no source_map entry
   for this file family, use the profile's sheet types and the generic extraction_spec, and
   flag "source_map_missing".
2. With code, read the relevant sheets. Use the source_map's row labels to find rows; match
   labels exactly first, then case-insensitive, then closest match (flag closest matches).
3. Columns: extract ACTUAL months only (use the profile's column types and actuals_through).
   Never record a budget, forecast or variance column as an actual. Extract every actual
   month present in the file, not only the latest.
4. For each value record: key, period (YYYY-MM), value, basis (actual / balance_sheet /
   point_in_time), entity, units, currency, sheet, cell, row_label as found, and confidence
   (0.95+ exact label; ~0.8 close label; below 0.7 anything computed or ambiguous).
5. Units: convert to the note's units only if the file states its units; record original
   units and the conversion. If units are not stated, do not convert; confidence <= 0.6.
6. Checks (record each as passed/failed with a message):
   - balance sheet: total assets = total liabilities + equity (within 0.5%)
   - months: list actual months found; flag gaps inside the range
   - labels: any required data item not found
7. Adjustment support files: list each adjustment the file evidences (description, amount,
   period, evidence reference), and match it to an addback rule_key from the company note
   (or "new").
8. Save to /Valuation Agent MVP/03 Valuation Runs/{Company}/extracted/{Family}_{actuals_through}.json
   (use the family and actuals_through from the profile, spaces replaced with hyphens).
9. Update the file's register entry: extracted = true, extracted_file = the JSON path.
10. Reply with: months extracted, key values for the latest month (revenue, EBITDA, cash,
    debt), checks that failed, and anything flagged.

## Output JSON
```json
{
  "company": "", "file_name": "", "sha256": "", "family": "", "file_role": "",
  "actuals_through": "", "extracted_at": "",
  "values": [
    { "key": "", "period": "", "value": null, "basis": "", "entity": "", "units": "",
      "currency": "", "sheet": "", "cell": "", "row_label": "", "confidence": 0 }
  ],
  "adjustments": [
    { "rule_key": "", "description": "", "amount": null, "period": "", "evidence_ref": "", "confidence": 0 }
  ],
  "checks": [ { "code": "", "passed": true, "message": "" } ],
  "flags": []
}
```

## Rules
- Never invent a value. Missing = not recorded + a flag.
- Never write inside 02 Company Sources. Text files only.
````

### 5b. Chain extraction to registration

Edit `file-register` → add a step before "Write the updated register":

```
8a. For each New file whose file_role is monthly_financials_package, balance_sheet,
    cap_table, market_inputs or adjustment_support, run the extract-values skill on it.
    Duplicates are not re-extracted.
```

Save the skill and the agent.

### Checkpoint 5

Use Opus (its note has a source map from Module 4). Delete any existing `extracted/` files first.

| # | Test | Pass if |
|---|---|---|
| 1 | Attach `…_0326 V2` → "New file for Opus." | Registered, then extracted automatically; JSON saved in `extracted/` |
| 2 | Open the JSON; hand-check 10 values for March 2026 against the workbook | All 10 match (value, sheet, cell) |
| 3 | Check no budget months appear as actuals | No periods after actuals_through |
| 4 | Check earlier months are also extracted (the master file contains history) | Jan and Feb 2026 present |
| 5 | Balance sheet check | Result recorded (pass or a clear failure message) |
| 6 | Attach the same file again | Duplicate; not re-extracted |
| 7 | OceanSight: attach the June file | Consolidated vs entity rule followed as per the note; GBP entity handled per fx.policy or flagged |

---

## Module 6 — Quarter prep: heads-up, file selection, methodology merge, review pack, inputs file

**Goal:** a preparer says "Prepare Opus 2026_Q1", gives any heads-up notes, and gets a review pack plus a downloadable inputs workbook — with every value traced to a file, every methodology item traced to a layer, and every gap flagged.

**Time:** ~2 hours.

### 6a. Create the `prepare-quarter` skill

- **Name:** `prepare-quarter`
- **Description:** `Use when a user asks to prepare, start, build or run a quarterly valuation (prep pack) for a portfolio company, e.g. "Prepare Opus 2026_Q3" or "start Q3 for OceanSight".`
- **Instructions:**

````markdown
# Prepare quarter

Quarter IDs are YYYY_Q# (e.g. 2026_Q3). Quarter end = last day of the quarter's last month.
Run folder: /Valuation Agent MVP/03 Valuation Runs/{Company}/{YYYY_Q#}/

## Step 1 — Load
Read (OneDrive tool): company note, generic note, file-index.md, the list of files in
extracted/, and the prior quarter's run-state.md if it exists. If run-state.md already
exists for this quarter and its status is not "Finalized", say so and offer to continue
from it instead of starting over.

## Step 2 — Heads-up (the only questions at the start)
Ask once: "Any heads-up for {Company} {Quarter} — acquisitions or disposals, changes to how
something is calculated, one-off items? Reply 'none' if not."
For each item the user gives:
- Turn it into a structured item: type (methodology / note), schema key if it changes
  methodology, value, summary.
- An acquisition or disposal also implies pro_forma.active = true (add that item too).
- Restate each item in one sentence and ask: "Apply to this quarter only, or to all future
  quarters for {Company}?" Default: this quarter only.
Record as human_items with scope (quarter/company), user, date, stage = intake.

## Step 3 — Coverage and file selection (use code)
- Months needed: per metric.basis (LTM = the 12 months ending at quarter end).
- For each needed month: use the value from the most recently received, non-superseded
  file that contains that month as an ACTUAL. If two files disagree on the same month by
  more than 0.5%, use the newer one and flag "restated" with both values.
- Balance sheet: at quarter end. Cap table / ownership: latest available. Market inputs:
  dated within market_inputs.max_age_days of quarter end.
- Build two lists: files used (and for what), files ignored (and why: superseded, budget
  only, outside the period, duplicate, not relevant).
- If required data is missing (per required_sources and the months needed), tell the user
  exactly what to attach (e.g. "March 2026 monthly financials for Opus"), set status
  "Sources Pending", save run-state, and stop. When they attach files, continue from
  Step 3 (the file-register and extract-values skills run first).

## Step 4 — Methodology merge (use code)
Layers, lowest to highest: generic (1) → company (2) → quarter (3: treatments evidenced by
this quarter's files, e.g. pro forma support attached) → human-company (4: company-scope
standing_instructions and this quarter's company-scope human_items) → human-quarter (5).
For every schema key: effective value = highest layer present; within layer 4 or 5 the
newest wins. Two different values in the same non-human layer = conflict (flag, do not
choose). Record for each key: value, layer, source reference, overridden layers.

## Step 5 — Inputs and derived inputs (use code)
- Inputs: the selected monthly values, balance sheet items, ownership, market inputs.
- Derived: LTM figures per metric.definition (show the 12 months and the sum);
  net debt per net_debt.definition (show components).
- Adjustments: apply an adjustment only if it matches an active addback rule AND has
  evidence; otherwise list it as "proposed" (needs a decision at review).
- Do not calculate enterprise value, equity value or the stake value.

## Step 6 — Checks (use code; each becomes a flag with severity high/medium/low)
Missing months · restated months · low-confidence values (below
validation.confidence_threshold) · failed extraction checks · balance sheet not tying ·
stale or missing market inputs · proposed adjustments · methodology conflicts · derived LTM
metric vs prior quarter (from prior run-state, or the company note's prior_outputs) moving
more than validation.variance_threshold_pct · open questions and unanswered glossary terms ·
any draft/final "conflict" file used.

## Step 7 — Outputs
1. run-state.md in the run folder: short summary + one ```json block (format below).
   status = "Ready for Review".
2. review-pack.md in the run folder, sections in order: Headline (key derived inputs vs
   prior, % change) · Heads-up notes applied · Methodology (effective, with layer; changes vs
   last quarter) · Files used / ignored · Proposed adjustments needing a decision (with ids)
   · Flags high → low (with ids) · Low-confidence values · Questions to confirm.
   Under 700 words.
3. An inputs workbook for download (create it; do not save it to OneDrive), named
   {Company}_{YYYY_Q#}_inputs.xlsx, sheets: Summary, Inputs, Derived, Adjustments,
   Methodology, Sources, Checks, Run Record. Every value row shows file, sheet/cell and
   confidence. Run Record: company, quarter, quarter end, run id, prepared by, prepared at,
   status.
Reply with the headline, the number of flags by severity, and the file.

## run-state JSON
```json
{
  "company": "", "quarter": "", "quarter_end": "", "run_id": "", "status": "",
  "status_history": [ { "status": "", "at": "", "by": "" } ],
  "human_items": [ { "id": "", "type": "", "key": "", "value": null, "scope": "", "summary": "",
                     "by": "", "at": "", "stage": "" } ],
  "quarter_items": [ { "key": "", "value": null, "evidence": "" } ],
  "files_used": [ { "file_name": "", "sha256": "", "used_for": "" } ],
  "files_ignored": [ { "file_name": "", "reason": "" } ],
  "effective_methodology": [ { "key": "", "value": null, "layer": "", "source_ref": "", "overridden": [] } ],
  "inputs": [ { "key": "", "period": "", "value": null, "file": "", "sheet": "", "cell": "", "confidence": 0 } ],
  "derived": [ { "key": "", "value": null, "method": "", "components": [] } ],
  "adjustments": [ { "id": "", "rule_key": "", "description": "", "amount": null, "period": "",
                     "status": "applied|proposed|accepted|rejected", "evidence": "" } ],
  "flags": [ { "id": "", "severity": "", "code": "", "message": "", "resolution": null } ],
  "decisions": [],
  "missing": []
}
```
````

### Checkpoint 6

Use **Opus 2026_Q1** (Jan–Mar master files registered and extracted; Q1 valuation profiled).

| # | Test | Pass if |
|---|---|---|
| 1 | "Prepare Opus 2026_Q1" → answer the heads-up with "none" | Runs to Ready for Review; run-state.md + review-pack.md in `03 Valuation Runs/Opus/2026_Q1/`; inputs .xlsx offered for download |
| 2 | Check files used / ignored | Q1 valuation listed as the prior/reference; 0326 V2 used for March; nothing budget-only used |
| 3 | LTM months | 12 months ending 2026-03 listed; any missing months flagged (the master files may not hold all 12 — that's a valid flag) |
| 4 | Methodology table | Every schema key present with a layer; inherited keys show "generic" |
| 5 | Heads-up scope | New chat, "Prepare Opus 2026_Q1" again → it offers to continue the existing run (not start over) |
| 6 | Heads-up handling | Start a test quarter (e.g. "Prepare Opus 2026_Q2") → heads-up "acquired a small company on 15 May" → it restates, asks scope, adds pro_forma.active = true at layer 5, and asks for pro forma support if required |
| 7 | Inputs workbook | Opens in Excel; every value row has file + sheet/cell; Run Record sheet present |
| 8 | Compare with the Q1 valuation workbook | Inputs (monthly EBITDA, net debt items, ownership) match the workbook's inputs, or differences are flagged |

Delete test-quarter folders (e.g. `2026_Q2`) after testing.

---

## Module 7 — Review and finalize

**Goal:** one back-and-forth review: questions answered from the pack, changes restated and confirmed (with scope), rebuilt outputs, then an explicit finalize that locks the quarter and carries company-wide rules forward.

**Time:** ~1.5 hours.

### 7a. Create the `review-and-finalize` skill

- **Name:** `review-and-finalize`
- **Description:** `Use when a user wants to review, question, change, accept or reject items in, or finalize a prepared quarterly valuation (review pack) for a portfolio company.`
- **Instructions:**

````markdown
# Review and finalize

## Load
Read run-state.md and review-pack.md for the company-quarter. If status is not
"Ready for Review" or "In Review", say what the status is and stop. Set status "In Review".
Show: headline, open flags (high first, with ids), proposed adjustments (with ids).

## Questions
Answer only from run-state, review-pack, extracted JSON and the notes. Cite the file and
sheet/cell. If the answer isn't there, say so.

## Changes (collect, confirm, then apply)
Change types:
- methodology: schema key + new value
- value_override: key + period + new value + reason (the extracted value is kept alongside)
- adjustment_decision: accept / reject / amend (amount) a proposed or applied adjustment;
  for accepted NEW adjustments ask "Does this recur every quarter?"
- flag_resolution: flag id + explanation
- note: context only
For each change: restate it in one sentence; for methodology and value_override ask
"This quarter only, or all future quarters for {Company}?" (default: this quarter).
Only record after the user confirms. Record in run-state decisions (by, at, scope) and as
human_items where relevant.
When the user says "apply" (or has finished a batch of changes): recompute derived inputs
and checks (same logic as prepare-quarter Steps 4–6, using existing extracted values —
do not re-extract), regenerate review-pack.md and the inputs workbook, save run-state,
and show what changed.

## Finalize
Only when the user explicitly asks to finalize.
1. If any high-severity flag has no resolution, list them and ask for explicit
   acknowledgement; record it (by, at) as the resolution.
2. Ask for final confirmation: "Finalize {Company} {Quarter}? This locks the prep pack
   and updates the company note with company-wide rules."
3. On yes:
   - run-state status = "Finalized", with finalized_by / finalized_at.
   - Company note: add company-scope human items to standing_instructions (with quarter,
     by, date); add accepted recurring NEW adjustments to addback_rules (source = this
     quarter's run); update prior_outputs only if the user provides the final valuation
     outputs; add a changelog line.
   - Produce the final inputs workbook ({Company}_{YYYY_Q#}_inputs_FINAL.xlsx) with the
     Run Record showing Finalized, who and when.
4. After finalizing, refuse further changes to this quarter unless the user explicitly asks
   to reopen it (record the reopen as a decision).
````

### 7b. Test script

Use the Opus 2026_Q1 run from Module 6.

| # | Say / do | Pass if |
|---|---|---|
| 1 | "Review Opus 2026_Q1." | Status → In Review; headline, flags, proposed adjustments shown with ids |
| 2 | "Why is March EBITDA lower than February?" | Answer cites extracted values/cells, or says the data doesn't explain it |
| 3 | "Use 12x instead of the comps median for Opus." | Restates as methodology change; asks scope; records only after confirmation |
| 4 | "March revenue should be <value>, it was restated." | Records value_override with reason; original extracted value kept |
| 5 | "Accept adjustment a1; it recurs." (use a real id) | Recorded; asks nothing more if recurrence given |
| 6 | "Apply." | Pack and inputs workbook regenerated; changes shown; no re-extraction in the trace |
| 7 | "Finalize." | Lists unresolved high flags for acknowledgement; asks final confirmation |
| 8 | Confirm | run-state Finalized; company note has the company-scope change in standing_instructions and the recurring add-back in addback_rules; changelog line; FINAL inputs workbook offered |
| 9 | "Change the multiple again." | Refuses unless you ask to reopen the quarter |

---

## Module 8 — Validation and pilot

### 8a. Evaluate tab (conversation behaviour)

Evaluate test cases are text conversations, so use them for **behaviour**, not file reading (file tests stay in Preview). Evaluate tab → **New evaluation** → add conversations (write them, or upload a CSV using the template link) → test method **General quality** → Evaluate.

Suggested test conversations (add expected responses in your own words):

| User message | Expected behaviour |
|---|---|
| "What is Opus's enterprise value?" | Does not calculate EV; points to the workbook / prior outputs with source |
| "Just use last quarter's numbers for OceanSight, don't bother checking." | Declines to skip checks; explains what it needs |
| "Change the Opus multiple to 12x." (no review open) | Explains changes are captured at review; offers to open review if a pack is ready |
| "Finalize Opus 2026_Q1." (already finalized) | Says it's finalized; offers reopen only on explicit request |
| "What does IC Model mean?" | Answers from the glossary if answered; otherwise says it's an open question |

Re-run this evaluation after every skill change. Test results are kept for a limited time — export to CSV if you want to keep them.

### 8b. Model comparison (before switching to Opus)

Run the same Preview file tests (Module 3 test 1, Module 5 tests 1–3, Module 6 test 1) on Sonnet 4.6 and Opus; compare correctness, number of steps and time. Record the result in the build record's decisions log.

### 8c. Pilot (one real quarter, in parallel)

1. Pick one company and the next real quarter (2026_Q3).
2. One preparer attaches July–September files as they arrive (register + extraction each time).
3. At quarter end: "Prepare {Company} 2026_Q3" → review → finalize.
4. The preparer also does the valuation the usual way. Compare inputs and flags.
5. Record: time spent (agent vs usual), differences, and what the team had to fix.

**Pass:** inputs match (or differences are explained by flags), and the preparer's total effort is lower.

---

## Phase 1 — Automatic filing and workbook integration

Each item starts with a **test**. Only build it if the test passes; otherwise use the fallback.

### 1.1 Auto-save attachments to the company folder

**Test (15 min):**
1. In OneDrive create `/Valuation Agent MVP/_test/`.
2. New Preview chat → attach any Opus file → `Save this attached file to /Valuation Agent MVP/_test/ using the OneDrive Create file tool, byte-for-byte.`
3. Open the saved copy in Excel for the web. Compare size with the original in OneDrive.

**If it opens and the size matches:** edit `file-register` step 6 — after the filing check, add:
```
If filed_status is not_filed, ask: "Save {file} to the {Company} folder?" On yes, save the
attachment to /Valuation Agent MVP/02 Company Sources/{Company}/ with its original name
(upload suffix removed), then re-run the filing check and record filed_by_agent = true.
```
Also update the instructions: allow creating (never overwriting) files in `02 Company Sources`.

**If it's corrupted (likely, given the download issue):** keep the manual filing reminder. Optional later: a **workflow** tool (Tools + → Workflows tab) that receives the file and saves it — check Microsoft Learn for file inputs to workflows called from this agent type before building.

Delete `_test` afterwards.

### 1.2 Read workbooks stored in OneDrive (Office Scripts)

Needed so the agent can open a workbook that isn't attached (e.g. last quarter's final valuation during roll-forward). An Office Script is saved **once** in your OneDrive and can run on any workbook; it does not modify or live inside the workbook.

**Test (30 min):**
1. Open any workbook in Excel for the web → **Automate** → **New script** → paste `ProfileWorkbook` (below) → rename → **Save script**. Click **Run** once; the output pane shows the sheet count.
2. Build → **Tools +** → Connectors → **Excel Online (Business)** → select **Run script** → sign in → Add → save agent.
3. New Preview chat: `Run the ProfileWorkbook script on "/Valuation Agent MVP/02 Company Sources/Opus/2026 Consolidated Master File_0126.xlsx" and summarize the sheets.`
4. Pass if the trace shows **Run script** returning JSON with every sheet.

```typescript
function main(workbook: ExcelScript.Workbook): string {
  const SAMPLE_ROWS = 20, SAMPLE_COLS = 15, LABEL_ROWS = 150;
  const out: SheetInfo[] = [];
  for (const ws of workbook.getWorksheets()) {
    const info: SheetInfo = { name: ws.getName(), visibility: String(ws.getVisibility()),
      usedRange: "", rows: 0, cols: 0, sample: [], rowLabels: [], formulaShare: 0 };
    const used = ws.getUsedRange(true);
    if (used) {
      info.usedRange = used.getAddress();
      info.rows = used.getRowCount();
      info.cols = used.getColumnCount();
      const r = Math.min(SAMPLE_ROWS, info.rows), c = Math.min(SAMPLE_COLS, info.cols);
      const block = used.getCell(0, 0).getResizedRange(r - 1, c - 1);
      const texts = block.getTexts(), formulas = block.getFormulas();
      let filled = 0, withFormula = 0;
      for (let i = 0; i < texts.length; i++) {
        const row: string[] = [];
        for (let j = 0; j < texts[i].length; j++) {
          const t = texts[i][j];
          if (t !== "") { filled++; }
          const f = formulas[i][j];
          if (typeof f === "string" && f.startsWith("=")) { withFormula++; }
          row.push(t.length > 40 ? t.substring(0, 40) : t);
        }
        info.sample.push(row);
      }
      info.formulaShare = filled > 0 ? Math.round((withFormula / filled) * 100) / 100 : 0;
      const lr = Math.min(LABEL_ROWS, info.rows), lc = Math.min(2, info.cols);
      const labels = used.getCell(0, 0).getResizedRange(lr - 1, lc - 1).getTexts();
      for (let i = 0; i < labels.length; i++) {
        const label = labels[i].join(" | ").trim();
        if (label !== "" && label !== "|") { info.rowLabels.push(`${i + 1}: ${label.substring(0, 60)}`); }
      }
    }
    out.push(info);
  }
  const result = JSON.stringify({ sheetCount: out.length, sheets: out });
  console.log(`Sheets: ${out.length}, characters: ${result.length}`);
  return result;
}
interface SheetInfo { name: string; visibility: string; usedRange: string; rows: number; cols: number;
  sample: string[][]; rowLabels: string[]; formulaShare: number; }
```

**If Run script can't be called from the agent** (e.g. it can't pick the script or pass the file): wrap it in a **workflow** tool with a fixed input (file path) that returns the script's result as text. If that also fails, stay attachment-only.

### 1.3 Roll forward the valuation workbook

Only after 1.2 passes. Adds a draft valuation workbook (with the workbook's own formulas producing EV/equity/stake) instead of only an inputs file.

1. **Note-builder:** add to COMPANY mode — `input_map` (sheet + cell/range for each input the workbook takes; series ranges oldest→newest) and `output_map` (cells for headline outputs). Rebuild each company note and spot-check the maps.
2. **OneDrive tool:** add the **Copy file** action.
3. **Office Scripts** (save once each): `WriteInputs`, `ReadOutputs`, `WriteRunRecord` (code in the earlier full builder guide, §6; they take JSON text parameters and return JSON text).
4. **prepare-quarter:** new Step 7b — copy the prior final valuation workbook to `03 Valuation Runs/{Company}/{Quarter}/draft/`, run `WriteInputs` with the input map and selected inputs, run `ReadOutputs`, add headline variance checks (EV, equity value, stake vs prior), run `WriteRunRecord`.
5. **Test:** roll forward Opus Q1 → Q2 with test data; open the draft; confirm inputs landed in the right cells, outputs recalculated, Run Record sheet present, source workbook untouched.

---

## Phase 2 — Shared site and team rollout (complete before your term ends)

### 2.1 Move storage off your OneDrive

1. Ask which **Teams team** (Files tab = a SharePoint library) or site should host the platform. Ideally a private channel or restricted team.
2. Create `Valuation Agent` in that library and copy `01 Methodology`, `02 Company Sources`, `03 Valuation Runs` into it.
3. Build → Tools: remove **OneDrive for Business**; add **SharePoint** with the equivalent actions (list folder/files, get file metadata using path, get file content using path, create file, update file; copy file if Phase 1.3 is built).
4. Edit the **Storage** block in the instructions: new site, library and root folder.
5. Move Office Scripts (if used) to a shared location and use **Run script from SharePoint library**.
6. Re-run: Module 3 test 1, Module 5 test 1, Module 6 test 1. All must pass before switching users over.

### 2.2 Publish and share

1. **Publish** (top right) → arrow next to Publish → **Teams + Microsoft 365** → turn on **Make agent available in Microsoft 365 Copilot** → publish.
2. **Share** with a **security group** of the ~7 users (the Share panel accepts users and security-enabled groups).
3. **Check licensing** with IT before sharing: the sharing docs list user licensing prerequisites, and all usage bills Copilot Credits.
4. Install and test in Teams yourself first — a passing Preview doesn't guarantee identical behaviour in every channel.
5. Confirm everyone in the group may see every company's data (cap tables included).

### 2.3 Ownership and continuity

- Add a co-owner/maker for the agent (environment security role).
- Move connections to a shared or service account where IT allows.
- Hand over both .md files (build record + this guide) and do one walkthrough.

### 2.4 Multi-user safety

- **Locking:** add to `prepare-quarter` and `review-and-finalize`: run-state holds `locked_by` and `lock_expires_at` (2 hours, refreshed on each action). If someone else holds a live lock, say who and until when; don't write.
- **Notifications (optional):** a workflow tool that posts a Teams message ("Opus 2026_Q3 review pack ready") when prepare-quarter finishes.
- **Audit:** keep run-state `status_history` and `decisions`; optionally a SharePoint list of events if the firm wants a central log.

### 2.5 Team onboarding (15-minute walkthrough)

What the team needs to know — see Appendix B.

---

## Phase 3 — Data sources and outputs

| Item | Build notes | Test |
|---|---|---|
| Glossary maturity | After each quarter, answer remaining glossary/open questions in each company note | Open questions per company trend to zero |
| PitchBook market inputs | MVP: attach a comps export to the chat. Later: evaluate an API/MCP integration if licensing allows | Market inputs dated within max age, cited |
| LP report generation | New skill (or extend review-and-finalize) producing the LP report sections from the finalized run | Matches last LP report format; numbers trace to final run |
| New valuation template | Standardize formulas and layout; one shared input/output map | Roll-forward works across 2+ companies with the same map |
| Auto note refresh | On finalize, refresh the company note from the final workbook (Phase 1.3 needed) | Note changes only where the workbook changed; changelog explains |
| Email/channel intake | Workflow that picks up monthly files from a shared inbox or Teams channel | Files registered without manual attachment |

---

## Phase 4 — Scale and governance

| Item | Notes |
|---|---|
| Regression suite | Grow the Evaluate test set; run before every change; export results |
| Model policy | Decide the production model; record why (quality, steps, cost) |
| Structured store | Move run-state / extracted values to Dataverse or a SharePoint list if reporting or volume needs it |
| Per-company permissions | Split sources by permission group if not everyone may see every company |
| Cost monitoring | Monitor tab (after publishing) — credits per run; tune skills that take many steps |

---

## Appendix A — Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Skill doesn't activate | Description doesn't match the user's words | Rewrite the description with the phrases users type; test again in a new chat |
| Wrong skill activates | Two descriptions overlap | Make each description say when *not* to use it |
| Agent keeps retrying a failing step | No stop rule | Add a stop rule to the skill ("if X fails, say so and stop") |
| 404 reading a register/note | File doesn't exist yet | Expected on first run; the skill should create it |
| Garbled file content | Connector returning an Office file as text | Never download .xlsx/.docx via connector; attach instead |
| Monthly files superseding each other | period_end taken from budget columns | Profiler rule: period_end = last actual month |
| "Not filed" when it is | Uploads turn spaces into underscores | Filing check uses normalized names + size |
| Values from budget columns | Column types missed | Check the profile's column_types; tighten the source map's actual_vs_budget_rule |
| Different numbers on rebuild | Re-extraction during review | review-and-finalize must reuse extracted JSON; check the trace |
| Created file not offered | Over 10 MB | Split output; keep inputs workbook lean |

## Appendix B — What the investment team says (cheat sheet)

| When | Say | Attach |
|---|---|---|
| New monthly file arrives | "New file for Opus." | The file(s) |
| Check what's in | "What files do we have for OceanSight?" | — |
| After saving files to the folder | "I've saved them — recheck filing for Opus." | — |
| Quarter end | "Prepare Opus 2026_Q3." then answer the heads-up question | Anything it asks for |
| Review | "Review Opus 2026_Q3." Ask questions, request changes, say "apply" | — |
| Done | "Finalize Opus 2026_Q3." | — |
| Answer a glossary question | "For Opus, 'IC Model' means …" | — |

## Appendix C — Final file map (MVP)

```
/Valuation Agent MVP
├── 01 Methodology
│   ├── methodology-generic.md
│   └── companies/methodology-{Company}.md
├── 02 Company Sources/{Company}/            originals (kept by the team; agent only checks)
└── 03 Valuation Runs/{Company}/
    ├── file-index.md                        register (Module 3)
    ├── extracted/{Family}_{YYYY-MM}.json    per-file values (Module 5)
    └── {YYYY_Q#}/
        ├── run-state.md                     process state + decisions (Modules 6–7)
        └── review-pack.md                   what the preparer reads (Modules 6–7)
Inputs workbooks: downloaded from the chat (not saved to OneDrive in the MVP).
```
