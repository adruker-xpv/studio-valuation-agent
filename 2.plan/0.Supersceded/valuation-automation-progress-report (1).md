# Valuation Automation – End-to-End Progress Log (15 Sept – 8 Oct 2026)

**Mandate:** make XPV's quarterly portfolio valuations faster and auditable – analysts give the system a company's monthly
financials and get a draft valuation workbook they approve, feeding the LP report – and leave something non-technical staff
(about 7 analysts, about 10 companies) can run after December.
**Status in one line:** the code that reads and checks workbooks works on test workbooks and in the agent; whether it picks
the right cells on real workbooks is not yet known – that is the next measurement. Quarterly generation is on hold on purpose.

## Glossary
| Term | Meaning |
|---|---|
| LP report | XPV's quarterly report to investors (limited partners); the end product every number must trace to |
| EV / EBITDA / TTM | Enterprise value; earnings before interest, tax, depreciation and amortization; trailing twelve months |
| Copilot Studio agent | The Microsoft chat agent analysts will use; it runs packaged Python "skills" in a sandbox (GitHub Copilot harness) |
| Office Script | A script that runs inside Excel for the web (used for recalculation and exports) |
| Chain | The calculation path: monthly figures → TTM adjusted EBITDA → multiple → EV → equity → XPV's share → LP report |
| Synthetic workbook | A made-up test workbook that reproduces a real structure without real data |

---

## Timeline at a glance
| Dates | Phase | Outcome |
|---|---|---|
| 15–17 Sept | Learn the domain, scope the project | Plan cut from ~19–22 weeks of work to fit the 12 available |
| 17–22 Sept | Architecture and governance | "AI prepares, humans decide, Python calculates"; licensing aligned with IT |
| ~19–24 Sept | Automate the Excel process step by step (Microsoft-native) | Worked mechanically; slow, detailed, brittle; files could not reach the sandbox |
| 23–25 Sept | Let the AI agent do the work | Stalled: inconsistent self-written code, unreliable numbers, credit burn |
| 25–30 Sept | Code-first pipeline (AI only for judgement) | Engine works on test files; real files exposed and fixed several serious bugs |
| 1–5 Oct | Simplify and cut cost; live Excel recalculation | Instructions cut ~900 → ~150 words; Excel recalculates from the agent |
| 6 Oct | v7 → v9 | v7 (92 tests) failed on real data; redesigned around the approved workbook |
| 6–7 Oct | Builds 11.0 – 11.3 | LP-backed lineage, auto file gathering; a second real failure; strict data boundary |
| 7–8 Oct | Builds 11.4 – 11.7: measure before building more | Reading proven on a real workbook; meaning failed; chain-first redesign |

---

## 1. Learn the domain and scope it (15–17 Sept)
- Learned the valuation chain from scratch: EV and EBITDA normalisation, the fair-value hierarchy (IFRS 13 / ASC 820),
  IPEV guidelines, comparables and discounts, the EV-to-equity bridge, waterfalls, MOIC / IRR / TVPI.
- Prepared and ran the stakeholder interview with the person who does the reporting manually; asked for real submission
  files and historical workbooks, which became the acceptance test.
- Checked constraints early: PitchBook has no API on XPV's plan (its Excel plug-in is the route), so comparables carry
  forward and the analyst approves them.
- Reviewed the first plan twice: the scope needed ~19–22 weeks against 12 → cut the MVP to intake, normalisation and
  deterministic metrics; lineage and audit built in from the start.

## 2. Architecture and governance (17–22 Sept)
- Principle set and kept since: **AI prepares, humans decide, Python calculates.** Agents never author valuation numbers.
- Design: exception-driven – last quarter's workbook plus new financials produce this quarter's draft; only exceptions go to
  a person; a decision ledger is both the audit trail and next quarter's memory.
- Governance: raised tool licensing with IT (an organisation-governed Copilot seat rather than a personal one) and kept real
  portfolio data out of non-approved tools.
- Requested raw monthly packages and the matching approved workbooks (not consolidated copies) to test real flows.

## 3. First build – automate the Excel process step by step (~19–24 Sept)
**Built:** a Power Automate flow that registers and inspects incoming workbooks with Office Scripts (file-type checks,
run logging, an inspection script); then Copilot Studio modules – a file profiler (reads real workbooks including very
hidden sheets, flags file-name versus content conflicts), a file register, a note builder.
**What happened:** it worked mechanically but copied every manual step – slow and detail-heavy. Days went into platform
quirks (the file trigger returning binary without metadata, typed script outputs, date escapes). The note builder ran slow,
oversized, and saved a file path instead of its content.
**The wall:** files fetched through the OneDrive connector reach the agent as **text, not as workbooks** the code can open
(confirmed with a diagnostic probe); connector downloads also corrupt Office files.
**Adapted:** files enter as chat attachments (later, knowledge sources); stop mirroring manual steps.

## 4. Second attempt – let the AI agent do the work (23–25 Sept)
**Built:** agent-written company notes and confidence scores; then two agents – *company set-up* (reads the last approved
workbook, finds every typed input, matches it to a statement line, produces a checked company pack a person approves) and
*quarterly roll-forward* (recalculates mapped inputs and writes only those cells).
**Why it stuck:**
- The agent's own confidence scores were assigned "by feel"; cell references came back as free text.
- When the agent wrote and ran its own code, results varied run to run and broken cells (#VALUE!-type errors) crept in.
- A language model cannot be trusted with exact arithmetic or large exact file contents; moving between steps burned
  expensive credits on reasoning.
- The first real pilot showed the statement reader could not handle Month / QTD / YTD / LTM column layouts, and matching by
  value alone was too noisy on large workbooks.
**Adapted:** evidence-based checks instead of self-reported confidence; **code does everything exact, AI only makes isolated
judgement calls, a named person approves.**

## 5. Code-first pipeline (25–30 Sept)
**Built:** one `valuation-pipeline` skill (plus `valuation-generate` for companies with no workbook) with one orchestrating
command:
- traces each workbook back from its key outputs (one pilot: ~930 referenced cells narrowed to 235 that matter);
- learns *executable* input rules by reproducing workbook values from statements (month-end value, 3/12-month sums,
  year-to-date differences, with scale and sign);
- replays a past quarter, backtests an unseen one against the analyst's real workbook, and drafts the next.
**Real-file bugs found and fixed:** re-saving with the Python library corrupted links and drawings ("repaired records") → now
edits only target cells inside the file's XML; small whole numbers (share counts, terms) matched statements by coincidence →
exact matching below 1,000 and sheet context; a countdown field was carried forward instead of decremented → flagged;
unexplained differences were asserted in prose → now traced deterministically.
**Platform facts established:** the sandbox cannot recalculate Excel (Excel itself must); SharePoint "Create file" overwrites
in place; "Get file content" returns text; ~4 MB per file.

## 6. Simplify and cut cost; live recalculation (1–5 Oct)
- Rebuilt against a 20-point simplification spec: instructions ~900 → ~150 words; key outputs chosen by deterministic rules;
  AI asked at most once per onboarding; a per-company decisions log (who, when, exact words) replaces a heavier approval gate.
- **Office Script recalc-and-read**, run from the agent, recalculates a saved workbook in Excel and returns the cells needed –
  tested live, removing the manual desktop-Excel step.
- Proven: the agent cannot fetch SharePoint files by path → inputs by upload or knowledge source, matched by name.

## 7. v7 → v9 (6 Oct)
- **v7** (92 synthetic tests): statement coverage checks, frozen data-provider cells (PitchBook shows #NOTAUTH until
  connected), bounded add-back search, prior-period roll-forward, an append-only archive (never delete history).
- Reviewed a third-party plan: it would have **saved over approved workbooks** (the Office Script saves the file it runs on) →
  corrected plan v8.
- **v7 failed on real data**: it tried to *prove* already-approved history from three months of statements, flagging ~260
  cells and period mismatches.
- **v9 redesign:** raw files immutable; history inherited from the approved workbook; results checked on a few headline
  numbers (EV, adjusted EBITDA, multiple, value to XPV).

## 8. Builds 11.0 – 11.3 (6–7 Oct)
- LP fields traced to source formulas and proven by recomputed identities (EV, equity, value to XPV, MOIC); a build map of
  every part (entity financials, pro forma, adjustments, cap table, comparables); statements matched to rows across all
  overlapping months; a release check so confidential names never ship in a package.
- **Gather:** an analyst says "Onboard Company X for Q2 2026" and the agent finds the files in four knowledge sources.
- Removed a portfolio-wide register when it proved to be overhead (simplicity over completeness).
- **Second real run:** a 15-month period misalignment that still passed every arithmetic check; typed LP values; Excel
  recalculation timing out on workbooks with data-provider add-ins and external links, worsened by the agent retrying →
  automatic skip, Office Script v4, a "run once, never retry" rule.
- **Data boundary made strict:** real files never leave XPV's environment; building moved to synthetic workbooks; real tests
  return count-only summary lines.
- 11.3: period checked first, multiples traced through formulas, staged Excel diagnostics, decisions required per exception
  (76 tests).

## 9. Measure before building more – builds 11.4 – 11.7 (7–8 Oct)
- Scope narrowed on purpose: before any more automation, **prove the system reads an approved workbook correctly**.
- **11.4–11.5:** a read-only discovery program and a separate benchmark that never shares its logic; every formula carries a
  status so nothing is silently skipped; clear stop messages for unreadable files (.xls, password, .xlsb, damaged); rules
  kept as versioned data; consistency checks reported as "consistency, not truth".
- **11.6:** Excel itself becomes the answer key – an Office Script exports every cell, the program exports the same format,
  the two are diffed; a 20-minute analyst form (it catches "label cell instead of number"); a one-command demo.
- **11.6.1:** tests that passed locally failed inside the agent (files written to the wrong folder) → fixed, and the release
  check now mirrors the agent exactly.
- **First real workbook through the new system:** reading worked (615 formulas, 592 fully interpreted, none disagreeing
  with Excel); **meaning failed** – a comparables summary taken as EV, a count as the multiple, an XPV-derived cell as equity.
- **11.7:** find the whole chain first and name cells by their place in it; start from the value reported in the fund
  valuation workbook and work back; reject rivals by fixed rules with reasons; "review required" rather than guess. The real
  run's failures were rebuilt in test workbooks: the old method fell for every decoy, the new one does not (49 tests).

---

## Barriers and workarounds
| Barrier (when found) | Workaround |
|---|---|
| OneDrive / connector files arrive as text, Office files corrupted (Sept) | Chat uploads, then knowledge sources; files matched by name; non-workbooks refused with a clear message |
| Sandbox cannot save or export files (Sept) | Code writes files and prints exact SharePoint "Create file" steps |
| Agent cannot fetch SharePoint files by path (Oct) | Inputs by upload, pasted link or knowledge source |
| 20 attachments per chat (Oct) | Knowledge sources supply workbooks and statements; analysts upload one form |
| Sandbox cannot recalculate Excel (Sept) | Office Script recalculates in Excel itself, run from the agent |
| Excel Online time limits (60 s tool / 120 s script) (Oct) | Skip rules, staged diagnostics, an export script that resumes |
| Agent-written code inconsistent, broken cells (Sept) | All logic in a packaged, tested skill; the agent only runs fixed commands |
| Python library re-saving corrupted workbooks (Sept) | Edit only target cells in the file's XML |
| Expensive harness credits (Oct) | One command per job, short instructions, AI only where judgement is needed |
| Confidential data (throughout) | Synthetic workbooks for building; real results as count-only lines |
| Publishing blocked by data policy (Oct) | Testing in the Preview pane (admin item) |

## Course corrections that shaped it
- Cut scope early to fit 12 weeks; then cut again (register removed, quarterly generation paused) when complexity outran value.
- Rejected "prove everything from statements" after real data showed it fails; trusted the approved workbook instead.
- Insisted flexibility for company conventions over rigid rules, and "review required" over confident guesses.
- Moved from "does it look right" to "can it prove the chain", and from end-to-end demos to measured checks.

## Where it stands – honestly
- **Works functionally:** reading, tracing and checking pass their tests, including inside the agent; reading has been
  confirmed on one real workbook.
- **Not yet known:** whether it picks the right cells on real workbooks. That is settled only when the analyst-judged
  comparison runs on several real workbooks.
- **Deliberately not started:** quarterly generation, until reading is proven.

## Next
1. Re-run the real workbook with 11.7 and its fund valuation workbook; then the Excel comparison and the analyst form.
2. Two to four more, structurally different workbooks (one kept aside, never tuned on).
3. Only then: quarterly generation, using the same proof layer as its safety check.
