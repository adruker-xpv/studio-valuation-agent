# XPV Valuation Automation — Studio Build Plan

*Draft 3, October 16, 2026. Owner until December 18, 2026: Aria (AI Intern).*

This is one of three working files:

- **Studio Build Plan** (this file): why we're building it, what we build and when.
- **System Spec:** how the system must behave.
- **Log:** questions, decisions and run results.

---

## North star

**Every quarter, the analyst gets a new valuation workbook in which every mechanical number is exactly right and shows where it came from. The analyst only decides what is new, unclear or a judgment call. Every approval is made by a person.**

**Why it matters, in order:**

1. **Exactness:** the figures go to investors.
2. **Clear inputs:** the analyst trusts a workbook when its inputs are easy to check.
3. **Time:** less mechanical work, and the process scales as the portfolio grows.
4. **Continuity:** it runs from a guide, not one person's memory.

**Goal by December 18:**

- Four Fund III companies have Q3 rebuilt by the system as a backtest, at track changes stage, with 0 wrong let through and every mechanical number matching the analyst's real Q3 workbook.
- The system is ready for Q4 in January, the first live quarter, run by the new owner.
- Q3 is done by hand because it's due about a week from October 16.

**Today's baseline** (being confirmed by Jerome):

| | Time |
|---|---|
| Known time per company-quarter | About 4 hours |
| Known time per year (about 22 company-quarters) | About 85–90 hours |
| Still pending | Comparables, judgment and checking times |
| Core build target | Removes about 1 hour per company-quarter |
| With Phase C | Removes up to about 2 hours per company-quarter |

**Who does what:**

| Who | Does | Never does |
|---|---|---|
| AI (extractor) | Reads files, proposes what each number means and what changed, explains differences | Approves, types into workbooks, makes judgment calls |
| Checking code | Confirms every AI claim, sorts items, types confirmed numbers, checks the finished workbook | Decides what a number means |
| Analyst | Chooses the release stage, answers the standard questions, approves items, signs off every workbook | Re-checks passed items (spot checks only) |
| Future interns | Start runs, supply files | Change agents or code without running the tests |

**In and out of scope:**

- **In:** Microsoft 365 only (Copilot Studio, Power Automate, Office Scripts, SharePoint).
- **Out, for now:**
  - Judgment calls (multiples, comparables, new adjustments, ownership treatment)
  - AI typing into workbooks
  - Azure
  - Workbook redesigns
  - Companies with no workbook yet

**After December 18:**

| Phase | Adds |
|---|---|
| A. Onboarding a new company | Start from the Opus and OceanSight template. The extractor proposes the mapping and the analyst confirms it |
| B. Comparables | Refreshed multiples from PitchBook, out-of-date comparables flagged, replacements suggested. The analyst decides |
| C. Change summary to investor update | What changed and why. A few questions for the analyst. A drafted investor update and filled investor fund workbooks (fund overview plus company breakdowns) |

**Success measures:**

| Measure | Target |
|---|---|
| Wrong let through | 0 |
| Mechanical numbers matching the analyst's workbook | All, exactly |
| Analyst questions at onboarding | A handful, not dozens |
| Items passed automatically | Above 0 from the second quarter, and rising |
| Analyst time | Below today's |
| Runs without Aria | An intern can run a quarter from the Run Guide |

---

## Legend

| Term | Meaning |
|---|---|
| Roll-forward | Updating last quarter's approved valuation workbook with the new quarter's numbers |
| Extractor | The AI agent that reads a company's files and traces how its value is built |
| Reviewer | A second AI agent that checks the extractor independently. Removed from the main flow; kept on the shelf |
| Test bench | The agent that grades runs against hidden answer keys. Development only |
| Checking code | Tested programs (verify.py, reconcile.py and others) that re-open the files and confirm every AI claim |
| Office Scripts | write_approved_values.ts types only confirmed numbers, refusing wrong labels and formula cells, all or nothing. check_outputs.ts checks the typed workbook against last quarter |
| Answer key (Gold key) | Correct answers written by a person before any run and hidden from the AI. Used only to grade |
| Core answers | The 10 main facts of a valuation, from the method to the value the fund reports |
| Anchor | The cell or cells that prove an answer |
| Fingerprint | A digital code for a file; any change to the file changes it |
| Company memory | Confirmed decisions per company (format in the System Spec, section 7) |
| Decision sheet | The Excel sheet where the analyst chooses the release stage, answers the standard questions and approves items |
| Re-learn one sheet | Learning a single new or restructured sheet without redoing the whole company |
| Backtest | A test on a past quarter where the analyst's real workbook shows the right answer |
| Regression check | Re-running every frozen test after a change, to prove nothing that worked before broke |
| Release stage | Track changes, approve new or unsure, or auto. The analyst chooses one at the start of every run |
| Adjusted earnings (Adjusted EBITDA) | Earnings after approved one-off adjustments; most companies are valued as a multiple of this |
| Comparables | Similar public companies, from PitchBook, that set the range for the multiple |
| Fund III | The fund whose companies are revalued every quarter. Other funds' companies are revalued in Q2 and Q4 only |
| Held at cost | A company kept at its purchase price and not revalued (currently 2) |
| Investors (LPs, limited partners) | The fund's investors. Each fund has an investor fund workbook |
| Wrong let through | A wrong number that reaches the workbook without a person seeing it. Target: 0 |

---

## To do (high level, in order)

| # | To do | When | Phase |
|---|---|---|---|
| 1 | Ask AJ and Jerome to time Q3 as they do it; send Jerome the Quarterly Process Flow (a one-off). Once he confirms it, update the baseline here and archive the flow | Oct 19–23 | Baseline |
| 2 | Raise the two discrepancies with AJ: OceanSight's multiple, and Opus's revised Q1 earnings (questions Q-09 to Q-11 in the Log) | Oct 19–30 | Baseline |
| 3 | Update the agents: lock the baseline, take the reviewer out, make the test bench fixes | Oct 19–30 | 0–2 |
| 4 | Test against the answer keys; first check whether the key workbooks use the new adjustments template | Oct 22–30 | 2 |
| 5 | Have the analyst confirm the answer keys (after Q3 is filed) | Oct 26–Nov 6 | 2 |
| 6 | Collect Q2 and Q3 2026 packages for Opus, OceanSight and two more Fund III companies | Oct 26–30 | 3 |
| 7 | Set up "approved" folders and the company memory location in SharePoint with Jim | Oct 26–30 | 5 |
| 8 | Finish the System Spec: onboarding questions, memory format, which file wins | Oct 26–Nov 6 | 4, 5 |
| 9 | Practice onboarding end to end on Opus, then OceanSight: upload, answer, produce the memory file | Nov 2–13 | 5 |
| 10 | Third company: write its answer key, then run it 3 times | Nov 2–13 | 3 |
| 11 | Test A: the invented two-quarter package | Nov 9–13 | 6 |
| 12 | Build quarterly mode and the workbook builder | Nov 9–27 | 6 |
| 13 | Test B: backtest Q2 to Q3, Opus first, then the other three | Nov 23–Dec 4 | 7 |
| 14 | Update Dave: Agent Builder retired, Q3 used as the backtest, Q4 is the first live quarter | Late Nov | — |
| 15 | Handover: Run Guide, tests, named owner, Q4 plan | Dec 7–18 | 8 |

**Who does what in the build:** Claude writes the programs, templates and invented test files. Aria uploads them to Copilot Studio, runs them, and brings back sanitized results only. Every run is recorded in the Log.

---

## 1. Where we are (October 15, 2026)

| Run | Company | Files | Core answers right | Wrong let through |
|---|---|---|---|---|
| Agent Builder (retired) | Company 1 | 5 | 3 of 10 | — (everything sent to review) |
| Studio baseline | Company 1 | 5 | 10 of 10 | 0 |
| Agent Builder (retired) | Company 2 | 6 | 3 of 9 | — (everything sent to review) |
| Studio baseline | Company 2 | 6 | 10 of 10 | 0 |

**Company 2 in detail:**

- 7 of 8 anchors were exact. The miss: the 12-month period was right, but it was proven with the 12 numbers rather than the 12 date headers.
- 12 diagnostic items couldn't be graded yet, because the answer key lacks matching details. This doesn't reduce the core score.

**Conclusion:** the extractor finds the valuation without the reviewer. The open question is whether it works on different companies, every time, with less analyst work.

---

## 2. What we reuse

| Existing piece | Used for |
|---|---|
| Extractor, all seven stages | Learning a company |
| verify.py, reconcile.py | Evidence checks; the starting point for the decision list |
| onboarding_review.xlsx | Starting point for the decision sheet |
| Test bench and Gold Test Kit | Grading against answer keys |
| write_approved_values.ts | All typing into workbooks |
| check_outputs.ts | Checking the typed workbook against last quarter |

---

## 3. Rules for every change

- **Universal agents.** No company names, cells or rules in agents, skills or instructions.
- **Answer keys only measure.**
- **AI proposes; code checks and types; a person approves.**
- **Confidence is decided by code, never by the AI.**
- **No fitting to one company.** If a change only helps one company, it doesn't go in.
- **Regression check after every change.** Nothing that scored right before may get worse.
- **Exact matching by default.** Rounding only where an answer key declares it.
- **Files are identified by fingerprint**, not by file name.

---

## 4. Phases

### Phase 0 — Lock the baseline (Oct 16–19)

- Save the current extractor, its skills and instructions as the baseline version.
- Freeze the two answer keys and their fingerprints as the regression set.
- **Done when:** both companies re-score 10 of 10 from the frozen files.

### Phase 1 — Remove the reviewer from the flow (Oct 19–21)

- Take the reviewer out of the run order. Don't change the extractor.
- **Done when:** 10 of 10 on both companies, with the same anchors.

### Phase 2 — Test bench 13.2: fairer, more complete grading (Oct 19–30)

All changes are additive, and old answer keys keep working.

1. **Period evidence.** Grade header evidence and value evidence separately. The checker accepts a value range together with its header range, even when the headers are far away.
2. **Matching details written automatically.** Every look-alike, difference and judgment call gets a stable ID and a verified cell, and the analyst approves them.
3. **Component evidence.** Cash and debt cells are marked as parts of a total, so they stop triggering "doesn't equal the total" warnings.
4. **Separate report sections:** core answers, anchors, look-alikes, differences, judgment calls kept open, file integrity, and the checking-code result.
- **Done when:** all 253 code tests plus the new ones pass, core results are unchanged, and the 12 diagnostic items can be graded.

### Phase 3 — Prove it generalizes (Oct 26–Nov 13)

- Add a third Fund III company with a different structure. Write and freeze its answer key before any run.
- Run each company 3 times.
- **Done when:** results are reported per company and per run, including the worst one.

### Phase 4 — Fewer, better questions (Oct 26–Nov 13)

- **Decision list:** sort findings by whether they matter and whether they need a decision. Merge duplicates (one underlying judgment = one decision). Show only real decisions; keep the rest in the audit detail.
- The AI lists every plausible candidate number with its source, and code rules out invalid ones.
- **Done when:** a handful of decisions per company, not dozens, with 0 wrong let through.

### Phase 5 — Company memory and onboarding (Oct 26–Nov 13)

- **Decision sheet:**
  - Release stage, the standard questions (System Spec, section 3) and one row per decision.
  - Each row is answered approve / correct (with the right cell) / exclude / unresolved.
  - Approver name and date at the top.
- **Memory writer:** code turns the decision sheet into memory entries, using the format and update rules in the System Spec (section 7). It refuses answer-key files.
- Save the approved workbook's fingerprint at sign-off.
- **Done when:** a second run on the same company uses memory and asks only about what changed. Time the analyst's onboarding approval.

### Phase 6 — Quarterly mode and workbook builder (Oct 26–Nov 27; hardest part)

**Start of run:**

- Release stage and standard questions.
- Workbook version check against the saved fingerprint.
- Past-period columns refreshed from the latest monthly files, with any revisions flagged.

**Order of work:**

1. The AI proposes each change.
2. Code checks it (System Spec, section 4).
3. Code sorts it (section 5).
4. Code applies items according to the stage (section 6), typing with write_approved_values.ts and adding a source note.
5. The workbook is recalculated, and check_outputs.ts runs, including the hidden-row and footnote checks.
6. Output: the new workbook, the change log, and a verdict in the file name.

**Re-learn one sheet:** for a new pro-forma sheet or a restructured ownership table, only that part stops and is re-learned. The rest of the run carries on.

**Test A — invented two-quarter package:**

| Case | Expected |
|---|---|
| Unchanged item, same cell or moved cell | Pass |
| Changed label, source or calculation | To the analyst |
| New item never approved | To the analyst |
| Multiple not confirmed | To the analyst |
| Out-of-date period, wrong source, broken total, mismatched units | Stopped |
| Files disagree with no rule in memory | Stopped |
| Past month revised | To the analyst |
| Last quarter's workbook changed since approval | Changes listed; to the analyst |
| Answer-key file passed to the memory writer | Refused |

**Fallback:** if the full build isn't ready, deliver checked numbers plus a list of changes for the analyst.

**Done when:** Test A gives every expected result.

### Phase 7 — Test B: Q3 backtest and Q4 readiness (Nov 23–Dec 4)

1. Onboard the company on Q2 and fill in the decision sheet (timed).
2. Run Q3 at track changes stage, with the analyst's real Q3 multiple and other judgment inputs entered.
3. Compare cell by cell with the analyst's real Q3 workbook. Score mechanical cells and judgment inputs separately.
4. Run once more without the judgment inputs entered. Every judgment-driven item must go to the analyst.
5. Record the four outcomes: right and passed; rightly sent to the analyst; needlessly sent to the analyst; wrong let through.
- Opus first, then OceanSight and the two other Fund III companies.
- **Done when:** 0 wrong let through, and every mechanical number matches or is explained.

### Phase 8 — Handover (Dec 7–18)

- Run Guide for non-technical owners and interns.
- Named owner; Q4 plan; go/no-go decision.

---

## 5. Scorecard (every company, every run — record in the Log)

| Measure | Target |
|---|---|
| Core answers right | 10 of 10 |
| Wrong let through | 0 |
| Anchors exact or approved equivalent | All |
| Judgment calls kept open, not guessed | All |
| Files proven identical (fingerprints) | All |
| Mechanical cells matching (backtests) | All |
| Analyst questions per company | Falling over time; only real decisions |
| Same result across 3 runs | Yes |

---

## 6. After December 18

Phases A, B and C are in the north star section.

**Saved for later:**

- Certified and development answer keys clearly labelled
- An optional "matters / doesn't matter" grade beside the current results
- Scoring XPV's share of value separately from company value
- Grading the whole chain from monthly numbers to fund value
- Wrappers for saving and uploading files
- Retry efficiency
- Moving Python checks into Office Scripts
