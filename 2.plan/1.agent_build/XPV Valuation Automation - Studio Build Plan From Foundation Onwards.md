# XPV Valuation Automation — Studio Build Plan

From the Studio build (today) to a working quarterly system by December 18, 2026. Plain language throughout. This is a new file; it doesn't replace the MVP Build Plan.

---

## Legend

| Term | Meaning |
|---|---|
| Studio build (today) | The Copilot Studio agents built so far: extractor, reviewer, test bench, and their checking code |
| Studio build | The streamlined target this plan builds towards |
| Extractor | The AI agent that reads a company's files and traces how its value is built |
| Reviewer | A second AI agent that checks the extractor's work independently. **Removed from the main flow by this plan** |
| Test bench | The agent that grades runs against hidden answer keys. Development only, never in a live quarter |
| Checking code | Tested programs (verify.py and others) that re-open the files and confirm every claim the AI makes |
| Answer key (Gold key) | The correct answers, written by a person before any run and hidden from the AI. Used only to grade |
| Core answers | The 10 main facts of a valuation, from the method to the value the fund reports |
| Anchor | The cell (or cells) that proves an answer |
| Diagnostic items | Extra checks in an answer key: look-alike numbers, differences between files, and judgment calls |
| Fingerprint | A digital code for a file; any change to the file changes it |
| Company memory | What the analyst approved for a company, saved and reused every quarter |
| Roll-forward | Updating last quarter's approved workbook with the new quarter's numbers |
| Backtest | A test on a past quarter where the right answer is already known |
| Regression check | Re-running every frozen test after a change, to prove nothing that worked before broke |

---

## 1. Where we are (October 15, 2026)

| Run | Company | Files | Core answers right | Wrong claims let through |
|---|---|---|---|---|
| AI-first (Agent Builder) | Company 1 | 5 | 3 of 10 | — (everything sent to review) |
| Studio build (today) | Company 1 | 5 | 10 of 10 | 0 |
| AI-first (Agent Builder) | Company 2 | 6 | 3 of 9 | — (everything sent to review) |
| Studio build (today) | Company 2 | 6 | 10 of 10 | 0 |

Company 2, Studio build, in more detail:

- Answer key passed validation.
- 10 of 10 core answers right; nothing wrong, nothing missed.
- All six files proven identical to the ones the key was written from (fingerprints).
- Checking code confirmed the run.
- 7 of 8 anchors exact. The one miss: the 12-month period was right, but it was proven with the 12 numbers instead of the 12 date headers.
- 12 diagnostic items couldn't be graded yet (5 look-alikes, 2 differences, 5 judgment calls), because the key lacked matching details (fix: Phase 2, item 2). They don't reduce the core score.

**What this means:** the extractor finds the valuation without the reviewer. The question now changes from "can it find the valuation?" to "does it work on different companies, every time, with less analyst work?"

---

## 2. Target flow

**Onboarding (once per company)**

1. Company files
2. Extractor traces the value
3. Checking code proves every claim, and sends failures back to the AI to fix
4. Analyst answers the few real questions
5. Company memory saves the approvals

**Each quarter (planned)**

1. Latest version of last quarter's workbook, plus the new monthly files
2. Extractor proposes what changed
3. Checking code checks each proposal against the files and the memory
4. Analyst decides only what's new or unclear
5. Code builds the new workbook, with a source note on every typed number and a change log

**Development only**

- Test bench grades runs against hidden answer keys.
- Its results go to the builder, never to the extractor.

**Reviewer:** removed from the main flow. It isn't deleted; it stays on the shelf for an unusual company if a later test shows we need it.

---

## 3. Rules for every change

- **Universal agents.** No company names, cells or rules in agents, skills or instructions. Company specifics live only in that company's memory.
- **Answer keys only measure.** They never feed the system.
- **AI proposes; code checks and makes every change; the analyst approves once.**
- **Confidence is decided by code, never by the AI.**
- **No fitting to one company.** A change to the extractor must be generic. If it only helps one company, it doesn't go in.
- **Regression check after every change.** Re-run every frozen answer key (Company 1, Company 2, then each new company). Nothing that scored right before may get worse.
- **Exact matching is the default.** Rounding is allowed only where an answer key declares it. No general tolerance.
- **Fingerprints, not file names or W-numbers, identify files.** W1, W2 and so on are local labels inside one run.

---

## 4. Phases

### Phase 0 — Lock the baseline (October 16–19)

- Save the current extractor, its skills and instructions as the baseline version.
- Freeze the two answer keys and their workbook fingerprints as the regression set.
- **Done when:** both companies re-score 10 of 10 from the frozen files.

### Phase 1 — Remove the reviewer from the flow (October 19–21)

- Take the reviewer out of the run order and the workflow. Don't change the extractor.
- Re-run the extractor alone on both companies.
- **Done when:** 10 of 10 on both, with the same anchors.

### Phase 2 — Test bench 13.2: fairer, more complete grading (October 19–30)

All changes are additive. Old answer keys keep working unchanged.

1. **Period evidence.** Grade the 12-month period on header evidence (the 12 date headers) and value evidence (the 12 numbers) separately. A full answer gives both. Don't simply loosen the check.
2. **Matching details written automatically.** When an answer key is written, the tool proposes stable IDs and verified cells for every look-alike, difference and judgment call. The analyst approves; nobody has to remember scorer details.
3. **Component evidence.** Cash and debt cells that build the debt-and-cash step are marked as components, so they stop triggering "doesn't equal the total" warnings.
4. **Separate report sections:**
   - core answers
   - anchors
   - look-alike handling
   - differences found
   - judgment calls kept open
   - file integrity
   - checking-code result

   Missing diagnostic details never lower the core score.
5. **Keep:** fingerprint-first file matching, local W-numbers, declared rounding only.
- **Done when:** 253 code tests plus the new ones pass, both companies score the same core result, and the 12 diagnostic items can be graded.

### Phase 3 — Prove it generalizes (October 26–November 13)

- Choose a third company with a genuinely different structure.
- Write and freeze its answer key independently, before any run.
- Run the extractor unchanged.
- Run each company 3 times to test repeatability.
- **Done when:** results are reported per company and per run, including the worst one. If it fails, fix it generically and re-run the regression set.

### Phase 4 — Fewer, better questions (October 26–November 13)

Generic extractor improvements only:

- The period answer cites the headers and the values.
- The AI lists every plausible candidate number with its source; code rules out invalid ones before anything is chosen.
- Measure the analyst's workload: questions per company, and how many were real decisions.
- **Done when:** fewer questions with 0 wrong answers let through, on all frozen companies.

### Phase 5 — Company memory (October 26–November 13)

- Store the analyst's answers twice: their own words, for audit, and a structured entry (item, decision, cell, who, when). The analyst confirms; code saves.
- Entries are never overwritten; a new version is added and the latest applies.
- What it holds:
  - each file's role
  - where each value lives
  - approved label variants
  - period rules
  - analyst-input cells
  - approved adjustments
  - known look-alikes
  - which file wins when files disagree
- **Done when:** a second run on the same company uses memory and asks only about what changed.

### Phase 6 — Quarterly mode and workbook builder (October 26–November 27; hardest part)

- Order of work:
  1. AI proposes each change
  2. code checks it
  3. code sorts it: pass, to the analyst, or stop
  4. code makes the change and adds a source note
  5. code checks the whole workbook
  6. output: the new workbook plus a change log
- Change log types: "this quarter only" or "permanent, saved to memory."
- **Backtest** on the company with two past quarters. The analyst's own numbers (such as the multiple) are entered from the real workbook first; every other cell must match exactly.
- **Fallback:** checked numbers plus a list of changes for the analyst.
- **Done when:** mechanical cells match exactly, formulas stay live, and 0 wrong numbers are let through.

### Phase 7 — Live quarter and more companies (November 9–December 4)

- Run the first company's next real quarter.
- Add more companies with different structures, at least 4 in scope.

### Phase 8 — Handover (December 7–18)

- Run guide for non-technical owners and future interns.
- Go/no-go decision.

---

## 5. Scorecard (reported for every company and every run)

| Measure | Target |
|---|---|
| Core answers right | 10 of 10 |
| Wrong answers let through | 0 |
| Anchors exact or approved equivalent | All |
| Look-alikes correctly rejected | All graded |
| Judgment calls kept open, not guessed | All |
| Files proven identical (fingerprints) | All |
| Analyst questions per company | Falling over time, only real decisions |
| Same result across 3 runs | Yes |

---

## 6. Next round of test bench fixes (saved, not yet built)

- Certified vs development answer keys (a development score clearly labelled as such)
- Optional "materiality" beside REAL / ROUNDING / UNRESOLVED
- An optional XPV investment value item scored separately from company value
- Later: grading the whole chain, step by step, from the monthly numbers to the fund value

---

## 7. Open questions

- Which company is the third test (genuinely different structure)?
- Analyst review of the answer keys: when?
- AJ's hour estimates for today's manual process: still pending.
