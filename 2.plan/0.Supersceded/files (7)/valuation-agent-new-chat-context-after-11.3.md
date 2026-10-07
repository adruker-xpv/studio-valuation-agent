# Context for a new chat – XPV valuation agent after build 11.3 (as of 7 October 2026)

**Attach:** this file, `valuation-pipeline.zip` (build 11.3, code baseline), `valuation-agent-build-11.3-guide.md`
(setup / tests / running), `valuation-build-plan-v11.1.md` (design reference), `agent-instructions.txt` (11.3),
`recalc-and-read.ts` (v5), and the sanitised `VERIFY:` / `VERIFICATION:` lines from the agent. Then say what you want next.

## Glossary
| Term | Meaning |
|---|---|
| Limited partner (LP) report | XPV's quarterly investor report; everything works back from each company's LP numbers |
| Enterprise value (EV) / trailing twelve months (TTM) | EV = selected multiple × metric (or a blend); TTM = 12 months ending at the valuation month |
| Work package (WP) | One of the nine build 11.3 packages (WP1 periods … WP9 docs) |
| Dependency role | What a cell is to the LP numbers, each with its own period rule (`periods.RULES`) |
| Exception | A finding needing its own explicit decision before approval (`pipeline.KIND_CLASS`, `OPTIONS`) |
| Answer key / sanitised diagnostics | Private expected cells for one company and quarter / `VERIFY:` lines built from a fixed vocabulary |

## Clearance boundary (binding, unchanged)
Claude never receives real workbooks, statements, company names, numbers, paths or contents. Build with synthetic
fixtures (`tests/fixtures.factory_workbook` and friends); real files are tested only in the agent by `verify` against a
private answer key; only `VERIFY:` lines come back. No production-readiness claim until the synthetic suite and an
authorised verify run both pass.

## State after build 11.3 (package 11.3.0)
- **76 synthetic tests pass** (51 regression + 25 new, T1.49–T1.73 tagged by WP), also as a non-root user with a
  read-only skill folder and `TMPDIR=/app/workspace`. Office Script v5 is type-checked against a stub and run on a mock
  workbook only. Not yet deployed; real verify run not yet done.
- **New modules:** `periods.py` (cell period and column role, request anchoring, role checks), `ftree.py` (EV formula tree,
  multiple provenance). **New commands:** `verify --key`, `attest`. **New options:** onboard `--cells`, `--entities`,
  `--said`, `--excel-diagnostic`; check-recalc `--stage`; approve `--decisions`. **New printed lines:** `PERIODS:`,
  `EVIDENCE:`, `EXCEPTIONS:`, `APPROVAL REFUSED:`, `VERIFICATION:`, `VERIFY:`, `ATTESTED:`.
- **Real-run symptoms reproduced synthetically on 11.2** (still hypotheses for the real file): older period column chosen
  (identities pass); a peer's row mapped as the selected multiple. Two silent-drop paths in gather found and fixed.

## Decisions made in 11.3 (keep unless changed by Aria)
- Budget / Variance / prior-year / YTD columns are always set aside; other periods are set aside when a date is requested.
- A field with no candidate of the requested period keeps its candidates, flagged `wrong_period` (reported, never hidden).
- EV is traced through its own formula first; the numeric search is a fallback restricted to EV's precedents, excluding
  comparables, and flagged `method_untraced`.
- Every period conflict needs an explicit decision (`small_lag_needs_decision = true`, configurable).
- Ambiguous statement entity (file name vs heading in rows 1–3) is blocked; `--entities` resolves it. Conflicting files
  without a revision marker are blocked; revised / final / higher version wins.
- Excel: the 11.2 automatic skip is kept (add-ins, linked workbooks, very large files), so such companies always carry
  an `excel_not_verified` exception (attest or `accept_python_checks_only`). Staged diagnostic above 20,000 formulas or
  2 MB, or on request.
- A pasted calculation or typed LP value is an exception (`restore_formula` / `accepted`); T1.18 updated accordingly.

## Next
1. Deploy 11.3 in Preview; run guide tests T1–T6; bring back only `VERIFY:` lines and the `VERIFICATION:` line.
2. Fix whatever the verify run shows (synthetic fixture first, then the code).
3. Then build 12: backtest build, quarterly generation (refresh), close – reading `periods.period_conventions` and
   `decisions` from the company file.

## Lessons to keep
Don't state causes without a test; report observed evidence and hypotheses separately. Internal consistency does not
prove semantic correctness. Every new printed prefix goes into `PREFIXES` and `SKILL.md` (T0.3). Test in the agent-like
layout before shipping. Patch scripts saved to files survive a failed edit; keep doing that.
