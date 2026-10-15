# XPV Valuation Automation — CEO Briefing v2 (draft)

**Status:** Draft for build. Placeholders in `{{DOUBLE_BRACES}}` are filled from today's test runs (see the companion file `Pre-deck Test Runbook - Oct 14 2026.md`).
**Audience:** CEO and finance leadership. No technical background assumed.
**Approach:** Visuals first. Every slide's headline is a full-sentence claim, and the visual is the evidence for it (the "assertion–evidence" style used in scientific communication). Speaker bullets: 3 maximum, 20 words maximum each.

---

## 0. Legend, glossary and design system

### 0.1 Colour roles (used identically on every slide)

| Role | Colour | Hex | Used for |
|---|---|---|---|
| XPV anchor | XPV navy | `#0B3B60` (from xpvwaterpartners.com site colour) | Headlines, slide frame, structure lines |
| XPV secondary | `{{XPV_SECONDARY_NAME}}` | `{{XPV_SECONDARY_HEX}}` | Accent only (confirm from the XPV brand template) |
| AI | Green | `#2E8B57` | Anything AI does: reading, proposing, challenging, explaining |
| Locked tools | Water blue | `#2C7FB8` | Fixed programs that check, build and audit; always shown with a lock icon |
| Analyst | Orange | `#E07A1F` | Human judgment, decisions, sign-off; also the "analyst queue" |
| Files | Grey | `#9AA5B1` | Workbooks, source files, outputs |
| Failure / risk | Red | `#C0392B` | Failures and risks only, always paired with a ✗ or ⚠ icon (never colour alone) |
| Background | White / light grey | `#FFFFFF` / `#F4F6F8` | Slide background and panels |

Rule: one role, one colour, for the whole deck. If something is blue, a locked tool did it. If something is orange, a person decided it.

### 0.2 Layout and typography rules

- 16:9. Headline at top-left, navy, 28–32 pt, one sentence.
- Body text 18 pt minimum; about 15 words maximum of body text per slide.
- Sources bottom-left, 10–11 pt grey, same position on every slide.
- Charts: label lines and bars directly (no legends); grey everything except the one number that matters.
- Zoom slides: the mini flow sits in the same strip at the bottom of every zoom slide, with the current step highlighted and the others greyed.
- Use PowerPoint "Summary Zoom" or "Section Zoom" on slide 6 so clicking a flow block jumps to its zoom slide and returns.

### 0.3 Plain-language glossary

| Term | Meaning on these slides |
|---|---|
| Roll-forward | Updating last quarter's approved valuation workbook to this quarter using new monthly files |
| Approved workbook | The latest analyst-approved valuation; the starting point and the rulebook for the next quarter |
| Earnings before interest, taxes, depreciation and amortization (EBITDA) | Operating earnings; the valuation base |
| Adjusted EBITDA | EBITDA plus approved add-backs |
| Trailing twelve months (TTM) | The 12 months ending at the quarter-end |
| Limited partner (LP) report | The investor report the workbooks ultimately feed |
| AI (maker) | The AI that reads files and proposes what goes where |
| AI challenger | A second AI, ideally a different model, whose only job is to find gaps; it can object, never approve |
| Locked tools | Fixed programs with one job each. The AI can press the button; it cannot rewire it |
| Checker | Locked tool that re-reads every cell the AI cites and confirms it says what the AI claims |
| Builder | Locked tool that types approved numbers into approved cells, inside Excel |
| Auditor | Locked tool that compares the new workbook to the approved one and rejects unapproved changes |
| Status stamp | The verdict written into the file name; computed by the tools, not chosen by the AI |
| Company map | Per-company file (set up once) saying which source lines feed which model rows, and which source sheets are the real actuals |
| Maker–checker | The finance control where the person who prepares a number cannot be the person who approves it |
| Silent error | A wrong number that looks right and isn't flagged; the outcome we design hardest against |

---

## Main narrative (slides 1–6, 12, 13 are the skip-through path; 7–11 are the zoom block)

---

### Slide 1 — Hook (problem and destination in 10 seconds)

**Headline:** Every quarter, analysts rebuild the same valuation model. We are automating the mechanics, not the judgment.

**Visual:**
- Left panel, "Today": one orange figure surrounded by four grey tasks (find data, copy, update, check) and one small orange task (judge).
- Arrow to the right panel, "Where we are going": three blocks in a row: green "AI reads and proposes" → blue (lock icon) "Locked tools check and build" → orange "Analyst decides".
- Top-right progress pill: "About one third through · {{STATUS_PILL}}" (for example: "Mechanics proven · Real-data mapping scored").

**On-slide text:** the two panel titles and the three block labels only.

**Speaker bullets:**
- Analysts spend most of each quarter searching, copying and checking instead of judging.
- Target: AI reads and proposes, locked tools check and build, analysts decide.
- About a third through: the hard lesson is learned and the design is set.

---

### Slide 2 — Today

**Headline:** Today, most analyst time goes to mechanics, not judgment.

**Visual:** One horizontal stacked bar per roll-forward: Find data | Copy and update | Check | Judgment. Mechanics segments in grey, judgment in orange. Label each segment directly.
- If hours are measured: use `{{HOURS_FIND}}`, `{{HOURS_UPDATE}}`, `{{HOURS_CHECK}}`, `{{HOURS_JUDGE}}` per company per quarter, and `{{COMPANIES}}` × `{{QUARTERS}}` for the annual total.
- If not measured: keep proportions illustrative and print "Illustrative; real hours measured during testing" under the bar.

**Speaker bullets:**
- Same four steps, every company, every quarter.
- Judgment is the smallest slice and the only one that needs an analyst.
- {{HOURS_LINE}} (for example: "Bars are illustrative; real hours are measured in testing.")

---

### Slide 3 — How we iterated

**Headline:** Each build tested the riskiest assumption, then added or removed structure based on the result.

**Visual:** Horizontal timeline, left to right, each stage a coloured node with a result badge above and "what we changed" below.

| Stage | Colour | Result badge | What we changed |
|---|---|---|---|
| 1. Rule-based discovery (Copilot Studio, builds 1–11.6) | Blue | Answer keys and test bench built | Too rigid across companies |
| 2. AI-led discovery (builds 11.7–12.0) | Green | First real end-to-end onboarding run | Split into extractor and independent reviewer |
| 3. Steelman: one AI, no structure | Green | Found the data ✓ · built it wrong ✗ | Added write rules and a verifier |
| 4. Agent Builder, fake company (13.2–13.3) | Green + blue | 14/14 outputs correct · 6/6 traps handled | Added prior-quarter tie-out |
| 5. First real company (13.x) | Red ✗ | Wrong categories, hidden plug, "complete" claim | Rebuilt the controls |
| 6. Rebuilt controls (14.0–14.1) | Blue | 25/25 fake-data tests | Still unproven on real data |
| 7. Today's real-data mapping test | `{{T1_COLOUR}}` | `{{T1_BADGE}}` | `{{T1_CHANGE}}` |

**Possible outcomes for node 7:**
- Good: badge "{{T1_CORRECT}} of {{T1_TOTAL}} links correct or safely flagged · 0 silent errors".
- Mixed: badge "Sources right · {{T1_SILENT}} silent errors → company map needed".
- Poor: badge "Mapping not yet reliable → stop and rethink".

**Sources (footer):** Internal build logs, Copilot Studio builds 1–12; Agent Builder synthetic runs 1–2 (Build 13.2–13.3); Build 13.x real-run log; v14.1 regression suite; today's map-only run ({{T1_DATE}}).

**Speaker bullets:**
- Started heavily controlled, tested whether AI needed it, removed what it didn't.
- Fake-company tests passed; the real company exposed what fake data couldn't.
- Studio work isn't wasted: it becomes onboarding, challenger and grader.

---

### Slide 4 — What broke, and why

**Headline:** Every fix moved the failure somewhere else, because the AI was still both maker and checker.

**Visual (two parts):**
- **Top band, "whack-a-mole":** four tiles left to right. Each shows the failure (red ✗) and the patch we applied (blue lock). The last tile is lit red.
  1. Steelman: headline Adjusted EBITDA typed in over a formula; add-back rows zeroed → patched with write rules.
  2. Fake-company run 1: last quarter's column quietly showed this quarter's numbers → patched with prior-quarter tie-out.
  3. Fake-company run 2: AI copied example answers → patched by removing examples.
  4. Real company: the AI wrote its own code around the tools → wrong categories, hidden plug, said "complete".
- **Bottom, "one AI, every role":** one green circle with five arrows to: Read · Write its own code · Edit workbook · Check itself · Report. Arrow ends at a red-flagged "Complete ✓". Beside it, the finance equivalent: "Maker = Checker".

**Real examples (callouts on the last tile):**
- Temporary labour landed in the setup-expenses row.
- One line was calculated as "total minus everything else", hiding any error inside it.
- The run was reported complete while its own checks showed failures.

**Sources (footer):** Steelman run log; Build 13.2–13.3 synthetic runs; Build 13.x real-run log and generated script (sanitized); "Build 13 Structural Failure Evidence" (internal).

**Speaker bullets:**
- The model stayed similar; failures surfaced wherever our setup gave it unchecked authority.
- Real example: temporary labour landed in setup expenses, then a plug hid it.
- Finance's oldest control applies: the maker can't be the checker. That's the fix.

---

### Slide 5 — It's not just us

**Headline:** The whole industry sees this, and humans make spreadsheet errors too.

**Visual:** Four tiles, one number each, same layout.

| Tile | Big number | One-line caption | Source |
|---|---|---|---|
| Complete-looking ≠ correct | **90% vs 34%** | Best AI changed about 90% of the cells a financial model needed, yet only 34% of models were correct | SpreadsheetBench 2 (June 2026; NeurIPS 2026) |
| Reading vs judging | **< 50%** | Frontier models do well at extraction and calculation; none clears 50% on judgment calls | Realm financial reasoning benchmark, micro1 (July 2026) |
| AI games its own checks | **93% → 1%** easy · **66% → 54%** realistic | A "stop if checks are wrong" instruction nearly eliminated cheating on simple tasks, but barely helped on realistic ones | ImpossibleBench (Zhong, Raghunathan, Carlini, 2025) |
| Humans err too | **94%** | Share of field-audited business spreadsheets containing errors | Panko, spreadsheet error research (field audits) |

**Bottom line (navy band):** "Goal: fewer errors, caught before use, with a full audit trail — at less analyst time."

**Sources (footer):** arxiv.org/abs/2606.29955 · micro1.ai/benchmark/financial-reasoning · arxiv.org/abs/2510.20270 · arxiv.org/pdf/0802.3457

**Speaker bullets:**
- Best AI touched 90% of required cells, yet got financial models right a third of the time.
- Instructions alone don't stop AI shortcuts on realistic work; structure does.
- Humans err too; our goal is fewer errors, caught early, fully auditable.

---

### Slide 6 — The flow at 40,000 feet (zoom hub)

**Headline:** AI proposes. Locked tools prove. Analysts decide.

**Visual:** Five zones in one horizontal flow, each zone a clickable Zoom link to slides 7–11. Each zone shows coloured dots for who touches it.

| Zone | Plain name | Steps inside | Who touches it | Frequency |
|---|---|---|---|---|
| 1 | Learn the company | AI drafts the company map → analyst approves | 🟢 AI · 🔵 Tools · 🟠 Analyst | Once per company |
| 2 | Read the new quarter | AI proposes every link → AI challenger hunts for gaps | 🟢 AI only | Every quarter |
| 3 | Check and decide | Checker re-reads every claim → analyst decides only new items | 🔵 Tools · 🟠 Analyst (exceptions) | Every quarter |
| 4 | Build and prove | Builder updates Excel → auditor compares → status stamp | 🔵 Tools only | Every quarter |
| 5 | Approve and learn | Analyst judgment and sign-off → decisions saved to company map | 🟠 Analyst · 🔵 Tools | Every quarter |

Loop arrow from zone 5 back to zone 2: "Approved decisions are remembered, so next quarter has fewer questions."

**Bottom strip, "What we will not do" (red icons, small):** AI writing its own code against the workbook · AI checking its own work · AIs voting as proof · instructions as the only control · AI choosing the source sheet unreviewed.

**Speaker bullets:**
- AI reads and proposes; it never writes the workbook or grades itself.
- Locked tools check and build; the AI can use them, not change them.
- Analysts see only new decisions and exceptions, then make the valuation calls.

---

## Zoom block (slides 7–11)

Every zoom slide uses the same layout:
- **Top:** headline.
- **Middle:** four swimlanes, always in this order: 🟢 AI · 🔵 Locked tools · 🟠 Analyst · ⚪ Files. Each lane says, in a few words, what that party does in this step. A lane with nothing to do shows "—" (that's information too).
- **Right side panel:** "Cannot do" (what each party is blocked from) and "Output" (what leaves this step).
- **Bottom strip:** the five-zone mini flow with this zone highlighted.

---

### Slide 7 — Zoom 1: Learn the company (once per company)

**Headline:** Once per company, AI drafts a map of the model and an analyst signs it off.

| Lane | What happens |
|---|---|
| 🟢 AI | Reads the approved workbook and last quarter's source files. Drafts the company map: what each model row means, which source sheets are the real actuals (not budget, not pro forma), and which labels pair up |
| 🔵 Locked tools | Re-read every cell the draft cites; flag anything missing or mismatched |
| 🟠 Analyst | Reviews and approves the map once. It becomes a versioned company file |
| ⚪ Files | In: approved workbook, source files, valuation policy. Out: approved company map v1 |

**Cannot do:** The AI cannot approve its own map.
**Analogy (one line on slide):** "A new analyst's first-week notes, written by AI, signed off by a senior."
**Evidence badge:** "Onboarding agents (extractor and reviewer) completed a first real end-to-end run · benchmark {{ONBOARD_BENCH_STATUS}}"
**Effort badge:** "Upfront cost: about {{ONBOARD_HOURS}} analyst hours per company × {{COMPANIES}} companies"

**Speaker bullets:**
- Done once per company: AI drafts the company map, an analyst approves it.
- It pins down which sheets are real actuals and what each model row means.
- This is the main upfront cost; every later quarter reuses it.

---

### Slide 8 — Zoom 2: Read the new quarter (propose and challenge)

**Headline:** AI proposes every link, and a second AI looks for what the first one missed.

| Lane | What happens |
|---|---|
| 🟢 AI (maker) | Proposes each link in plain terms: "this source line → that model row, same sign, these 12 months" |
| 🟢 AI (challenger, different model) | Asks only: what's left unused? Could another sheet be the real actuals? Any sign or category doubts? |
| 🔵 Locked tools | — (nothing written yet) |
| 🟠 Analyst | — |
| ⚪ Files | In: new monthly files and the company map. Out: a proposal list, not edits |

**Cannot do:** Neither AI can touch the workbook. The challenger can object but never approve.
**Visual detail:** show one example proposal card (sanitized): "Temporary labour (source) → Temporary labour add-back (model) · same sign · Jul–Jun".
**Evidence badge:** "Today: maker proposed {{T1_TOTAL}} links · challenger caught {{T6_CATCHES}} real issues, {{T6_FALSE}} false alarms" (or "Challenger test pending").

**Speaker bullets:**
- AI proposes every link as a list; nothing touches the workbook yet.
- A different-model challenger hunts for gaps; it can object, never approve.
- Different models share fewer blind spots, but agreement still isn't proof.

---

### Slide 9 — Zoom 3: Check and decide

**Headline:** A locked checker re-reads every claim; analysts see only what's new.

| Lane | What happens |
|---|---|
| 🟢 AI | Explains any queued item in plain English. Cannot approve |
| 🔵 Locked tools (checker) | Re-reads each cited cell itself: right sheet, right months, right meaning, right sign, not used twice. Sorts every link into three bins |
| 🟠 Analyst | Reviews only the orange bin: Approve / Reclassify / Exclude, with the evidence and dollar impact shown |
| ⚪ Files | Out: a frozen, approved link list |

**Visual:** a funnel or three-bin bar for one company's quarter.
- 🔵 Auto-pass (seen and approved before): `{{BIN_PASS}}`
- 🟠 Analyst queue (new or changed): `{{BIN_QUEUE}}`
- 🔴 Stop (plug, invented zero, double count, wrong source sheet): `{{BIN_STOP}}`

(First quarter for a company: most items are orange. The share of blue grows every quarter as decisions are remembered; label this on the chart.)

**Cannot do:** The AI cannot move an item between bins.

**Speaker bullets:**
- The checker re-reads each cited cell instead of trusting the AI's notes.
- Known links pass automatically; new ones queue for the analyst with evidence.
- Plugs, invented zeros or double-counted lines stop the run outright.

---

### Slide 10 — Zoom 4: Build and prove

**Headline:** Locked tools build inside Excel, audit the result and stamp its status.

| Lane | What happens |
|---|---|
| 🟢 AI | Writes a plain-English summary, reading only from the saved file. Cannot change the status |
| 🔵 Locked tools (builder) | On a copy of last quarter's approved workbook: extends the existing pattern, types in only approved numbers, recalculates in Excel |
| 🔵 Locked tools (auditor) | Compares new against approved: any unapproved change fails. Rebuilds Adjusted EBITDA from detail and compares to the company's headline. Confirms key outputs are live and non-zero |
| 🟠 Analyst | — |
| ⚪ Files | Out: the draft workbook with its status in the file name |

**Visual:** the four status stamps, as they appear in a file name:
- 🔵 APPROVAL READY
- 🟠 DRAFT — ANALYST JUDGMENT REQUIRED
- 🔴 INCOMPLETE — DO NOT USE
- 🔴 FAILED — DO NOT USE

**Evidence badge:** "Today's Excel test: builder wrote {{T5_WRITES}} approved values in {{T5_SECONDS}} s; refused the bad batch ✓ {{T5_REFUSED_LABEL}}; refused overwriting a formula ✓ {{T5_REFUSED_FORMULA}}"

**Cannot do:** Nobody, including the AI, can hand-edit the file between audit and stamp.

**Speaker bullets:**
- The builder works inside Excel, typing only approved numbers into approved cells.
- Any change not on the approved list fails the file.
- The status is computed and stamped in the file name; the AI can't upgrade it.

---

### Slide 11 — Zoom 5: Approve and learn

**Headline:** Analysts make the valuation calls, and every decision makes next quarter easier.

| Lane | What happens |
|---|---|
| 🟢 AI | Drafts the review memo and highlights what changed. Cannot sign |
| 🔵 Locked tools | Record each decision. Approved links are added to the company map. Any new failure becomes a permanent test |
| 🟠 Analyst | Multiple, comparables, new adjustments, ownership changes, final sign-off |
| ⚪ Files | Out: approved workbook, which becomes next quarter's starting point |

**Visual:** loop arrow back to Zoom 2, plus a small illustrative chart: "share of links auto-passed" rising across quarters 1 → 4 (label clearly "Illustrative until measured").

**Speaker bullets:**
- Valuation judgment stays with analysts: multiple, comparables, adjustments, sign-off.
- Every approval is remembered, so the analyst queue shrinks each quarter.
- Every new failure becomes a permanent test, so it can't recur silently.

---

## Decision slides

---

### Slide 12 — Options: speed versus safety

**Headline:** We recommend a locked pipeline: slower to build, but it can't produce silent errors unnoticed.

**Visual:** One row per option. Left: a tiny flow icon in role colours. Middle: a **stage ladder** of six dots (filled = reached): Designed · Built · Fake-data tested · Real-data tested · Blind-graded · In use. Right: three rating dials.

| Option | How it works | Stage reached (honest) | Silent-error risk | Analyst time saved | Effort still needed |
|---|---|---|---|---|---|
| A. Fully autonomous AI (Build 13) | One AI does everything | Real-data tested → **failed** | 🔴 High (observed) | Looks high, but every output needs full re-checking | None: rejected |
| B. Guarded AI in Agent Builder (current, v14.1) | Locked tools exist, but the AI can still work around them; problems are caught after the fact | Built · fake-data 25/25 · real mapping `{{T1_STAGE}}` | 🟠 Medium: catches, can't prevent | Expected medium–high; **not yet measured** | Small (known fixes) |
| C. Locked pipeline (Copilot Studio + Excel scripts) | AI only proposes; locked flows build and audit; the AI can't touch the delivered file | Designed · Excel smoke test `{{T5_STAGE}}` | 🔵 Low expected; **unproven** | Expected medium–high; **not yet measured** | Largest: build flows, port checks, onboard {{COMPANIES}} companies |
| C+. Locked pipeline + different-model challenger | Adds an independent gap-hunter to C | Reviewer agent built (Studio); as challenger `{{T6_STAGE}}` | 🔵 Lower expected | Same as C | Small add-on; extra run cost |
| D. Rule-based per company | Fixed rules, no AI | Built for discovery only (builds 1–11.6); **never tried as a roll-forward** | 🟠 Medium: fails loudly on layout changes, silently on look-alike rows | Medium for stable companies; high upkeep | Large per company |
| E. AI assistant only | AI explains and suggests; analysts do the work | **Not built or tested** | Same as today | Low (estimate) | Low |

**Footnote on slide:** "D and E were not tested end to end; shown as reference points. No time savings are claimed until measured."

**Running cost row (small, below table):** B: within the existing Copilot licence (`{{CONFIRM_B_COST}}`). C/C+: Copilot Studio capacity is consumed per run (`{{C_COST_PER_RUN}}` × about 40 runs per quarter).

**Risks of the choice (right-side panel, red ⚠ icons, one line each):**
- Too AI-forward → a silent error reaches the LP report.
- Too conservative → small payoff, project stalls.
- Microsoft changes features monthly → keep the rules in company files and tests, not in one tool.
- Onboarding cost → {{COMPANIES}} company maps to approve.
- Key person → my term ends December 18; handover is designed in from now.

**Speaker bullets:**
- Autonomous is fastest and least safe; assistant-only is safe but barely saves time.
- Recommended: locked pipeline with a different-model challenger; current agent remains the test vehicle.
- Biggest risks: onboarding effort, Microsoft changes, and ownership after December.

---

### Slide 13 — Where we are and the gates ahead

**Headline:** Mechanics are proven and the design flaw is fixed; real-data gates come next, each with a stop rule.

**Visual:** a progress track. Ticks (navy) for completed mini-steps; diamonds for gates; today's position marked.

| # | Mini-step or gate | Status |
|---|---|---|
| 1 | Answer keys and test bench | ✓ |
| 2 | Steelman: AI understands the valuation | ✓ |
| 3 | Fake company: 14/14 outputs, 6/6 traps | ✓ |
| 4 | First real run: design flaw found | ✓ (lesson) |
| 5 | Controls rebuilt: 25/25 fake-data tests | ✓ |
| 6 | Real-data mapping scored | `{{T1_TICK}}` |
| 7 | Excel build route proven | `{{T5_TICK}}` |
| ◆ Gate 1 | Mapping accuracy acceptable? | `{{GATE1_RESULT}}` |
| ◆ Gate 2 | Full build, one company, graded blind | `{{GATE2_DATE}}` |
| ◆ Gate 3 | Second, structurally different company | `{{GATE3_DATE}}` |
| ◆ Gate 4 | Build the locked pipeline for production | `{{GATE4_DATE}}` |
| ◆ Gate 5 | Handover to non-technical owner | Before December 18, 2026 |

**Banner:** "No accuracy promises until blind results."

**Possible outcomes for Gate 1:**
- Pass: "Proceed to full blind build."
- Partial: "Add company maps before full build."
- Fail: "Pause; AI mapping not yet reliable."

**Speaker bullets:**
- Done: mechanics proven, design flaw found, controls rebuilt, first real mapping scored.
- Next: blind run, a second different company, then the production build decision.
- Every gate has a stop rule; poor mapping means rethink, not patch.

---

## Appendix (what and why, not how)

### A1. Glossary
Reuse section 0.3 as one slide.

### A2. The 20 observed failures, in five themes

| Theme | What happened (plain language) | What now prevents it | Prevented or only caught? |
|---|---|---|---|
| Wrong meaning | Real numbers placed in the wrong category; positions used instead of meaning | Company map and checker | B: caught · C: prevented |
| Hiding errors | A "total minus the rest" plug; signs stripped; missing values typed as zero | Checker stops plugs, invented zeros and sign flips | B: caught · C: prevented |
| Wrong source | No decision on actual vs budget, company-only vs pro forma before building | Approved source sheets in the company map | Prevented once approved |
| Damaging the workbook | Formatting deleted to force a save; history changed | Builder works inside Excel; auditor rejects unapproved changes | B: caught · C: prevented |
| Grading itself | Checks failed but the run was called "complete"; summary didn't match the file | Status computed by tools and stamped in the file name | B: caught · C: prevented |

Source: "Build 13 Structural Failure Evidence" (internal).

### A3. The one line that explains Build 13 (sanitized)
Show on one slide, large:
`Other = Total adjustments − (all the items it did map)`
Caption: "This is a plug. It makes the schedule add up, whatever was missed, double-counted or misclassified."

### A4. What every run returns
The four status stamps (slide 10) plus: the draft workbook, a one-page summary, the analyst queue with evidence, and the updated company map proposal.

### A5. Why instructions alone are not enough
ImpossibleBench detail in two bars (easy vs realistic tasks). One line: "Making checks read-only works better than asking nicely."

### A6. Microsoft facts that shape the design (plain language)
- Agent Builder and Copilot Studio can both run Python, but the AI can also write its own code there. That's why the delivered file must be built by a flow the AI can't touch.
- The AI's coding ability can be switched off per agent (today's test: {{T3_RESULT}}).
- Excel scripts run in steps of up to about two minutes; long builds are split into steps, resumed automatically or with "RESUME".
- Sources: learn.microsoft.com (Agent Builder code interpreter; Copilot Studio flows; Office Scripts limits).

### A7. How success will be measured
Links correct, silent errors (target: zero), share auto-passed, analyst queue size, analyst hours versus today, outputs matching the approved workbook in blind grading.

### A8. Handover and ownership
Who runs it after December 18 (`{{OWNER}}`), what they need (runbook, company maps, test bench), what happens when Microsoft changes something.

### A9. Sources
- SpreadsheetBench 2 (June 2026): https://arxiv.org/abs/2606.29955
- Realm financial reasoning benchmark, micro1 (July 2026): https://www.micro1.ai/benchmark/financial-reasoning
- ImpossibleBench (2025): https://arxiv.org/abs/2510.20270
- Panko, spreadsheet error research: https://arxiv.org/pdf/0802.3457
- BlueFin financial spreadsheet benchmark (2026): https://arxiv.org/html/2605.30907
- Microsoft Learn: Agent Builder code interpreter; Copilot Studio flows; Office Scripts platform limits
- Internal: Copilot Studio builds 1–12 logs; steelman run; Build 13.2/13.3 synthetic runs; Build 13.x real-run log; v14.1 regression suite; today's tests T1–T6 ({{T_DATE}})
