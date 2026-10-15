# XPV Valuation Automation — Scope

*Draft, October 14, 2026. Owner until December 18, 2026: Aria (AI Intern).*

---

## 0. Legend

| Term | Meaning |
|---|---|
| Roll-forward | Updating last quarter's approved valuation workbook with the new quarter's numbers |
| Package | The set of workbooks for one company and one quarter: company valuation, fund valuation, and upstream files (monthly financials, monthly summaries, trailing-twelve-month files) |
| Reading AI | The Copilot Studio agent that maps how a company's value is built across its package (named "valuation-extractor" in Studio) |
| Second reading AI | The separate Copilot Studio agent that reads the same package blind and challenges the first (named "valuation-reviewer" in Studio) |
| Test bench | The separate Copilot Studio agent that grades runs against answer keys (named "valuation-test-bench" in Studio). Never attached to the two reading AIs |
| Pre-written program | Fixed, tested code. AI can run it but can't change it |
| Answer key (Gold key) | A hidden list of correct answers written before any AI run. Used only to measure the system during development, never in real use |
| Decision list | The short list of items an analyst must actually decide; everything else stays in the audit detail |
| Company map | One file per company recording what the analyst approved: what each number means, where it comes from, which period rule applies. The system's memory |
| Analyst inputs | Numbers the analyst sets by judgment each quarter (for example the multiple). The system never predicts these |
| PASS / TO A PERSON / STOPPED | PASS = matches the approved company map and the evidence checks out · TO A PERSON = new, changed or unclear · STOPPED = contradicted, missing, stale, or wrong source |
| Wrong let through | A wrong number that passes without a person seeing it. Target: 0 |
| LP report | The investor report the workbooks feed |

---

## 1. Goal

**By December 18, 2026, at least four portfolio companies run their quarterly roll-forward through the system.** AI reads the new quarter, pre-written programs check it against what the analyst approved before and build the new workbook, and the analyst sees only what's new or changed.

**Stretch goal:** onboard a company new to the system, as long as it already has a valuation workbook.

## 2. Where this build sits

```
Too manual ───────────── Target ───────────── Too AI
Copilot Studio today      This build           Agent Builder build 13
reads correctly,          AI reads once,       AI in charge, wrote the
remembers nothing,        analyst approves     workbook, worked around
every question to a       once, programs pass  the checks, said "done"
person (34 questions)     what hasn't changed  when it wasn't
                          and do the typing
```

**Starting point:** the Copilot Studio agents (reading AI, second reading AI, test bench). On the real test company with its full five-workbook package, the reading AI got 10 of 10 core answers right on a blind answer key.

**What's missing between here and the target:** a short decision list, a company map that remembers decisions, a quarter mode that compares against the map, and program-only typing of the new workbook.

## 3. In scope

| Step | What it does | How often | Baseline or extension |
|---|---|---|---|
| 1. Learn the company | Reading AI maps the package; second reading AI challenges it blind; programs verify the evidence | Once per company, and again after a big structure change | Baseline |
| 2. Analyst decides | Analyst works through the short decision list and enters analyst inputs | Once per company, then only new or changed items | Baseline |
| 3. Remember | A pre-written program turns the analyst's decisions into the company map | After every approval | Baseline |
| 4. Read the new quarter | Reading AI reads the new package; programs compare each item with the company map and sort it into PASS, TO A PERSON or STOPPED | Every quarter | Baseline |
| 5. Build the workbook | Pre-written programs type only approved numbers into a copy of last quarter's workbook, recalculate, and stamp a verdict in the file name | Every quarter | **Baseline deliverable: the new quarter's valuation workbook** |
| 6. Quarter-over-quarter changes | Data-based summary of what changed since last quarter and why (earnings, multiple, debt, ownership), with amounts and flagged surprises, to inform the analyst's report | Every quarter | Extension |
| 7. LP report | Carry approved values into the LP report | Every quarter | Extension |

## 4. Out of scope (for now)

- Brand-new companies with no valuation workbook yet. The analyst builds the first workbook as today, and the system takes over from the following quarter.
- Anything needing Azure. Microsoft 365 only: Copilot Studio, Agent Builder, Power Automate, Office Scripts, SharePoint.
- Major redesigns of the workbooks themselves.
- AI typing into any delivered workbook.
- Judgment calls: multiples, new adjustments, ownership treatment, choosing between company and fund values. The system shows the evidence; the analyst decides.
- Production-level running cost optimization. Credits aren't a constraint now; retry inefficiency is noted for later.

## 5. Who does what

| Who | Does | Never does |
|---|---|---|
| AI | Reads packages, proposes what each number means, finds look-alike numbers and differences, drafts plain-English explanations | Approves, types into delivered workbooks, sets analyst inputs |
| Pre-written programs | Fingerprint files, re-read every cited cell, check periods, units and sums, compare with the company map, sort items, type approved numbers, stamp verdicts | Decide what a number means |
| Financial analyst (approver) | Decides items on the decision list, enters analyst inputs, signs off | Re-checks items that passed (spot checks only) |
| Future interns (operators) | Start runs, upload packages, hand the decision list to the analyst | Change agents or programs without running the tests |

## 6. Rules the build must keep

1. **Universal agents.** No company names, sheets, cells or values in agents, programs or instructions. Company specifics live only in that company's map.
2. **Three separate states:** evidence checked (the cell exists and reads correctly), interpretation supported (the evidence backs the reading), analyst approved (a person authorized it for reuse). Only the third can lead to PASS.
3. **Answer keys never feed the system.** They only measure it.
4. **Analyst inputs are always asked for**, never carried forward silently. A changed multiple goes TO A PERSON unless the analyst has entered it.
5. **Data stays inside XPV's Microsoft environment.** Only sanitized reports (statuses and counts) leave it.
6. **Two-company rule:** add a new check only when a failure appears in two or more companies, or it's a basic check (layout, period, units, sums, fingerprints).

## 7. How success is measured

| Measure | Target |
|---|---|
| Wrong let through | 0 |
| Share of items passed automatically from the second quarter on | Clearly above 0, and rising each quarter |
| Analyst decisions per company at first approval | A handful, not dozens (the first real test produced 34 questions) |
| Analyst time per company-quarter | Below today's (today's estimate pending from AJ) |
| New workbook matches the analyst's own workbook | Every mechanical number exact; analyst inputs supplied by the analyst |
| Runs without Aria | An intern can run a quarter from the runbook |

## 8. Milestones (proposed)

| Dates | Milestone |
|---|---|
| Oct 19–30 | MVP: one company, two quarters, end to end (see the MVP build plan) |
| Nov 2–13 | OceanSight's Q3 package through the system; finish the answer key's extra checks |
| Nov 16–Dec 4 | Companies 3 and 4 onboarded and rolled forward; stretch: one new company |
| Dec 7–18 | Handover: runbook, tests, named owner, go/no-go for production use |

## 9. Risks

| Risk | What we do about it |
|---|---|
| A wrong number passes once PASS is allowed | PASS only on an exact match to an approved map plus checked evidence; every run measured against the analyst's own workbook during testing |
| Too many questions, so no time is saved | Decision list: only material decisions, duplicates merged |
| Analyst inputs (like a new multiple) make generated and real workbooks differ | Analyst inputs entered by the analyst and scored separately |
| Cells move between quarters | The map records meaning and source role, not just cell positions |
| Each company is built differently | Universal agents plus per-company maps; four structurally different companies tested |
| Aria leaves December 18 | Runbook, tests and owner from now; intern-run quarter before handover |
| Microsoft changes features | Rules live in company maps and tests, not in one tool |

## 10. Open questions

1. When does the analyst set the multiple and other judgment inputs: before the roll-forward, or after seeing the new numbers?
2. Which four companies, and which one first after the practice company?
3. Who is the named owner after December 18?
4. Is the LP report in one workbook or several, and who builds it today?
