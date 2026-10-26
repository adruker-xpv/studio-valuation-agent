# XPV Valuation Automation — System Spec

*Draft 1, October 16, 2026. The rulebook for how the finished system behaves. The agents, the code and the tests are all checked against this doc. When a rule changes, change it here first, then record the decision in the Log.*

---

## 0. Legend

| Term | Meaning |
|---|---|
| Run | One company, one quarter, from supplying files to the signed-off workbook |
| Extractor | The AI agent that reads the files and proposes what each number is and what changed |
| Checking code | Tested programs that confirm every AI claim and do all typing |
| Company memory | One file per company of confirmed decisions (section 7) |
| Fingerprint | A digital code for a file; any change to the file changes it |
| Pass / to the analyst / stopped | The three possible results for each item (section 5) |
| Release stage | Track changes, approve new or unsure, or auto (section 6) |
| Adjusted earnings (Adjusted EBITDA) | Earnings after approved one-off adjustments; most companies are valued as a multiple of this |
| Pro-forma financials | A sheet that restates earnings as if an acquired business had been owned for 12 months. When present, it is used for the valuation |
| Ownership table (cap table) / payout order (waterfall) | Who owns what / the order in which value is paid out to owners |
| Source note | A comment on every typed number saying which file, sheet and cell it came from |

---

## 1. Ground rules

1. **Every approval is made by a person.** The system proposes, checks and types. It never approves.
2. **AI never types into a workbook.** Only checking code does, and only confirmed values.
3. **Universal agents.** No company names, sheets, cells or values in agents, code or instructions. Company specifics live only in company memory.
4. **Answer keys only measure.** They never feed the system.
5. **Exact matching.** Rounding is allowed only where it's declared. There is no general tolerance.
6. **Data stays inside XPV's Microsoft 365.** Only sanitized results (statuses and counts) leave it.
7. **Two-company rule.** Add a new check only when a failure appears in two or more companies, or the check is basic (layout, periods, units, totals, fingerprints).

---

## 2. Inputs for a run

| Input | Where it comes from |
|---|---|
| Last quarter's approved valuation workbook | The company's "approved" folder in SharePoint, picked up by Power Automate. Supplied by a person until that folder exists |
| The new quarter's monthly files | Uploaded by the operator |
| Company memory | Saved by code after the last run |
| Investor fund workbooks | Phase C only |

---

## 3. Start of every run: the analyst answers

| # | Question | If yes / answer |
|---|---|---|
| 0 | Which release stage: track changes, approve new or unsure, or auto? | A company's first run is always track changes. The screen shows the company's record: quarters run and wrong numbers found |
| 1 | Confirm the multiple, or enter the new one and the reason | Always asked, at every stage |
| 2 | Was there an acquisition, merger or sale of part of the business? | See the table below |
| 3 | Are any earnings adjustments new, removed or changed? | Enter each one with its amount and reason |
| 4 | Are comparable companies being added or removed? | List the changes (Phase B will suggest these) |
| 5 | Is the valuation method changing? | The workbook is marked for full review |
| 6 | Has anyone joined or left the ownership table? | The analyst confirms the new table. If not, shares carry forward |
| 7 | Has the payout order changed? | That company's run stops |
| 8 | Is there new debt, a repayment, a refinancing or an unusual cash item? | Confirm the amounts and the source |
| 9 | Were there one-off events that could affect value? | Note how to treat it |
| 10 | Did a meeting with the company's CFO agree any changes? | Enter the agreed changes |
| 11 | Has XPV's ownership share changed, or is the company moving to held at cost or exit? | A company held at cost skips the roll-forward |

**Acquisitions and sales (question 2)**

| Answer | System behaviour |
|---|---|
| No | Normal run |
| Closed this quarter, no pro-forma sheet yet | That part stops. The analyst builds the sheet. The system re-learns that one sheet, and the analyst confirms it into memory |
| Closed earlier, pro-forma sheet exists | Rolled forward like any sheet. Memory holds the closing date, and the system asks for confirmation when the 12 months end |
| Sale of part of the business | Stops until the analyst confirms how the removed earnings are treated |
| Agreed, not closed | No change; noted in memory |

**At onboarding only:** which file wins when files disagree; each file's role; the 12-month period rule; which cells are analyst inputs; known look-alike numbers; approved label variants; past deals; the named approver.

---

## 4. Checks code always runs

| Check | What happens |
|---|---|
| Workbook version | Compare last quarter's workbook with the fingerprint saved at approval. If it differs, code lists every changed cell, the AI explains each change, and the analyst confirms |
| Past periods revised | Comparison columns are refreshed from the latest monthly files. Any past number that changed is flagged to the analyst |
| Files disagree | Use the file memory says wins. If memory has no rule, the item stops |
| Every cited cell | Re-read; it must exist and match |
| Periods, units, totals | The right months, matching units, totals that add up |
| Hidden rows and columns | Compared with last quarter's approved version; any newly hidden or newly shown row is flagged |
| Footnotes | Numbers run in order with none skipped or repeated, and every footnote marker has a note |
| Formulas | Formula cells are never overwritten; formulas stay live after recalculation |

---

## 5. Sorting rules

| Result | When |
|---|---|
| **Pass** | Matches a confirmed memory entry exactly, and every check above is clean |
| **To the analyst** | New, changed in meaning, a "yes" answer to a standard question, or anything code can't fully confirm |
| **Stopped** | Contradicted, missing, out of date, wrong source, totals don't add up, files disagree with no rule, or the payout order changed |

---

## 6. Release stages

| Stage | Pass items | To the analyst | Stopped |
|---|---|---|---|
| 1. Track changes | Shown for approval | Shown for approval | Must be resolved |
| 2. Approve new or unsure | Applied and logged | Shown for approval | Must be resolved |
| 3. Auto | Applied and logged | Judgment calls and "yes" answers only | Must be resolved |

At every stage the analyst signs off the finished workbook.

---

## 7. Company memory

**Update rules**

- Entries are only added; nothing is edited or deleted.
- The latest entry for an item wins once the analyst confirms it.
- Unconfirmed entries are marked "proposed" and can never make an item pass.

**Every entry carries:** item ID, value or rule, quarter, who confirmed it, date, and the analyst's own words.

**Format:** one file per company, written only by code, with a readable Excel view generated from it.

| Section | Holds |
|---|---|
| Company | Fund, revalued quarterly or twice a year, held at cost yes/no, named approver, run record |
| Files | Each file's role; fingerprint of the last approved workbook |
| Items | For each number: meaning, source file role, sheet, approved labels, last cell seen, period rule, units, carried or refreshed, analyst input yes/no |
| Adjustments | Each approved adjustment: amount rule, reason, first and last quarter |
| Deals | Acquisitions and sales: closing date, pro-forma sheet yes/no, end of the 12-month pro-forma period |
| Ownership table | Participants as last approved; date of the last change |
| Checks | Known look-alikes; which file wins when files disagree |

---

## 8. Outputs of a run

1. The new valuation workbook. It is a copy of last quarter's, with confirmed values typed by code, a source note on every typed number, and formulas kept live.
2. A change log. Every change is listed with old value, new value, source, result (pass / to the analyst / stopped), and type ("this quarter only" or "saved to memory").
3. A verdict in the file name: ready for sign-off, or needs attention.
4. New memory entries, saved as "proposed" until the analyst confirms them.
