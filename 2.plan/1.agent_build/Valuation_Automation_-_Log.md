# XPV Valuation Automation — Log

*Living file, started October 16, 2026.*

**How to use it:**

- This file holds everything that changes week to week: questions, decisions and run results.
- Add new rows at the bottom of each table, and never delete a row.
- When a question is answered, fill in the answer and the date, and set its status.
- When an answer changes a rule, add a decision row and update the System Spec.

---

## Legend

| Term | Meaning |
|---|---|
| Q-number | Question ID |
| D-number | Decision ID |
| Status | Open (not yet asked) · Asked · Answered · Closed (answered and acted on) |
| Run type | Answer-key test · Backtest (past quarter, compared with the analyst's workbook) · Live |
| Core | Core answers right, out of 10 |
| Wrong through | Wrong numbers let through without a person seeing them (target 0) |
| Pass / Analyst / Stopped | Count of items in each result |
| Cells match | Mechanical cells matching the analyst's workbook / total |
| Minutes | Analyst minutes on the run |

---

## Questions

| ID | Question | For | Why it matters | Status | Answer | Date |
|---|---|---|---|---|---|---|
| Q-01 | Time each step of Q3 as you do it this week | AJ, Jerome | Completes the time baseline | Open | | |
| Q-02 | Confirm the Quarterly Process Flow: missing steps, wrong order, missing times | Jerome | Baseline; the steps the build recreates | Open | | |
| Q-03 | How long does refreshing comparable multiples from PitchBook take per company per quarter? | Jerome | Baseline; Phase B | Open | | |
| Q-04 | How often does the comparable set itself change: about how many companies a year? | Jerome | Phase B | Open | | |
| Q-05 | When there is an acquisition, how is the pro-forma financials sheet built, where do the acquired business's numbers come from, and how long does it take? | Jerome | Acquisition handling; re-learn one sheet | Open | | |
| Q-06 | How often does the ownership table change (people joining or leaving)? More than once a year per company? | Jerome | Standard question 6 | Open | | |
| Q-07 | Is the multiple chosen before or after the new quarter's numbers are in? Is that why OceanSight's fund workbook multiple is typed in and differs from the valuation workbook? | Jerome, AJ | When questions are asked; Q-09 | Open | | |
| Q-08 | When setting up a new company's workbook, what is always the same and what is always different? Should the Opus and OceanSight structure be the standard template? | Jerome | Phase A | Open | | |
| Q-09 | OceanSight: why does the fund workbook use a different multiple from the valuation workbook? Which value went to investors? | AJ | Which file wins; undocumented change | Open | | |
| Q-10 | Opus: why did the Q1 earnings change in the Q2 workbook? Are past quarters routinely updated when companies revise their numbers? | AJ | Past-period refresh rule | Open | | |
| Q-11 | Are changes from the approval meeting always made in both the valuation workbook and the fund workbook? | AJ | Which file wins | Open | | |
| Q-12 | In what format do PitchBook numbers come out (export or copy), and who has access? | Jerome | Phase B | Open | | |
| Q-13 | Are the investor fund workbooks the same as the fund valuation workbook in each package, or built from it? | AJ | Phase C | Open | | |
| Q-14 | Do the frozen answer-key workbooks use the new adjustments template? | Aria | Regression tests still valid | Open | | |
| Q-15 | Can each company have an "approved" folder in SharePoint, and where should company memory files live? Who can edit them? | Jim | Inputs; memory storage | Open | | |
| Q-16 | Which two Fund III companies join Opus and OceanSight, and which one has a different structure? | AJ | Third company; backtest | Open | | |
| Q-17 | Who confirms the answer keys, and when? | AJ | Answer keys | Open | | |
| Q-18 | Who owns the system after December 18, and who runs Q4 in January? | Dave | Handover | Open | | |
| Q-19 | Do the 3 companies revalued twice a year join for Q4, or stay manual for now? | Dave, AJ | Q4 scope | Open | | |
| Q-20 | When are Q3 valuations due? | AJ | Timeline | Closed | About one week from Oct 16; Q3 becomes the backtest | Oct 16 |
| Q-21 | Is the approval cycle (~2.5 h) per company or per quarter? | AJ | Baseline | Answered | Assumed per company; confirm with Q-01 | Oct 16 |

---

## Decisions

| ID | Decision | By | Date |
|---|---|---|---|
| D-01 | Agent Builder MVP retired; the build continues from the Copilot Studio foundation | Aria | Oct 16 |
| D-02 | Reviewer agent removed from the main flow; kept on the shelf | Aria | Oct 15 |
| D-03 | Every approval is made by a person. The system never approves | Aria | Oct 16 |
| D-04 | The release stage is chosen by the analyst at the start of every run; a company's first run is track changes | Aria | Oct 16 |
| D-05 | The multiple is always confirmed, at every stage | Aria | Oct 16 |
| D-06 | Company memory: entries only added; the latest confirmed entry wins; proposed entries never make an item pass | Aria | Oct 16 |
| D-07 | Opus and OceanSight (Fund III) are the baseline companies; the adjustments sheet is now a template | Aria | Oct 16 |
| D-08 | Q3 is done by hand and used as the backtest; Q4 (January) is the first live quarter | Aria | Oct 16 |
| D-09 | After December 18: Phase A onboarding a new company, Phase B comparables (PitchBook), Phase C change summary to investor update | Aria | Oct 16 |
| D-10 | Sean's review time is not needed for the baseline | Aria | Oct 16 |
| D-11 | Three working files only: Studio Build Plan, System Spec, Log. Scope, MVP Build Plan and Project Summary are archived; the Process Flow is a one-off for Jerome | Aria | Oct 16 |
| D-12 | Project docs are kept in Markdown | Aria | Oct 16 |

---

## Runs

Record only sanitized results (statuses and counts). Never edit past rows.

| Date | Company | Quarter | Run type | Agent version | Stage | Core | Wrong through | Pass / Analyst / Stopped | Cells match | Minutes | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Before Oct 15 | Company 1 | — | Answer-key test | Agent Builder (retired) | — | 3/10 | — | 0 / all / — | — | — | Everything sent to review |
| Before Oct 15 | Company 1 | — | Answer-key test | Studio baseline | — | 10/10 | 0 | — | — | — | |
| Before Oct 15 | Company 2 | — | Answer-key test | Agent Builder (retired) | — | 3/9 | — | 0 / all / — | — | — | Everything sent to review |
| Oct 15 | Company 2 | — | Answer-key test | Studio baseline | — | 10/10 | 0 | — | — | — | 7 of 8 anchors exact (period proven by values, not headers); 12 diagnostic items ungraded |
