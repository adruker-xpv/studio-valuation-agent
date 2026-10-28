## XPV Valuation Automation - AI Development Log

_Last updated October 28, 2026._

Purpose: a lightweight evidence log of material AI successes, AI failures, checking-code/guardrail successes, and UX/schema failures during development. Use the Log for version/run results; use this log for observed behaviour in real or test runs.

### Logging rule

Record an event only when it teaches us something about reliability, generalisation, analyst effort, or safety. Use the same fields:

- **Situation** - what the system was trying to do.
- **Method** - AI / deterministic check / human review involved.
- **Outcome** - what actually happened.
- **Detected by** - answer key, checking code, review reader, analyst, regression test, etc.
- **Significance / impact** - Good AI, Bad AI, Good guardrail, or UX/schema issue. Record wrong let through where known.

### Strengths and weaknesses so far

| | Evidence |
|---|---|
| **AI strength: reading valuation chains** | 10/10 core answers on both baseline companies; Opus Q1 chain traced from monthly figures to the fund value with 0 contradicted |
| **AI strength: tracing sources** | Matched every monthly EBITDA and add-back row to its source; found a $0.10 rounding difference and a stale cap-table link without being asked |
| **AI strength: accepting correction** | Changed its own "value to XPV" mapping when memory showed the source cell |
| **AI weakness: workflow discipline** | Loaded memory late; skipped a proposal silently; deferred checkpoint uploads to save tokens |
| **AI weakness: improvising mechanics** | Moved files by printing base64 and retyping memory from context, outside any approved method |
| **Guardrail strength** | Review reader refused invalid human input 3 times and a mismatched snapshot once; nothing bad reached memory; wrong let through 0 throughout |
| **UX weakness** | Allowed answer types on the review workbook are easy to get wrong (Approve with no suggestion; prose in cell fields) |

### Events

#### 2026-10-28 - Memory reuse works on a fresh run
- **Situation:** Opus Q1 2026 r7, a fresh extraction run with company memory supplied after the r6 review.
- **Method:** AI extraction (stages 1–8) reconciled against confirmed memory by concept; deterministic verify.
- **Outcome:** 14 memory items reused, 1 pending decision carried forward, 0 reopened, 1 new decision (LP report ownership link), 3 new memory candidates. VERIFIED, 0 contradicted. The three r6 answers were not asked again.
- **Detected by:** Run summary and verify.
- **Significance / impact:** **Good AI + good system behaviour.** First evidence that memory reduces repeat analyst review. Wrong let through: 0.

#### 2026-10-28 - Memory corrects an AI mapping
- **Situation:** In r7 the extractor mapped "value to XPV" to the valuation summary cell, which only copies the cap-table result.
- **Method:** Memory reconciliation raised a contradiction; AI re-examined the formula path.
- **Outcome:** The AI moved the mapping to the cap-table source cell, reopened stage 3, re-saved and re-verified. Contradiction closed.
- **Detected by:** Company memory reconciliation.
- **Significance / impact:** **Good guardrail; Bad AI (minor).** Memory caught a copy-vs-source error. Cost: a stage 3 revision after stage 8, because memory was loaded at stage 6. Fix: load memory before stage 1.

#### 2026-10-28 - AI skips a proposal without flagging it
- **Situation:** r7 stage 7, building proposals for next quarter.
- **Method:** AI proposal generation.
- **Outcome:** The monthly rows proposal was skipped as "unclear" and not raised as a question. Proposals fell from 13 (r6) to 12.
- **Detected by:** Human reading of the trace.
- **Significance / impact:** **Bad AI.** A silent drop, against the no-silent-failure rule. No wrong value resulted. Fix: every candidate becomes a proposal or an open question.

#### 2026-10-28 - AI improvises file transfer
- **Situation:** r7 needed checkpoints, extraction files and memory uploaded to SharePoint.
- **Method:** AI agent choosing its own upload approach in the sandbox.
- **Outcome:** Files were printed as base64 text, memory was retyped from context, staging folders were tested by trial, and checkpoint uploads were deferred to save tokens. Final sizes matched.
- **Detected by:** Human reading of the trace.
- **Significance / impact:** **Bad AI / UX-schema issue; highest operational risk.** Retyping could corrupt a file; the memory hash chain would likely catch a bad copy, but other files have no such check. Fix: one approved upload method with size and hash checks.

#### 2026-10-28 - Review reader refuses Approve with no suggested answer (Opus)
- **Situation:** Opus Q1 r6 completed review marked three unresolved decisions (multiple, debt, approved value) as Approve.
- **Method:** Human review (AI-assisted fill) followed by deterministic review validation.
- **Outcome:** Refused twice; nothing written. Second refusal was caused by submitting an older file version. Third submission (Correct + written answers) accepted: 23 approved, 4 corrected, 0 rejected, 2 undecided; memory created with 15 entries, coherence OK; hand-off `ready_with_unresolved`.
- **Detected by:** Review reader.
- **Significance / impact:** **Good guardrail; UX/schema issue repeated.** Same failure as OceanSight on Oct 26, so the allowed answers need to be clearer in the workbook and Run Guide. Also: AI-assisted filling did not check the sheet's allowed values first. Wrong let through: 0.

#### 2026-10-28 - Deliberate blank kept as pending
- **Situation:** Add-backs approval left blank in the r6 review because the evidence could not show they were non-recurring.
- **Method:** Human review; memory writer.
- **Outcome:** Saved as pending, carried into the hand-off as unresolved, and surfaced again in r7.
- **Detected by:** Run summaries (r6, r7).
- **Significance / impact:** **Good system behaviour.** An unknown was not turned into a fact.

#### 2026-10-26 - Review reader blocks invalid onboarding decisions
- **Situation:** OceanSight onboarding review contained five entries that could not be safely applied: two prose corrections where a cell/value was required, plus three Approve decisions with no suggested answer.
- **Method:** AI-led onboarding/review flow followed by deterministic review-workbook validation.
- **Outcome:** The reader refused the review. Company memory remained unchanged.
- **Detected by:** Review reader / schema validation.
- **Significance / impact:** **Good guardrail; UX/schema issue exposed.** Wrong let through: 0.

#### 2026-10-26 - Review reader blocks mismatched proposal snapshot
- **Situation:** A completed review was read back against a proposal snapshot that did not match the one it was built from.
- **Method:** Deterministic proposal-identity validation.
- **Outcome:** Rejected; memory unchanged.
- **Detected by:** Review reader / proposal identity check.
- **Significance / impact:** **Good guardrail; persistence defect exposed.** Wrong let through: 0.

#### Before 2026-10-15 - Retired Agent Builder showed low core-answer accuracy
- **Outcome:** Company 1 3/10, Company 2 3/9; everything sent to review. Approach retired.
- **Significance / impact:** **Bad AI / useful development evidence.**

#### Before/On 2026-10-15 - Studio baseline reaches core-answer target
- **Outcome:** Both baseline companies 10/10 core answers; wrong let through 0. Company 2: 7/8 anchors exact; 12 diagnostic items not yet gradable.
- **Significance / impact:** **Good AI with a diagnostic gap.**

#### Test2 / pre-13.0 - Correct reading but run fails to persist
- **Outcome:** Reading correct, but the extractor timed out before saving anything.
- **Significance / impact:** **AI interpretation success, engineering failure.** Motivated the checkpointed, resumable 13.0 architecture.
