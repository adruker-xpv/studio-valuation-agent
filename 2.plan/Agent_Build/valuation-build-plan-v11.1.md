# Valuation agent – build plan, build 11.1 (end to end)

Build 11.1 (package 11.1.0) supersedes builds 9, 10 and 11. Setup, tests and running: `valuation-agent-build-11.1-guide.md`. Phase 1 (onboarding: mapping, approval, register, intake, file
gathering from knowledge) is built. Phases 2–3 (backtest build, quarterly generation, close) are specified here.

---

## 1. Glossary
| Term | Meaning |
|---|---|
| Limited partner (LP) report | The quarterly investor report. Everything works back from its per-company row. |
| LP row / LP fields | The per-company numbers the LP report needs: enterprise value, equity value, value to XPV, multiple on invested capital (MOIC), metrics, ownership |
| Enterprise value (EV) | Value before debt and cash: selected multiple × metric, or a weighted blend of revenue and EBITDA values |
| EBITDA / adjusted EBITDA | Earnings before interest, tax, depreciation and amortization; adjusted adds approved one-time items (nine categories) |
| Trailing twelve months (TTM) | Sum of the last 12 monthly values (or 4 quarters) ending at the valuation month |
| Bronze / silver / gold | Raw files, never modified / the company's normalised data in the company file / the LP numbers Excel calculates |
| Identity | A valuation equation Python checks against Excel: EV = multiple × metric; equity = EV + cash − debt; value to XPV = equity × ownership (÷ FX); MOIC = (value + proceeds) ÷ invested capital |
| Python chain | All identities plus Python re-computing each LP formula from its saved inputs |
| Liveness checks L1–L5 | L1 LP values are formulas; L2 no pasted calculations; L3 no external links, manual calculation, errors or missing saved values; L4 Excel recalculation of a copy matches; L5 the Python chain matches Excel |
| Pasted calculation | A typed number equal to a calculation of other cells (e.g. a typed TTM total); it will not update |
| Period block | Workbook rows under month (or quarter) headers; new periods are written here |
| Line map | Statement line → period row, proven on every overlap month after scale and sign |
| Parameter | Typed input carried from the approved workbook: comparables, discounts, weights, cap table, waterfall terms |
| Add-in cell | Formula calling a data provider (e.g. PitchBook); frozen to its saved value in drafts, formula kept |
| Company file | `Valuations/<company_id>/company/<company_id>_company.zip`: silver data, evidence ledger, manifest |
| Office Script | `recalc-and-read.ts` v3: recalculates a file in SharePoint and returns cell values; refuses files whose name lacks `__copy` or `__draft` |
| JUDGMENT NEEDED | The only AI step: the script prints options, the agent answers in JSON, the script records the answer as an AI judgement |

## 2. Decisions (settled)
| ID | Decision |
|---|---|
| D1 | **Work back from the LP row.** Only cells upstream of LP fields are classified or written; everything else is counted, never touched. |
| D2 | **One agent, one skill, separate commands** (census, onboard, check-recalc, approve, explain; later refresh, close, backtest). The company file is the hand-off between onboarding and refresh. Connected agents are preview and are not used. |
| D3 | **Assume, record, confirm once.** Each judgement is filled automatically in this order: approved workbook → company decision → XPV pattern → best-practice default → AI judgement; each records its basis. The analyst approves once per run. Only impossible states stop a run. |
| D4 | **Everything downstream stays live.** The pipeline writes only raw inputs (statement periods, dates, FX, frozen add-in values). Every other cell keeps its formula, so analyst changes (comparables, add-backs, terms) flow through. Pasted calculations get a proposed formula restoration, applied after approval. |
| D5 | **Excel computes gold; Python checks it** (identities, formula re-computation, bounds for waterfalls). Python never re-implements a waterfall. |
| D6 | **History comes from approved workbooks.** Statements prove the line map; an approved value always wins over a later statement (the difference is listed). |
| D7 | **The analyst finishes in Excel.** The pipeline takes the draft about 90% of the way; the analyst edits anything (multiple, comparables, add-backs) and says "approved"; `close` records every change as a decision for future refreshes. The multiple is not a separate question each quarter. |
| D8 | **Approved quarters are never restated**; corrections apply from the open quarter. |
| D9 | **Layout or method change → re-onboard** from the new approved workbook (detected by fingerprint). |
| D10 | **Fund-level reporting is a separate skill** (stage 2), built on approved LP rows; disclosures and PDF reconciliation are stage 3. |
| D11 | **Names need not be anonymized.** The deny-list release check stays optional. |
| D13 | **No stored portfolio archive (11.1).** SharePoint and the knowledge sources are the record of files; each company's map, facts and approvals live in its company file; cross-company references are built on demand from workbooks found in *Valuation Workbooks*; the census is an occasional overview only. (The 11.0 register was removed: an extra step on every request, a link to maintain, and lost updates when two people ran at once.) |
| D14 | **Judgement where it helps, verification always.** The AI chooses between options (line map, field cells) and proposes calculations Python could not prove from the formula and its labelled inputs; Python keeps a proposal only if it reproduces Excel's value; the analyst approves. Numbers are never produced by the AI. |
| D16 | **Agent finds files; analyst names company and quarter.** `gather` selects files deterministically from what knowledge returns, prints exact searches for gaps, and the onboarding command; the analyst is asked only for what two search rounds could not find. |
| D15 | **Prove before approval.** Onboarding = mapping → backtest build (same-quarter, and walk-forward when the previous quarter exists) → one named approval of a proven recipe. |
| D12 | **Build map.** Onboarding traces the LP row back through every part it depends on (each entity's financials, EBITDA adjustments, pro forma, metrics, comparables, valuation, cap table / waterfall, FX, fund records, LP outputs), puts the parts in build order, and gives every input a next-quarter source. An input with no source is a gap. The refresh rebuilds every part in that order and cannot be approved while a gap remains or a required part was not rebuilt or confirmed. Roles and sources are data (`references/build_rules.json`), so a new company's structure needs wording, not code. |

## 2a. The two workflows
**Onboarding (once per company):** Mapping → Backtest build → Approval
- *Mapping:* understand the approved workbook and that quarter's statements: LP fields proven, line map by entity,
  build map, gaps, HAVE / NEED; Excel recalculates a copy.
- *Backtest build:* rebuild an already-approved quarter from statements and compare with its approved numbers (no new
  quarters). Two forms:

  | | Same-quarter build | Walk-forward build |
  |---|---|---|
  | Starts from | this quarter's approved workbook (Q1) | the previous quarter's approved workbook (Q4) |
  | Feeds in | this quarter's statements (Q1) | this quarter's statements (Q1) |
  | Compares with | the approved Q1 | the approved Q1 |
  | Proves | the mapping: rows, entities, scale, sign, nothing missing | the quarter-to-quarter move: windows roll, quarter-named sheets copied, cap table changes explained |
  | Needs | nothing extra | the previous quarter's approved workbook |

- *Approval:* one named sign-off on a recipe that has been proven.

**Generation (every quarter):** Mapping → Excel calculates → Checks → Analyst review → Approval → Close
- *Mapping:* the new statements go onto the company's map (by entity), adjustments are proposed, quarter-named sheets
  are rolled, cap table / FX / fund records are updated or confirmed.
- *Excel calculates* the draft; *checks* (ties, identities, value bridge) mark it approvable or not.
- *Analyst review* in Excel and in chat (questions, facts, corrections) → *approval* → *close* records every change for
  next quarter.

**Data rules:** the approved valuation always wins over monthly data. Monthly workbooks and statement packs given to
the census are filed for onboarding (not censused). Upload limit is 20 files per message: census in batches (the
register is additive); onboard one company at a time.

## 3. Flow
```
PHASE 1  CENSUS    all approved workbooks → one table: method, fields, blocks, findings (read-only)
         ONBOARD   approved workbook + that quarter's statements
                   → find LP fields → prove by identities → classify inputs → line map → liveness L1-L3, L5
                   → bronze saved, copy saved → RECALC copy (Office Script) → L4 → report → approve (named)
PHASE 2  REFRESH   new quarter's statements → silver adds months → draft (inputs only, restorations, add-ins frozen)
                   → RECALC draft → Excel vs Python chain, tie-outs, outliers, value bridge → notes sheet → analyst
PHASE 3  CLOSE     approved workbook → compared with draft → decisions recorded → next template
         BACKTEST  refresh of a past quarter vs its approved workbook → GOLD_MATCH / EXPLAINED → PROVEN
PHASE 4  ROLL-OUT  every company; year-end backtest; handover rehearsal
PHASE 5  FUND      approved LP rows + fund cash flows → fund summary (separate skill)
PHASE 6  REPORT    LP report / PDF reconciliation and disclosures (separate skill)
```

## 4. Environment facts (checked 6 October 2026)
- GitHub Copilot harness: generally available. Skills (`SKILL.md` + scripts) run in a Python 3.12 sandbox with no
  network; files there are temporary. Workflows and MCP servers as tools: generally available. Connected agents,
  memory and user file uploads: preview.
- Files the agent creates: 10 MB each, kept 28 days. Attachments: 16 MiB each. URL attachments must be public.
- SharePoint *Create file* accepts at most ~4 MB inline (larger files are returned as downloads).
- Office Scripts: 120-second limit, 1,600 Run-script calls per user per day, 5 MB request/response. A flow used as a
  tool must answer in 100 seconds.
- IPEV 2025 guidelines (periods from 1 April 2026): calibration at each measurement date; documented assumptions;
  AI may support the process but a human valuer makes the judgement. The design meets this through the analyst's
  sign-off and the recorded decisions.

---

## 4a. Getting files to the agent (best practice)
- **Four knowledge sources** feed the scripts (whole files are fetched into the sandbox and reused for the conversation):
  *Valuation Workbooks*, *Company Financial Statements*, *Monthly Summaries* (created by XPV), *LP_reports*. They are used
  only to fetch files, never to answer valuation questions.
- **`gather` chooses the files**, so the analyst only names the company and quarter: this company's approved workbook
  for the quarter (approved over draft, highest version), the previous quarter's, the quarter's three months of
  statements and monthly summaries, and the monthly workbooks the valuation workbook links to. It ignores other
  companies' workbooks, prints the exact search for anything missing (at most two rounds), then prints the onboarding
  command. Statements named for an entity rather than the company are kept: the line map proves or rejects them.
- **Knowledge is search, not exact lookup:** the READING / HAVE lines and the register's file hashes confirm what arrived.
  Clear file names (company, entity, period, kind) help; new files can take time to be indexed.
- **One company per conversation;** uploads (20 per conversation) only for files not in SharePoint (`add` files them).
- **Which company a file belongs to:** the user says so > the chosen valuation workbook links to it by name > its name
  resembles the company > unknown (statements: the line map decides; anything else is not filed).
- **gather only looks in its search folders** (uploads, the working folder, and where knowledge files land) and prints
  where it looked and where it found files.
- **The census is optional:** an occasional portfolio overview, never needed before onboarding.
- **Known limit:** the company file (`.zip`) is not indexed by knowledge, so approval should happen in the onboarding
  conversation; a later conversation needs its SharePoint link.

**Runbook R0 – the standard request (run first):** in a new conversation, without uploading, say "Onboard <Company B> for
Q2 2026". Correct when the GATHER / HAVE lines name the approved Q2 workbook (not a draft), the Q1 workbook, and the
quarter's statements for every entity, and the agent runs the printed THEN command without asking you for files.

## 5. Phase 0 – Deploy and clean
| Step | What to do | Correct when |
|---|---|---|
| 0.1 | In the agent, delete the v6 `valuation-pipeline` skill (it carries old test files and `~BROMIUM` stubs) | Only v10 remains |
| 0.2 | Upload `valuation-pipeline.zip` (11.1.0) **as downloaded** (do not unzip and re-zip on the laptop) | Skill shows version 10 description |
| 0.3 | Replace `valuation-generate` with the cleaned zip (stray pipeline copy and stubs removed) | — |
| 0.4 | In SharePoint, replace the Office Script with `recalc-and-read.ts` v3 (same `cells` parameter; the tool needs no change) | — |
| 0.5 | Paste `agent-instructions.txt` into the agent's Instructions | — |
| 0.5b | Knowledge: the four sources (Valuation Workbooks, Company Financial Statements, Monthly Summaries, LP_reports) with descriptions that name what each holds and how files are named; run runbook R0 | R0 passes |
| 0.5a | After the first census with build 11: copy the SharePoint link of `Valuations/_portfolio/register.json` into the instructions' *Register link* line and publish | Later runs print `REGISTER: ... updated` instead of the NOTE |
| 0.6 | Optional: switch the model to the strongest available (judgement calls now matter) | — |
| 0.7 | Say: **"Run the pipeline self-test."** | `ALL SELFTESTS: PASS (49/49)` |

## 6. Phase 1 – Census and onboarding (built)

### 6.1 Commands and printed lines
See `SKILL.md`. Exit codes: 0 done, 10 JUDGMENT NEEDED, 20 waiting for a tool step, 3 STOPPED, 1 error.

### 6.2 Runbook R1 – Census
- **Upload:** the latest approved workbook of every company (paste SharePoint links).
- **Say:** "Run a census on these workbooks."
- **Correct when:**
  1. Every workbook has a verdict: READY TO ONBOARD, REVIEW (warnings or unproven identities), BLOCKED (something would
     make the LP numbers wrong: required field missing, period mismatch, stale or missing saved values, errors of its
     own upstream) or NOT ANALYSED (the analysis could not finish, e.g. killed for memory; the other workbooks still run).
  2. *Metric window* and *period alignment* read as you expect for each company. Windows are found by their values, so
     SUM ranges, SUMIFS/OFFSET date windows and typed totals are all read correctly, and each is labelled *dynamic*
     (rolls with a date) or *fixed range* (moved by hand). Periods are conventions, not errors: `aligned`, `lagged n
     month(s)` (within 3 months, information only) or `mismatch` (longer lag, metrics ending in different months, or a
     date cell disagreeing with the file name) – a question for the analyst, never a block. `unresolved` means give the
     valuation date at onboarding (`--period-end`). Onboarding records the confirmed convention for that company.
  3. *Method* lists its components (multiple cell, metric cell, weight, period basis) and any multiple present but not
     used in EV; *unproven identities* are named, never shown as "-".
  4. Spot check: for 3 companies, confirm the EV, equity value and value to XPV cells the census JSON names.
  5. Every count states its scope (LP dependency graph, LP fields, entire workbook); add-in provider errors (e.g.
     `#NOTAUTH`) are one warning, separate from errors of the workbook's own.
- **What it tells us:** which companies have monthly vs quarterly structures, FX, add-ins, and how much clean-up each
  workbook needs. Paste the census table back to this chat to plan phase 2.

### 6.3 Runbook R2 – First company onboarding (includes the Office Script check)
- **Upload:** the company's approved workbook for one quarter plus the monthly statements of **that same quarter**.
- **Say:** "Onboard <Company> from this approved workbook and these statements."
- **The agent then:** may answer a JUDGMENT NEEDED item; saves bronze files and a `__copy`; runs the Office Script on
  the copy; runs `check-recalc`; posts the report and the onboarding report file.
- **Upload for a pro forma company:** every entity's statement pack, and (recommended) the previous quarter's approved
  workbook with `--previous` ("Onboard <Company> from this approved workbook, these statements, and last quarter's
  approved workbook").
- **Correct when:**
  0. `BUILD`: every part you would expect is listed (each entity, pro forma, adjustments, comparables, valuation, cap
     table, LP outputs) with the right sources; `TRACE: investor value` reaches every entity's financials; gaps are 0
     or ones you agree need a source; `LEARNED` (with `--previous`) shows quarter-named sheets rolled and the inputs that
     really changed (e.g. cap table).
  1. `LP FIELDS`: EV, equity value and value to XPV are `[verified]`.
  2. `LIVENESS`: L1–L3 PASS or findings you agree with; **L4 PASS** with time under 90 s; L5 all identities pass.
  3. `LINE MAP`: statement rows "matched all overlap months"; adjustment rows are not review items.
  4. `REVIEW`: a short list (target ≤ 10) where each item makes sense; ask "explain A-xxxx" for any item.
  5. Guard test (once): run the Office Script by hand on a file without `__copy` in its name → it returns `refused`.
- **Approve:** "Approve the onboarding as <name>" (add corrections, e.g. "restore the TTM formula").
  `APPROVED:` and `READINESS: ONBOARDED`.

### 6.4 Tests (synthetic, in the package)
| ID | Proves |
|---|---|
| T0.1 | Identical inputs and clock → byte-identical company file |
| T0.2 | Release check catches deny-listed terms, `~BROMIUM` folders, nested skills |
| T0.3 | Every protocol line printed is documented in `SKILL.md` |
| T1.1 | Census of a standard EV/EBITDA workbook: all required fields proven, no findings |
| T1.2 | Typed TTM total → pasted calculation with `=SUM(...)` restoration |
| T1.3 | Typed copy of value to XPV on the LP sheet → L1 finding with `=` link |
| T1.4 | TTM window ending a month early → L5 finding naming both months |
| T1.5 | Add-in cells listed; external links, manual calculation, errors → L3 |
| T1.6 | Blended method with weight cell 0.25 / 0.75 |
| T1.7 | FX: value to XPV = local value ÷ rate |
| T1.8 | Held at cost recognised |
| T1.9 | Cells feeding no LP field are never classified |
| T1.10 | Formula month headers (`=EOMONTH`) form a block |
| T1.11 | 3 overlap months, statements in thousands → matched on every month at scale 1,000 |
| T1.12 | Renamed statement line matched by its numbers |
| T1.13 | One differing month → JUDGMENT NEEDED → AI answer recorded and listed for review |
| T1.14 | Single overlap period → weaker evidence, listed |
| T1.15 | Next quarter's statements with this quarter's workbook → STOPPED, nothing saved |
| T1.16 | check-recalc PASS on the wrapped script result; report with glossary |
| T1.17 | check-recalc FAIL on a differing value, FAIL when refused, NOT RUN when unavailable |
| T1.18 | Approve needs a name, records corrections, binds to the method hash; unknown IDs rejected |
| T1.19 | Tampered company file → integrity STOP |
| T1.20 | explain prints formula and labelled precedents |
| T1.21 | Files over 4 MB are returned as downloads |
| T1.22 | Quarterly columns: flows = 3 statement months, balances = quarter end, TTM = 4 quarters |
| T1.23 | Workbook without saved values (saved by a non-calculating tool) → finding |
| T1.24 | Census: a workbook killed for memory is reported NOT ANALYSED; the others complete |
| T1.25 | Q2 file whose date cell and TTM windows say March → blocking period mismatch |
| T1.26 | Add-in cells saved with provider errors → one warning, not valuation failures |
| T1.27 | Adjusted EBITDA summed from its own monthly row → proven by formula, not "unproven" |
| T1.28 | Data sheet nothing refers to → counted, not stored |
| T1.29 | Dynamic TTM (SUMIFS on dates) found by its values, labelled dynamic |
| T1.30 | Calendar-year window 6 months behind the valuation date → described and asked, not blocked |
| T1.31 | Metrics in one EV ending in different months → warning even with a small lag |
| T1.32 | Build map: all parts traced in build order (entities → pro forma → metrics → valuation → cap table → LP), every input with a source |
| T1.33 | Pro forma: each entity's statement pack maps to that entity's rows |
| T1.34 | Previous quarter: quarter-named sheet rolled, cap-table change seen, comparables carried |
| T1.35 | An input with no source next quarter → GAP and review item |
| T1.36 | A bracketed sheet name is not mistaken for a data-provider function |
| T1.37 | Census is a report only: monthly files given with it are named and skipped, nothing else stored |
| T1.38 | `reference` on demand: structure of the workbooks found for a feature, no numbers |
| T1.39 | `add`: files classified and filed; a stated fact recorded word for word in the company file |
| T1.40 | HAVE / NEED: missing entity statements and optional previous quarter listed |
| T1.41 | AI-proposed equity bridge verified by Python; a wrong proposal rejected |
| T1.42 | A metric read from a linked workbook is reported as such |
| T1.43 | `gather` looks only in its search folders and says where it looked |
| T1.44 | `gather` treats a monthly workbook the valuation workbook links to as this company's |
| T1.45 | `gather` picks the approved workbook over a draft and the highest version, the previous quarter and the quarter's statements; ignores other companies; prints the onboarding command |
| T1.46 | `gather` with only a draft says exactly what to search for; quarter wording is flexible |

Development checks outside the package: fixture values matched an independent spreadsheet engine's recalculation;
v6's differently built test workbooks (factor multipliers, equity-level discounts, quarterly columns) were proven by
formula re-computation; a 300,000-cell workbook analysed in about 9 seconds; a 2-million-cell workbook completes
under a 1.5 GB memory cap (peak 55–590 MB) where the earlier full loading ran out of memory.

---

## 7. Phase 2 – Refresh (to build next)

### 7.1 Command
`refresh --company "<id>" --workbook "<last approved workbook>" --statements "<n>" ... [--fx <rate>] [--answers '<JSON>']`
then the printed `RECALC` and `THEN: check-draft ...` steps.

### 7.2 Steps
1. Verify the company file (manifest, ledger) and that the latest approval matches the method hash; else STOP.
2. Fingerprint the given workbook; if the layout changed since the approval → STOP: re-onboard from it.
3. Period gate: new months follow the last valuation month and complete the quarter; else STOP naming months.
4. Read statements; apply the line map (scale, sign, sum of 3 months or quarter-end for quarterly rows); a mapped
   line missing from the new pack → review item `give_value`. Approved history wins over restated statement months.
5. Adjustment rows: proposed from statement lines in the nine categories, consistent with the company's past
   add-backs; listed for the analyst; zero when nothing qualifies.
6. Write the draft `<stem>__draft.xlsx`: new period values into the matching date columns (shift rules from v9 §6
   when no column exists); valuation date; FX rate (`--fx`, else JUDGMENT/asks); add-in cells frozen (formula text
   kept in the company file); approved formula restorations applied. No other cell changes.
7. Add a notes sheet `_Agent_Notes` (what was updated, assumptions, checks, value bridge). `close` ignores it.
8. RECALC the draft, then `check-draft`: Excel-vs-Python chain (TTM from silver vs Excel's TTM cells; identities with
   the new values; every LP formula re-computed), waterfall bounds, statement tie-outs (subtotals where present),
   outliers versus trailing history (sign flips, |z| > 3), value bridge in XPV's buckets (multiple, metric, net debt,
   ownership, FX, other) using XPV's attribution convention.
9. Save the four gold files to `Valuations/<id>/<YYYY-Qn>/`: draft, run log, evidence pack, company snapshot.

### 7.2a Company conventions (learned, not imposed)
Onboarding records each company's conventions from its approved workbook and the analyst's confirmation; the refresh
follows them and flags only a change:
- **Metric period:** window length, lag behind the valuation date (e.g. TTM at the valuation month, latest available
  month, last fiscal year), and window type. *Dynamic* windows roll by themselves when the valuation date changes;
  *fixed ranges* need the period block shifted (v9 shift rules) or the range moved – chosen per company at onboarding.
- **Linked workbooks:** each external source (e.g. a detailed backup workbook) is registered as an input; the refresh
  asks for it and reads the linked values from it, or carries the last values with a note. Workbooks are not edited to
  remove links unless the analyst decides to.
- **Fiscal year end, FX source, add-back sources, cost-held status:** recorded once, re-asked only when evidence changes.
With several approved quarters of one company, the convention is taken from the pattern across them.

### 7.2b Refresh = executing the build map
The refresh walks the build map in order. For each part it applies the recorded source of every input (statements by
entity, adjustment proposals, period-end balances, cap table update or confirmation, FX, fund records, carried values),
creates the next quarter's copy of quarter-named sheets and points the dependent formulas at it, then lets Excel
recalculate. Gates before the draft can be approved:
1. every part rebuilt or explicitly confirmed (cap table, fund records, FX are never silently carried);
2. no gaps;
3. ties: each consolidated row equals the sum of its entity rows, each metric equals its window, every LP formula
   re-computes in Python, identities hold;
4. LP outputs read back and checked.
A failing gate does not discard the draft: it is saved marked NOT APPROVABLE with the failures listed, and `approve`
refuses until they pass.

### 7.3 Tests (to write first)
| ID | Proves |
|---|---|
| T2.1 | New months land in the right date columns |
| T2.2 | Typed-header block shifts left with its headers; formula headers shift values only |
| T2.3 | Template and draft differ only in input cells (plus frozen add-ins and approved restorations) |
| T2.4 | Add-in cell frozen; its formula text stored in the company file |
| T2.5 | Approved pasted-calculation restoration becomes a live formula in the draft |
| T2.6 | Missing mapped line → `give_value` review item, nothing invented |
| T2.7 | Quarter not complete / wrong quarter → STOPPED with the months |
| T2.8 | Statement restating an approved month → approved value kept, difference listed |
| T2.9 | Simulated wrong column → Python TTM ≠ Excel TTM → FAIL naming the cell |
| T2.10 | Value bridge buckets sum to the total change in value to XPV |
| T2.11 | Missing FX rate → asked once; given rate recorded with its source |
| T2.12 | Layout changed since approval → STOP: re-onboard |
| T2.13 | Draft name contains `__draft`; the original is never written |
| T2.14 | Deterministic: identical inputs give identical draft cells and run log |

### 7.4 Correct when (runbook R3: first refresh)
- Upload: the last approved workbook (link) + the new quarter's statements. Say: "Run the Q3 refresh for <Company>."
- The draft opens in Excel; every LP cell is a formula; checks PASS; the bridge explains the move; the review list
  is short (target ≤ 5); the analyst can finish in Excel.

## 8. Phase 3 – Close and prove (to build)
- **close** `--company --approved "<approved workbook>" --by "<name>"`: register as bronze; compare formulas and typed
  inputs with the draft (never bytes); each difference becomes a named decision ("analyst changed <label> from a to
  b"); approved values become silver history; fingerprint change → re-onboard next time; the approved file becomes
  the next template.
- **backtest** `--company --workbook "<approved Q>" --statements <Q+1> --compare "<approved Q+1>"`: refresh in the
  sandbox; compare gold fields; attribute each difference to a driver line and month, an analyst-changed input, or a
  method change; `GOLD_MATCH`, `GOLD_EXPLAINED`, `GOLD_MISMATCH`, `LAYOUT_CHANGED`. The comparison file can never be
  an input. Every input the analyst changed in the backtest becomes a standing "confirm this quarter" item.
- **Tests T3.1–T3.8:** close records each change; ignores `_Agent_Notes`; bytes-only changes are not differences;
  layout change detected; backtest match; explained (changed multiple); mismatch pinned to line and month;
  comparison-as-input guard.
- **Correct when (R4):** onboard Q1 → refresh Q2 → backtest against approved Q2 → `GOLD_MATCH` or `GOLD_EXPLAINED`
  → readiness `PROVEN`.

## 9. Phase 4 – Roll-out and handover
- Census findings fixed or accepted for every company; each company onboarded (R2) and proven (R4).
- Cost-held and realized companies: handled per the answer to question Q3 below.
- One backtest across a fiscal year-end.
- Handover pack: `SKILL.md`, this plan, `MAINTAINERS.md`, a one-page user guide (prompts below).
- Rehearsal: an analyst onboards and refreshes a company alone; everything they had to ask becomes the backlog.

## 10. Phase 5 – Fund roll-up (separate skill, outline)
Inputs: approved LP rows (one per company per quarter) + fund cash flows (contributions, distributions, dates).
Outputs: fund summary, gross MOIC / IRR / DPI / RVPI / TVPI, totals reconciled to the approved rows. Net returns,
fees and carry stay with fund accounting unless XPV computes them in-house.

## 11. Phase 6 – Report reconciliation and disclosures (outline)
Every LP report figure traced to an approved LP row; disclosure items (method changes, comparable changes, cost holds,
escrow discounts) generated from the decision log.

---

## 12. Prompts (what users say)
| Goal | Say | Upload / paste |
|---|---|---|
| Add information | "Here are Company B's Q2 statements" / "Company D bought Gamma; Gamma's TTM EBITDA is 2.1m" | files, or the fact in words |
| See how others did it | "How have other companies structured an acquisition?" | — |
| What's on file / missing | "What do we have for Company B?" | — |
| Health check | "Run the pipeline self-test." | — |
| See what the workbooks look like | "Run a census on these workbooks." | approved workbooks |
| Set up a company | "Onboard <Company> for Q2 2026." | nothing (files come from knowledge) |
| Ask about an item | "Explain A-xxxxxxxx for <company>." / "Explain enterprise_value for <company>." | — |
| Approve | "Approve the onboarding of <company> as <name>." (+ corrections in plain words) | — |
| (Phase 2) Quarterly update | "Run the Q3 refresh for <Company>." | last approved workbook link + new statements |
| (Phase 3) Record approval | "<Company> Q3 is approved; here is the final workbook." | final workbook link |

## 13. Open questions (defaults apply until answered)
| # | Question | Default |
|---|---|---|
| Q1 | Where does the period-end FX rate come from, and what convention (divide by CAD/USD, period-end)? | Asked each refresh; recorded with its source |
| Q2 | Attribution convention: sequential order or isolated effects plus an interaction term? | Sequential: multiple, metric, net debt, ownership, FX, other |
| Q3 | Do cost-held and realized companies go through the agent? | Yes, as trivial drafts (no statements needed) |
| Q4 | Invested capital, proceeds, cash-flow dates: fund summary workbook or company workbook? | Company workbook values, confirmed against fund records each quarter |
| Q5 | Who may approve; must the approver differ from the person who ran it? | Any named analyst; warning when the same |
| Q6 | Materiality thresholds | `references/materiality_defaults.json`, labelled unapproved |

## 14. Troubleshooting
| You see | Do |
|---|---|
| `STOPPED: period gate` | Upload the statements of the workbook's own quarter |
| `L4 NOT RUN` / Run script failed | Check the Excel connection (Set up connection, Retry); onboarding can still be approved |
| `L4 FAIL` | The saved values were stale or the copy differs: open the original in Excel, recalculate, save, re-onboard |
| `no_saved_values` finding | The workbook was saved by a tool that does not calculate; open and save it in Excel |
| `integrity` STOP | Use the company file saved in SharePoint; never edit the zip |
| Many review items | Paste the census row here; the workbook probably needs a label added to `references/lp_fields.json` |
