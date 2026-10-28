# OceanSight Regression for Build 13.2.6

## Words used here

| Word | Meaning |
|---|---|
| Extractor | The `valuation-extractor` agent, build 13.2.6 |
| Review bundle | A hidden sheet inside the review workbook carrying everything the review read needs, with its own fingerprint |
| Pending decision | A review question you left blank. It comes back next run |
| N | The run number the Extractor gives you in Step 1 |

**The five workbooks:** the final OceanSight Q2 2026 source package.

## Before you start

- [ ] Extractor updated to 13.2.6 (skill and instructions)
- [ ] To see "created a new memory file" in Step 4, move `5.company_memory/OceanSight.memory.json` to `0.SS/` first. If you keep it, "appended" is the correct result instead.
- [ ] Do not reuse or trust the earlier Opus review conversation

---

## Conversation 1: extract and build the review

**Step 1.** Attach the five workbooks. Send:

```text
ONBOARDING EXTRACTION
Company: OceanSight
Period: 2026 Q2
```

✅ It names a new run folder `Q2_rN`. **Write it down.**

**Step 2.** Same conversation, no attachments needed. Send:

```text
ONBOARDING RESUME
```

✅ Ends VERIFIED, 0 contradicted.

**Step 3.** Same conversation. Send:

```text
ONBOARDING REVIEW
Create a fresh review workbook.
```

✅ `OceanSight_2026_Q2_rN_Review.xlsx` saved.

**Then close this conversation.**

---

## You: fill in the review

- [ ] Fill it in as usual. **Leave one decision blank on purpose** and note which one.
- [ ] Save it as `OceanSight_2026_Q2_rN_Review.completed.xlsx`.

---

## Conversation 2 (new): read the review, write memory

**Step 4.** Attach **only** the completed review, with no source workbooks. Send:

```text
ONBOARDING REVIEW
Company: OceanSight
Period: 2026 Q2
Run folder: /Shared Documents/Valuations/2.extractor-outputs/OceanSight/2026/Q2_rN
Filled review: attached
MEMORY: /Shared Documents/Valuations/5.company_memory/OceanSight.memory.json
```

✅ `REVIEW INPUT:` line shows made by `review_xlsx 13.2.6` and a `bundle` fingerprint
✅ `review accepted`
✅ It doesn't ask for the source workbooks and doesn't fetch or retype any run file
✅ Memory: "created a new memory file" (or "appended" if you kept the old one), and "coherence OK"
✅ Your deliberate blank is listed as pending
✅ `HANDOFF: ready_with_unresolved`, saved to `6.generation_handoff/OceanSight/2026/Q2_rN/`

❌ If the reply mentions rebuilding, reformatting or trimming a file, stop and send me the trace.

---

## Conversation 3 (new): check memory is reused

**Step 5.** Attach the five workbooks. Send:

```text
ONBOARDING EXTRACTION
Company: OceanSight
Period: 2026 Q2
```

**Step 6.** Same conversation. Send:

```text
ONBOARDING RESUME
MEMORY: /Shared Documents/Valuations/5.company_memory/OceanSight.memory.json
```

✅ REVIEW SUMMARY shows items reused from memory
✅ Your blank is still pending, and is the only decision left (or close to it)
✅ Ends VERIFIED

---

## Done when

- [ ] Step 4 accepted the review from the attachment alone, wrote coherent memory and built the handoff
- [ ] Step 6 reused confirmed items and kept the blank pending

Then send me the handoff file and we start generation.
