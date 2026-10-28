# XPV Valuation Automation — Run Guide (Onboarding)

_Draft 1, October 28, 2026. Extractor build 13.2.6. Replaces the OceanSight Onboarding End-to-End Test. Works for any company: replace `<Company>`, `<YYYY>`, `<Qn>` and `rN`._

## Words used here

| Word | Meaning |
|---|---|
| Extractor | The valuation-extractor agent (build 13.2.6) |
| Test Bench | The valuation-test-bench agent (build 13.2.2, frozen). Development only |
| Gold key | The answer key. Only the Test Bench sees it |
| Run folder | `/Shared Documents/Valuations/2.extractor-outputs/<Company>/<YYYY>/<Qn>_rN`. The Extractor picks N and tells you |
| Review folder | `/Shared Documents/Valuations/4.human_review/<Company>/<YYYY>/<Qn>_rN` |
| Memory | `/Shared Documents/Valuations/5.company_memory/<Company>.memory.json` |
| Hand-off | `/Shared Documents/Valuations/6.generation_handoff/<Company>/<YYYY>/<Qn>_rN/` |
| Pending decision | A review question you left blank. It comes back next run |
| STOPPED | Two different answers for the same item; neither is saved |

**Source package:** all workbooks for the quarter (valuation workbook, fund summary, monthly files). Attach the same set every time.

## Step 1: Extract (two messages)

**1a.** Attach the workbooks. Send:

```
ONBOARDING EXTRACTION
Company: <Company>
Period: <YYYY> <Qn>
MEMORY: /Shared Documents/Valuations/5.company_memory/<Company>.memory.json
```

Leave out the MEMORY line only if the company has no memory yet.

✅ Names a new run folder `<Qn>_rN`. **Write it down.**
✅ Pass A done (stages 1–3), status PROVISIONAL, 0 contradicted.

**1b.** Send:

```
ONBOARDING RESUME
Company: <Company>
Period: <YYYY> <Qn>
Run folder: /Shared Documents/Valuations/2.extractor-outputs/<Company>/<YYYY>/<Qn>_rN
MEMORY: /Shared Documents/Valuations/5.company_memory/<Company>.memory.json
```

✅ Ends with VERIFIED and 0 contradicted.
✅ With memory: shows reused / pending / reopened / new counts. Pending decisions are listed.
❌ If the trace shows files printed as base64, memory retyped, or a stage reopened after stage 8, log it in the AI Development Log.

## Step 2: Grade (development only)

Test Bench. Attach the Gold key, the run's `_extraction.json` and `_verification.json`, and the source workbooks. Send:

```
Gold-score the attached extraction against the attached cleaned Gold key,
using the attached verification file and frozen source workbooks.
Validate the Gold first. If Gold validation fails, do not score.
```

✅ GOLD VALIDATION: PASS · all core answers correct · 0 wrong, 0 omitted, 0 false claims · SOURCE INTEGRITY: SAME_BINARY
❌ If anything fails, stop and diagnose.

## Step 3: Get the review workbook

Ask the Extractor for it in the same conversation.
✅ `<Company>_<YYYY>_<Qn>_rN_Review.xlsx`, every Decision blank, only a handful of decisions.

## Step 4: Fill in the review (you)

| Sheet | Use | Never |
|---|---|---|
| Start here | Type your name in **B6** | |
| Unresolved decisions | **Correct** + your answer in "Your correction", or **Reject**, or blank | **Approve** (there is no suggested answer; the review will be refused) |
| Proposed changes | **Approve**, **Correct** + answer, **Reject**, or blank | Leaving "Always confirm" rows (the multiple) undecided without a reason |
| Memory candidates | **Approve**, **Correct** + answer, **Reject**, or blank | Approving a rule that depends on a decision you left blank |

- Match the "Correction may be" column: Number (`8.75`), Cell (`'Sheet'!D9`) or Text (one sentence).
- Explanations go in **Comment**, never in a number or cell field.
- Leave a decision blank if you can't support it. It stays pending; it is never treated as approved.
- Don't give two different answers for the same item on different sheets.
- Save as `<Company>_<YYYY>_<Qn>_rN_Review.completed.xlsx` in the review folder. **Before attaching, reopen it and check the Decision cells.**

## Step 5: Save to memory

Attach **only** the completed review. Send:

```
ONBOARDING REVIEW
Company: <Company>
Period: <YYYY> <Qn>
Run folder: /Shared Documents/Valuations/2.extractor-outputs/<Company>/<YYYY>/<Qn>_rN
Filled review: attached
MEMORY: /Shared Documents/Valuations/5.company_memory/<Company>.memory.json
```

✅ `REVIEW INPUT:` line shows `made by review_xlsx 13.2.6` and a bundle fingerprint
✅ Review accepted, without asking for workbooks or fetching run files
✅ "created a new memory file" (or entries added) and "coherence OK"
✅ Your blanks are listed as pending
✅ `HANDOFF: ready` or `ready_with_unresolved`
❌ **Refused:** fix only the rows listed, re-save, resubmit. Nothing was written.
❌ If it mentions rebuilding, reformatting or trimming a file, stop and send the trace.

## Step 6: Check memory is reused

Repeat Step 1 with the MEMORY line on a new run folder.
✅ Memory attaches with no warning
✅ Pending decisions listed at the start
✅ Confirmed items reused, not asked again; fewer memory candidates than the first run
✅ Ends VERIFIED

## Done when

- Grading all correct, full source integrity (development runs)
- Memory created, coherent, nothing STOPPED that you didn't expect
- A repeat run reused memory and kept your pending decisions
- Hand-off built

Then move on to quarterly workbook generation (Run Guide section to be added in Phase 6).
