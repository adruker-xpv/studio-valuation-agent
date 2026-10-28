# XPV Valuation Automation — Log

_Living file, started October 16, 2026. Last updated October 28, 2026._

**How to use it:** add new rows at the bottom of each table and never delete a row. When a question is answered, fill in the answer, date and status. When an answer changes a rule, add a decision row and update the System Spec. AI behaviour events go in the AI Development Log.

## Legend

| Term | Meaning |
|---|---|
| Q-number / D-number | Question ID / Decision ID |
| Status | Open (not yet asked) · Asked · Answered · Closed (answered and acted on) |
| Run type | Answer-key test · Onboarding · Memory reuse · Backtest · Live |
| Core | Core answers right, out of 10 |
| Wrong through | Wrong numbers let through without a person seeing them (target 0) |
| A / C / R / U | Review decisions: approved / corrected / rejected / undecided |
| Mem | Memory entries added or reused |

## Questions

| ID | Question | For | Why it matters | Status | Answer | Date |
|---|---|---|---|---|---|---|
| Q-01 | Time each step of Q3 as you do it this week | AJ, Jerome | Completes the time baseline | Open | | |
| Q-02 | Confirm the Quarterly Process Flow: missing steps, wrong order, missing times | Jerome | Baseline | Open | | |
| Q-03 | How long does refreshing comparable multiples from PitchBook take per company per quarter? | Jerome | Baseline; Phase B | Open | | |
| Q-04 | How often does the comparable set itself change? | Jerome | Phase B | Open | | |
| Q-05 | When there is an acquisition, how is the pro-forma sheet built and how long does it take? | Jerome | Re-learn one sheet | Open | | |
| Q-06 | How often does the ownership table change? | Jerome | Standard question 6 | Open | | |
| Q-07 | Is the multiple chosen before or after the new quarter's numbers are in? | Jerome, AJ | Q-09 | Open | | |
| Q-08 | What is always the same and always different when setting up a new company's workbook? | Jerome | Phase A | Open | | |
| Q-09 | OceanSight: why does the fund workbook use a different multiple from the valuation workbook? | AJ | Which file wins | Open | | |
| Q-10 | Opus: why did the Q1 earnings change in the Q2 workbook? Are past quarters routinely updated? | AJ | Past-period refresh rule | Open | | |
| Q-11 | Are approval-meeting changes always made in both the valuation and fund workbooks? | AJ | Which file wins | Open | | |
| Q-12 | In what format do PitchBook numbers come out, and who has access? | Jerome | Phase B | Open | | |
| Q-13 | Are the investor fund workbooks the same as the fund valuation workbook, or built from it? | AJ | Phase C | Open | | |
| Q-14 | Do the frozen answer-key workbooks use the new adjustments template? | Aria | Regression tests valid | Open | | |
| Q-15 | Can each company have an "approved" folder, and who can edit memory files? | Jim | Inputs; memory storage | Open | | |
| Q-16 | Which two Fund III companies join Opus and OceanSight, and which has a different structure? | AJ | Phase 3; backtest | Open | | |
| Q-17 | Who confirms the answer keys, and when? | AJ | Answer keys | Open | | |
| Q-18 | Who owns the system after December 18, and who runs Q4 in January? | Dave | Handover | Open | | |
| Q-19 | Do the 3 twice-a-year companies join for Q4, or stay manual? | Dave, AJ | Q4 scope | Open | | |
| Q-20 | When are Q3 valuations due? | AJ | Timeline | Closed | About one week from Oct 16; Q3 becomes the backtest | Oct 16 |
| Q-21 | Is the approval cycle (~2.5 h) per company or per quarter? | AJ | Baseline | Answered | Assumed per company; confirm with Q-01 | Oct 16 |
| Q-22 | Opus Q1 2026: are the $2,875,964 TTM add-backs (incl. excess temporary labour $890,525 and consulting $746,591) approved as non-recurring? Who signs off add-backs in general? | AJ / investment team | Pending in memory; blocks one memory rule | Open | | |
| Q-23 | Opus: should 'LP Report'!I9 (fully diluted ownership) be relinked from the Dec 2025 cap table to the current one each quarter? | AJ | r7 review decision | Open | | |
| Q-24 | Can the agent upload by staged file path in production (no base64, no retyping)? | Aria / Jim | Upload integrity (Spec §10) | Open | | |

## Decisions

| ID | Decision | By | Date |
|---|---|---|---|
| D-01 | Agent Builder MVP retired; build continues from the Copilot Studio foundation | Aria | Oct 16 |
| D-02 | Reviewer agent removed from the main flow; kept on the shelf | Aria | Oct 15 |
| D-03 | Every approval is made by a person. The system never approves | Aria | Oct 16 |
| D-04 | Release stage chosen by the analyst at the start of every run; first run is track changes | Aria | Oct 16 |
| D-05 | The multiple is always confirmed, at every stage | Aria | Oct 16 |
| D-06 | Company memory: entries only added; latest confirmed wins; proposed never makes an item pass | Aria | Oct 16 |
| D-07 | Opus and OceanSight (Fund III) are the baseline companies; adjustments sheet is a template | Aria | Oct 16 |
| D-08 | Q3 done by hand and used as the backtest; Q4 (January) is the first live quarter | Aria | Oct 16 |
| D-09 | After December 18: Phase A onboarding, Phase B comparables, Phase C change summary | Aria | Oct 16 |
| D-10 | Sean's review time is not needed for the baseline | Aria | Oct 16 |
| D-11 | Three working files only: Studio Build Plan, System Spec, Log (superseded by D-14) | Aria | Oct 16 |
| D-12 | Project docs are kept in Markdown | Aria | Oct 16 |
| D-13 | Onboarding polish phase closed. Onboarding frozen except for defects. Open items (memory first, no silent drops, upload method, clean responses) become Phase 6 entry items | Aria | Oct 28 |
| D-14 | Five working files: Build Plan, System Spec, Log, AI Development Log, Run Guide. Polish doc and OceanSight E2E Test archived | Aria | Oct 28 |
| D-15 | Unresolved decisions accept Correct or Reject only; Approve is invalid where there is no suggested answer | Review reader (rule recorded) | Oct 28 |
| D-16 | First generation target is Opus Q1 → Q2 2026, starting from the Q1 r6 hand-off | Aria | Oct 28 |

## Runs

Record only sanitized results. Never edit past rows.

| Date | Company | Quarter | Run | Run type | Build | Core | Wrong through | Result | A / C / R / U | Mem | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Before Oct 15 | Company 1 | — | — | Answer-key test | Agent Builder (retired) | 3/10 | — | Everything to review | — | — | |
| Before Oct 15 | Company 1 | — | — | Answer-key test | Studio baseline | 10/10 | 0 | — | — | — | |
| Before Oct 15 | Company 2 | — | — | Answer-key test | Agent Builder (retired) | 3/9 | — | Everything to review | — | — | |
| Oct 15 | Company 2 | — | — | Answer-key test | Studio baseline | 10/10 | 0 | — | — | — | 7 of 8 anchors exact; 12 diagnostic items ungraded |
| Oct 28 | Opus | 2026 Q1 | r6 | Onboarding review (1st) | 13.2.6 | — | 0 | Refused | — | 0 | 3 unresolved decisions marked Approve |
| Oct 28 | Opus | 2026 Q1 | r6 | Onboarding review (2nd) | 13.2.6 | — | 0 | Refused | — | 0 | Same 3 rows; wrong file version submitted |
| Oct 28 | Opus | 2026 Q1 | r6 | Onboarding review (3rd) | 13.2.6 | — | 0 | Accepted | 23 / 4 / 0 / 2 | 15 added | Memory created, coherence OK; hand-off ready_with_unresolved; 1 pending (add-backs) |
| Oct 28 | Opus | 2026 Q1 | r7 | Memory reuse (extraction A+B) | 13.2.6 | — | 0 | VERIFIED, 0 contradicted | — | 14 reused | 1 pending carried, 0 reopened, 1 new decision, 3 new candidates; 12 proposals; 1 immaterial $0.10 difference |
