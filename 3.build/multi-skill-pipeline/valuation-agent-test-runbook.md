# Valuation agent: end-to-end test runbook

This runbook takes the demo workbook through the full pipeline in one new chat: structure, mapping profile, replay, certification, then a Q3 refresh.

**Keep everything in one chat from Step 1 to Step 11.** The sandbox keeps files only for the length of a conversation.

---

## Glossary (read first)

**Step codes** (used inside the skills):
- **P1–P5, Python steps.** Deterministic scripts that read, trace, merge, check and report.
- **J1–J3, Judgment steps.** Decisions the agent (the language model) makes and writes to a file:
  - J1: choose the key outputs;
  - J2: classify the inputs;
  - J3: write the workbook map.

**Real-data tests** (Part D of this runbook):
- **D1, Generate test.** Build a valuation from statements alone, then compare it with the true workbook.
- **D2, Backtest.** Use last quarter's workbook to predict this quarter, then compare with the real one.
- **D3, Full pipeline.** Run the whole existing-workbook process on a real company.

**Modes of the valuation-refresh skill:**
- **Replay.** Rebuild a period from its own statements, to check the lookup rules and the writing work.
- **Backtest.** Predict a period the rules have never seen. This is the strongest test.
- **Refresh.** Build next quarter's draft.

**Rule discovery.** The system tries every statement line, across all monthly files, with every operation: value at the period, 3- or 12-month sum, YTD difference. It keeps the rule that reproduces the workbook's number. Possible results:
- **reproduced_all:** the rule rebuilds every tested cell in the block.
- **reproduced_some:** usually because earlier periods aren't covered by the statements supplied.
- **ambiguous:** two different rules rebuild it equally well.
- **no_rule:** nothing in the statements rebuilds it. This usually means it's an analyst's judgment, such as add-backs.
- **not_testable:** a rate or multiple that doesn't come from statements.

**Concept statuses:**
- **EXECUTABLE:** a runnable rule that reproduced the workbook.
- **EXECUTABLE_UNVERIFIED:** a rule the analyst stated, which the replay will test for the first time.
- **MANUAL:** a manual input or carry-forward.
- **EXCEPTION:** no runnable rule yet.

**Historical kept:** an earlier-period cell the statements don't cover. It's kept from the workbook and reported as not proof.

**Statuses:**
- **Technical status** (COMPLETE / REVIEW_REQUIRED / BLOCKED): the machine checks.
- **Business review** (PENDING / CONFIRMED): whether a named person has confirmed the classifications.
- **Profile status** (DRAFT / READY_FOR_REPLAY): whether the mapping profile is approved and complete.
- **Certification** (CERTIFIED): a replay or backtest passed and a named person signed it off.

**Statement layouts** (detected automatically; a change from the company's usual layout is flagged):
- one period per file;
- months across columns;
- sheet per month.

A **statement pack check** lists undated files, duplicate or missing months, and labels repeated on the same sheet (for example a consolidated block and a subsidiary block).

**Other abbreviations:** LTM = last twelve months; EV = enterprise value; EBITDA = earnings before interest, taxes, depreciation and amortization.

---

## Part A. One-time setup in Copilot Studio

Skip this part if nothing has changed since your last run.

### A1. Skills

Open the agent, then **Skills**. Remove any older versions, then upload the latest zips:

| Skill | File |
|---|---|
| valuation-workbook-schema | `valuation-workbook-schema.zip` |
| valuation-mapping-profile | `valuation-mapping-profile.zip` |
| valuation-refresh | `valuation-refresh.zip` |
| valuation-generate | `valuation-generate.zip` |
| sandbox-env-check | `sandbox-env-check.zip` |

Check that exactly these five skills are listed.

### A2. Instructions

Replace the entire **Instructions** field with the block in Part C, then **Save**.

### A3. Files to have ready on your computer

- `tricky_valuation.xlsx`
- `test_source_statements.xlsx` (the **Q2** statements)
- `test_source_statements_q3.xlsx` (the **Q3** statements)

---

## Part B. The test chat

Start a new test chat, then go through the steps in order. For each step, upload the files listed (if any), send the prompt exactly as written, and check the result against **Expect**.

### Step 0. Self-tests (about 2 minutes)

**Prompt:**
```
Run the valuation-refresh self-test, then the valuation-generate self-test.
```
**Expect:** `SELFTEST: PASS` twice: 11 passes for refresh and 8 for generate.

### Step 1. Structure and mapping profile

**Upload:** `tricky_valuation.xlsx` and `test_source_statements.xlsx`

**Prompt:**
```
Map this workbook and build the mapping profile from these statements.
```

**Expect:**
- `Structure initialization: technical status REVIEW_REQUIRED; business review PENDING.`
- `PROFILE STATUS: DRAFT`
- Four `reproduced_all` results: Revenue, COGS and SG&A as 3-month sums, and Net debt as a value at the period end.
- One `no_rule` (add-backs) and three `not_testable` (the multiple, the discount, and B6).
- `PROFILE STATUS: READY_FOR_REPLAY`. Approvals aren't needed to test.

### Step 2. Business review and mapping rules

**Prompt:**
```
Corrections - reviewed by Aria:
Inputs!B6: assumption, changes each quarter: yes, note: management adjustment factor.
Inputs!B4: changes each quarter: no.
Confirm all blocks - reviewed by Aria.
Mapping rules:
- EV/EBITDA multiple, one-off costs added back, and the adjustment factor (Inputs!B6): manual_input each quarter, missing: manual_input.
- Illiquidity discount: carry_forward, missing: carry_forward_and_flag.
- Revenue, COGS, SG&A: roll_window, quarter_sum_of_months, entity Test Co, filename pattern src_q<N>_statements.xlsx, reconciliation: three months sum to the quarter, missing: block_and_flag. The rightmost column is the newest period.
- Net debt: replace_period_value, quarter_end_balance, entity Test Co, filename pattern src_q<N>_statements.xlsx, reconciliation: equals balance sheet net debt, missing: block_and_flag.
```

**Expect:**
- `technical status COMPLETE; business review CONFIRMED`, with 8/8 blocks confirmed.
- The profile is rebuilt as `DRAFT`, with the rules above.

### Step 3. (Optional) Record approvals

Approvals are recorded, but they're no longer required. The named sign-off happens at certification (Step 7). Skip this step, or send:
```
Approve all concepts - Aria
```

### Step 4. Replay

**Prompt:**
```
Replay this profile.
```

**Expect:**
- `PLAN STATUS: READY`: 17 cells, 13 rebuilt by rule, 0 historical and 0 exceptions.
- If you see `PLAN STATUS: BLOCKED`, the agent must stop and list the exceptions. That's the correct behaviour.
- A download named `..._replay_draft.xlsx`.

### Step 5. Excel step for the replay draft

1. Download the replay draft.
2. Open it in **desktop** Excel. If a yellow bar appears, click **Enable Editing**.
3. Wait until the status bar no longer shows "Calculating". If calculation is set to manual, press **Ctrl+Alt+F9**.
4. Press **Ctrl+S**. Keep the `.xlsx` format and the same file name.

### Step 6. Check the replay

**Upload:** the saved replay draft

**Prompt:**
```
Here is the replay draft saved in Excel. Check it.
```

**Expect:**
- `CHECK STATUS: REPLAY_PASS`, with all 6 checks PASS.
- Fair value of `28812.875` in both the original and the rebuilt workbook.
- A "By concept" table showing every concept fully reproduced.

The replay now uses the same lookup as refresh: the source line by label, and periods by header date. That makes a pass meaningful. It is still weaker than a backtest (Part D2), because the rules are tested on the period they were built from.

### Step 7. Certify

**Prompt:**
```
Certify the replay - Aria
```

**Expect:** a `certification.json` file with status `CERTIFIED`.

### Step 8. Q3 refresh

**Upload:** `test_source_statements_q3.xlsx`

**Prompt:**
```
Refresh for the period ending 2026-09-30 using these statements, with last quarter's final being the replay draft I saved in Excel. Manual inputs: Inputs!B3 = 9.0, Adjustments!B1 = 150, Inputs!B6 = 1.1.
```

**Expect:**
- `PLAN STATUS: READY`, with 17 cells and 0 exceptions.
- Net debt of `3000`.
- A note saying the profile was certified by replay only. This is expected, because there is no prior-quarter workbook for the demo.
- The illiquidity discount carried forward at `0.15`.
- A download named `..._refresh_draft.xlsx`.

### Step 9. Excel step for the refresh draft

Same as Step 5, using the refresh draft.

### Step 10. Check the refresh

**Upload:** the saved refresh draft

**Prompt:**
```
Here is the refresh draft saved in Excel. Check it.
```

**Expect:**
- `CHECK STATUS: DRAFT_READY_FOR_REVIEW`.
- Fair value moves from `28812.875` to `26313.45`, a change of -8.7%. This is under the 15% threshold, so there is no output flag.
- A variance flag on `Quarterly!E4 [SG&A] moved +42.9%`. This spike was planted in the test data on purpose.

### Step 11. Approve the draft

**Prompt:**
```
Approve refresh draft - Aria
```

**Expect:** the approval is recorded in the summary.

### What to send back

- The final summary text from Steps 1, 6 and 10.
- The `_check_report.md` files from Steps 6 and 10.
- For any step that did not match its Expect, the agent's trace.

---

## Troubleshooting

| What you see | Cause | What to do |
|---|---|---|
| Net debt is `no_tie` in Step 1 | The Q3 statements were uploaded instead of Q2 | Start a new chat and use the Q2 file |
| The agent stops and asks for key outputs | An old version of the schema skill is loaded | Re-upload `valuation-workbook-schema.zip` |
| `PLAN STATUS: REFUSED` | The profile or certification is missing, unapproved, or out of date | Read the reasons it gives. Usually Step 3 or Step 7 was skipped |
| Check reports "Excel recalculated the draft: FAIL" | The file was uploaded without being opened and saved in desktop Excel | Repeat the Excel step |
| An approval resets unexpectedly | Something the approval covered has changed: its targets, rules, source file or template | Expected behaviour. Re-approve after reviewing |
| `EXTRACTION_ERROR`, `PLAN_ERROR`, `MAPPING_ERROR` or `BUILD_ERROR` | A script bug | Send me the error line and the trace |
| `MAPPING STATUS: NEEDS_ANSWERS` keeps repeating | An answer did not reach answers.json | Reply with every answer in one message, using the field names in the prompt |
| Generated net debt looks too high or too low | Several debt lines were summed, or a line was missed | Check the FLAG line and mapping.json, then answer with a `label_overrides` correction |

---

## Part C. Agent instructions (paste over the whole field)

```
ROLE
You help XPV analysts map valuation workbooks and prepare them for quarterly updates. You map
structure, inputs and source lineage, run replays, backtests and quarterly refresh drafts, and
generate baseline valuations for new companies from their statements. You do
not value companies, give investment opinions, or edit the user's workbooks by hand.

HOW YOU WORK
- Runs are autonomous: once you have the files you need, complete the whole workflow without
  asking questions. Make the judgment calls the skills assign to you, record them in the skill's
  decision files, and report every decision at the end for the user to confirm or correct.
- The only pause is the Excel recalculation step (hand over the file and wait for the saved copy).
  Never ask questions during a run: missing answers become flagged assumptions, and every question,
  assumption, flag and check goes into one review list in the final summary.
- Python scripts do all deterministic work (reading, tracing, merging, validating, control checks,
  matching, planning, writing, checking, reporting, manifests). You do only the judgment steps:
  choosing key outputs and controls, classifying inputs, grouping concepts, short explanations.
- Every script ends with a NEXT REQUIRED STEP line. Do exactly that next. Never give a final
  summary while a NEXT REQUIRED STEP is outstanding.
- Everything you decide is a proposal. Technical status is separate from business review.
  Never describe results as verified or correct.

SKILL USE
- Workbook uploaded (with or without a saved input map) -> valuation-workbook-schema.
- Workbook + source statements uploaded -> valuation-workbook-schema, then
  valuation-mapping-profile in the same run, then one final summary covering both.
- Source statements + a saved input map -> valuation-mapping-profile.
- Requests to replay, backtest, certify, refresh, roll forward or produce a quarterly draft, or to run
  the refresh self-test -> valuation-refresh.
- Financial statements for a company with no mapped workbook, or a request to generate a valuation from
  statements (optionally compared with an uploaded actual workbook), or the generate self-test ->
  valuation-generate.
- Questions about the environment (libraries, programs, recalculation) -> sandbox-env-check.
- If a required file is missing, say which one and stop.
- Never write your own code to read or fill a workbook or statements, and never modify, import or
  debug skill scripts. If a script reports an error, show the error line and stop.

CORRECTIONS, CONFIRMATIONS AND APPROVALS
Only act on these when the user's latest message states them explicitly.
- Corrections and mapping rules: apply through the skill's decision files, re-run from the step
  the skill names, and report the new status. Record the user's own words in the notes.
- Confirmations ("confirm ... - reviewed by <name>") set reviewed_by on exactly the blocks named.
- Reporting scope ("Reporting scope: <sheet> yes/no - reviewed by <name>"): write scope.json as the
  skill describes.
- Controls: change a control only when the user says so. Never change an expected value to make a
  control pass.
- Approvals are optional and never needed to test. Certifications and draft approvals: only for the
  items the user names, with the person they name. Never set a reviewer, approver or certifier the user
  did not name.
- Rule corrections ("revenue is the sum of monthly Total Revenue") become the concept's executable rule;
  text in notes is never executed.
- A plan with exceptions (BLOCKED) stops the run: report the exceptions, do not do the Excel step.
- Manual input values are copied exactly as the user gives them.

NUMBERS
- Never calculate, estimate, or project numbers. Every figure you state must come from script
  output, cited as Sheet!A1, shown exactly as printed (no added units, currency or %).
- For scenario questions, explain that this agent maps and refreshes workbooks from approved
  sources, and point to the input cells that would change.

FILES
- The sandbox is deleted after each conversation. Save every file the skill lists, including run
  manifests and certification.json, through the SharePoint Create file tool (pass the sandbox path
  as the file content), or return them as downloads if no tool is connected.
- Tell the user the exact name and location of each saved file and the run_id.
- The saved input map, mapping_profile.json and certification.json are the reusable records;
  tell the user to upload them with the workbook next time.

FINAL SUMMARY (the only long message in a run)
1. The status line the scripts tell you to use (structure, profile, plan or check status),
   quoted exactly, then the reconciliation line where there is one.
2. The CONTROLS LINE and GATES LINE exactly as printed. Gates are not controls.
3. Workbook Map (skill template, short) for structure runs.
4. Decisions made: key outputs and controls with reasons, classification breakdown, concepts.
5. The Review list from the report, unchanged and in its order: highest priority (impact x
   uncertainty) first. This is the only list the analyst needs to work through.
6. Files saved with locations, and the run_id.
7. One line on the next action.
Never say analyst input is "none", or that passing gates means the mapping is correct.

STYLE
- No progress narration during the run.
- Be concise. Use tables only where the skill templates use them.
- Write UNCERTAIN where the evidence doesn't settle something; never guess to fill a gap.
```

---

---

## Part D. Real-data tests (OceanSight)

Run D1 now. It needs only the one true workbook you have. Run D2 as soon as an earlier quarter's workbook is available. Use a new chat for each.

### D1. Generic generation vs the true workbook (possible now)

**What it tests:** whether the generic template, given only the statements and a few answers, reaches the analyst's valuation. The differences it finds are the company-specific logic the generic template lacks.

1. **Upload:** OceanSight's Q2 source statements (Excel or CSV), the OceanSight Q2 valuation workbook, and its saved input map from the schema run (if you have it).
2. **Prompt** (fill in the values from the analyst or the true workbook):
```
Generate a valuation for OceanSight from these statements and compare it with the uploaded valuation workbook.
Answers: company OceanSight, period end 2026-06-30, statements in <units>, report in <units>,
EV/EBITDA multiple <x> weight 0.75, EV/Revenue multiple <y> weight 0.25, EBITDA adjustments <n or 0>,
illiquidity discount <d>, XPV ownership <p>, claims ahead of common equity <c or 0>.
```
3. **Expect:** `MAPPING STATUS: READY` or `READY_WITH_ASSUMPTIONS`, then a generated workbook. The agent asks nothing during the run; any assumptions are listed at the end. Do the Excel step and upload the saved file with `Here is the generated workbook saved in Excel. Compare it.`
4. **Result:** `GENERATED_MATCHES` or `GENERATED_DIFFERS`, with a metric-by-metric table and an explanation of the EV gap (EBITDA effect versus multiple effect).
5. **How to read it:**
   - EBITDA differs: the statements' line choice or the add-backs differ from the analyst's.
   - The implied multiple differs from the input multiple: the true workbook's EV formula has extra terms.
   - Net debt differs: debt lines, leases, or a cash definition.
   - Equity or XPV value differs after EV matches: preferred shares, the waterfall, or ownership.

   Each difference is a question for the analyst, or a rule to add to the generic template.

If you take the multiples and discount from the true workbook, those items will match by construction. The test then isolates what matters: whether the statements are read correctly, and whether the mechanics hold.

**Send back:** the final summary, the `_vs_actual.md` report, and `mapping.json`.

### D2. Backtest (the strongest test; needs an earlier quarter)

**Upload:**
- the prior quarter's final workbook (e.g. Q1);
- the Q2 statements;
- the true Q2 workbook;
- the Q2 input map, `mapping_profile.json` and `matches.json`.

**Prompt:**
```
Backtest the profile: prior workbook is the Q1 file, actual is the Q2 workbook, period end 2026-06-30.
```
Do the Excel step, then upload the saved file with `Here is the backtest draft saved in Excel. Check it.`

**Expect:** `BACKTEST_PASS`, or a "By concept" table showing which concepts did not reproduce. Certify only after a pass: `Certify the backtest - <name>`.

### D3. Full pipeline on OceanSight's own workbook

This is the same as Part B Steps 1–7, using the real workbook and its **same-period** statements. The analyst's answers replace the demo corrections in Step 2. Use D2 instead of the replay whenever an earlier quarter exists.

