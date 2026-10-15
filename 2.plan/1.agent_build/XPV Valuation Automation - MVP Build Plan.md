# XPV Valuation Automation — MVP Build Plan

*Draft, October 14, 2026. Goes with "XPV Valuation Automation - Scope.md".*

---

## 0. Legend

| Term | Meaning |
|---|---|
| MVP | Minimum viable product: the smallest build that proves the idea end to end |
| Practice company | The real company with two quarters of data on file, used for the first roll-forward |
| Quarter 1 / Quarter 2 | Its earlier and later quarter |
| Reading AI / second reading AI / test bench | The three existing Copilot Studio agents (valuation-extractor, valuation-reviewer, valuation-test-bench) |
| Decision list | Only the items an analyst must actually decide |
| Decision sheet | The Excel file where the analyst records decisions |
| Company map | A JSON file built by a program from the decision sheet. The system's memory for that company |
| Analyst inputs | Numbers set by judgment each quarter (for example the multiple) |
| PASS / TO A PERSON / STOPPED | Sorting result for each item (see the scope document) |
| Wrong let through | A wrong number that passes unseen. Target: 0 |

---

## 1. What the MVP proves

**One company, two quarters, end to end:** learn the company on quarter 1, have the analyst approve it once, then roll forward to quarter 2 with familiar items passing automatically and the new workbook typed by programs. The result is compared with the analyst's own quarter 2 workbook.

That comparison is the truth check, so no answer key is needed for this test.

**The question it answers:** does one analyst approval make the next quarter quicker, with nothing wrong let through?

## 2. What we reuse (no rebuild)

| Existing piece | Used for |
|---|---|
| Reading AI, all seven stages | Learning the company (quarter 1) |
| Second reading AI | Blind challenge on quarter 1 only |
| Evidence checker (verify.py) and comparison (reconcile.py) | Evidence checks; the starting point for the decision list |
| Review sheet (onboarding_review.xlsx) | Starting point for the decision sheet |
| Test bench | Repeat tests; answer-key scoring where a key exists |
| Office Script write_approved_values.ts | Types only approved numbers; refuses wrong labels and formula cells; all or nothing |
| Office Script check_outputs.ts | Checks the typed workbook against last quarter |
| Gold Test Kit | Measuring tool only. The quick one-workbook reader (Gold Producer) is retired |

## 3. What we build (six pieces)

| # | Piece | What it does | Type |
|---|---|---|---|
| M1 | Decision list | Sorts reading-AI and second-AI findings by whether they matter and whether they need a decision; merges duplicates ("one underlying judgment = one decision"); shows only material decisions; keeps the rest in the audit detail | Program |
| M2 | Decision sheet | One Excel row per decision and per core item: approve / correct (with the right cell) / exclude / unresolved, plus a section for analyst inputs. Approver name and date at the top | Excel template |
| M3 | Company-map writer | Turns the decision sheet plus the frozen reading into a draft company map (JSON). For each item: meaning, source role, period rule, units, carried or refreshed, analyst input or not, evidence from the approved quarter. Stays a draft until the approver fields are filled. Refuses answer-key files | Program |
| M4 | Quarter mode | A new "ROLL-FORWARD" pass for the reading AI: reads the new package with the company map; a program compares each item and sorts it into PASS / TO A PERSON / STOPPED. Analyst inputs are always requested unless entered | Agent instructions + program |
| M5 | Workbook build | Copies last quarter's workbook, types PASS items and approved analyst inputs with the existing Office Script, recalculates, runs check_outputs, stamps the verdict in the file name | Existing scripts + Power Automate |
| M6 | Distant date headers | Lets evidence name the value range and its header range together, so the checker can confirm all 12 months even when headers are far away. Seen in both reading AIs, so it meets the two-company rule | Program fix |

**Order of work:** M6 and M1 → M2 and M3 → M4 → M5.

**Who does what:** Claude writes the programs, templates and invented test files. Aria uploads them to Copilot Studio, runs them, and brings back sanitized results only.

## 4. Tests

### Test A — invented two-quarter package (before touching real data)

| Case | Expected |
|---|---|
| Unchanged item, same cell | PASS |
| Unchanged item, moved cell | PASS |
| Changed label, source or calculation | TO A PERSON |
| New item, never approved | TO A PERSON |
| Analyst input changed and not entered | TO A PERSON |
| Stale period, wrong source, broken sum, mismatched units | STOPPED |
| Answer-key file passed to the map writer | Refused |

### Test B — practice company, real data

1. Quarter 1: run the reading AI and second reading AI; produce the decision list.
2. The analyst fills in the decision sheet. **Time it.**
3. The map writer creates the company map; the analyst signs it.
4. Quarter 2: quarter mode run. **The analyst's actual quarter 2 multiple and other judgment inputs are entered as analyst inputs**, so the generated workbook isn't marked wrong for decisions it couldn't know.
5. Programs type the workbook.
6. Compare with the analyst's real quarter 2 workbook, cell by cell, for mechanical numbers. Score analyst inputs separately.

**Record:** the four outcomes (right and passed · rightly sent to a person · needlessly sent to a person · wrong let through), share passed, analyst minutes at approval and in quarter 2, mechanical cells matching, STOPPED reasons.

**Also run once:** quarter 2 *without* the analyst's inputs entered. Every judgment-driven item should go TO A PERSON, none should pass.

## 5. Done when

- Test A gives every expected result.
- Test B: wrong let through = 0; some items PASS in quarter 2; every mechanical number in the typed workbook matches the analyst's workbook, or is explained.
- The decision list for quarter 1 has a handful of decisions, not dozens.
- The approval and quarter 2 runs are timed.

## 6. Not in the MVP

- LP report and quarter-over-quarter change summary (scope extensions; next after the MVP)
- Redesigning the second reading AI beyond the decision list (it runs on onboarding only for now)
- Finishing matching details for the answer key's 9 unscored checks (Nov 2–13, by the analyst, to avoid a circular test)
- Wrappers for saving and uploading files, and retry efficiency (before handover)
- Moving Python checks into Office Scripts

## 7. Open questions

1. What is the practice company's package for each quarter: the same five kinds of workbook as OceanSight?
2. Besides the multiple, which numbers did the analyst change by judgment between quarter 1 and quarter 2?
3. Which analyst fills in the decision sheet for the practice company, and can we time it this month?
