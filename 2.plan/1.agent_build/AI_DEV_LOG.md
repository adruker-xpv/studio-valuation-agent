# XPV Valuation Automation - AI Development Log

Purpose: a lightweight evidence log of material AI successes, AI failures, checking-code/guardrail successes, and UX/schema failures during development. Keep the existing project changelog for version/build changes; use this log for observed behaviour in real or test runs.

## Logging rule
Record an event only when it teaches us something about reliability, generalisation, analyst effort, or safety. Keep each entry short and use the same fields:
- **Situation** - what the system was trying to do.
- **Method** - AI / deterministic check / human review involved.
- **Outcome** - what actually happened.
- **Detected by** - answer key, checking code, review reader, analyst, regression test, etc.
- **Significance / impact** - why it matters; classify as Good AI, Bad AI, Good guardrail, or UX/schema issue. Record `wrong let through` where known.

## Events

### 2026-10-26 - Review reader blocks invalid onboarding decisions
- **Situation:** OceanSight onboarding review contained five entries that could not be safely applied: two prose corrections where a cell/value was required, plus three `Approve` decisions with no suggested answer to approve.
- **Method:** AI-led onboarding/review flow followed by deterministic review-workbook validation before writing decisions or company memory.
- **Outcome:** The reader refused the review. No review decisions or approved changes were written and company memory remained unchanged.
- **Detected by:** Review reader / schema validation.
- **Significance / impact:** **Good guardrail / good system behaviour; UX/schema issue exposed.** Ambiguous human inputs were stopped before becoming authoritative memory. `wrong let through: 0` for this event. Follow-up: make allowed answer types clearer so prose rules are not entered into cell/value-only fields.

### Before 2026-10-15 - Retired Agent Builder showed low core-answer accuracy
- **Situation:** Early answer-key tests on the two baseline companies.
- **Method:** Agent Builder extraction graded against hidden answer keys.
- **Outcome:** Company 1 scored 3/10 core answers and Company 2 scored 3/9; everything was sent to review.
- **Detected by:** Answer-key test bench.
- **Significance / impact:** **Bad AI / useful development evidence.** The approach was not reliably extracting the core valuation facts and was subsequently retired. No `wrong let through` figure was recorded because everything went to review.

### Before/On 2026-10-15 - Studio baseline reaches core-answer target
- **Situation:** Same baseline-company answer-key testing after moving to the Studio foundation.
- **Method:** Studio extractor graded against the frozen answer keys.
- **Outcome:** Both baseline companies scored 10/10 core answers; recorded wrong let through was 0. For Company 2, 7/8 anchors were exact; the 12-month period was supported by values rather than the expected header evidence, and 12 diagnostic items were not yet gradable.
- **Detected by:** Answer-key test bench and anchor grading.
- **Significance / impact:** **Good AI with a diagnostic gap.** Core valuation interpretation improved materially while exposing the need for fairer period-evidence and diagnostic grading rather than hiding the residual evidence issue.

### Test2 / pre-13.0 - Correct reading but run fails to persist
- **Situation:** Five real workbooks were processed in Test2.
- **Method:** AI-led extractor using the pre-13.0 workbook reader/run architecture.
- **Outcome:** The reading was reported as correct, but the extractor timed out before saving anything.
- **Detected by:** Test2 run outcome / missing persisted output.
- **Significance / impact:** **AI interpretation success, engineering failure.** This separated reading quality from run reliability and directly motivated the bounded reader and checkpointed/resumable 13.0 architecture.
