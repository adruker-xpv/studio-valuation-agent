# XPV Valuation Automation — Studio Build Plan

_Draft 4, October 28, 2026. Owner until December 18, 2026: Aria (AI Intern). Replaces Draft 3 (October 16)._

This is one of five working files:

| File | Holds |
|---|---|
| **Studio Build Plan** (this file) | Why we're building it, what we build and when |
| **System Spec** | How the system must behave |
| **Log** | Questions, decisions and run results |
| **AI Development Log** | What the AI and the guardrails did well or badly in real runs |
| **Run Guide** | Step-by-step instructions for whoever runs the system |

Archived: Scope, MVP Build Plan, Project Summary, Quarterly Process Flow (one-off for Jerome), Onboarding Expansion / Polish Phase (closed October 28), OceanSight Onboarding End-to-End Test (replaced by the Run Guide).

## North star

**Every quarter, the analyst gets a new valuation workbook in which every mechanical number is exactly right and shows where it came from. The analyst only decides what is new, unclear or a judgment call. Every approval is made by a person.**

**Why it matters, in order:**

- **Exactness:** the figures go to investors.
- **Clear inputs:** the analyst trusts a workbook when its inputs are easy to check.
- **Time:** less mechanical work, and the process scales as the portfolio grows.
- **Continuity:** it runs from a guide, not one person's memory.

**Goal by December 18:**

- Four Fund III companies have Q3 rebuilt by the system as a backtest, at track changes stage, with 0 wrong let through and every mechanical number matching the analyst's real Q3 workbook.
- The system is ready for Q4 in January, the first live quarter, run by the new owner.

**Today's baseline** (still being confirmed by Jerome, Q-01/Q-02):

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
| Checking code | Confirms every AI claim, sorts items, reads the review, writes memory, types confirmed numbers, checks the finished workbook | Decides what a number means |
| Analyst | Chooses the release stage, answers decisions, approves items, signs off every workbook | Re-checks passed items (spot checks only) |
| Future interns | Start runs, supply files, follow the Run Guide | Change agents or code without running the tests |

**In and out of scope:** unchanged from Draft 3 (Microsoft 365 only; judgment calls, AI typing into workbooks, Azure, workbook redesigns and companies with no workbook yet are out for now).

**After December 18:** Phase A onboarding a new company, Phase B comparables (PitchBook), Phase C change summary to investor update (unchanged).

## 1. Where we are (October 28, 2026)

**Onboarding is working end to end and is frozen except for defects. Next phase: quarterly workbook generation (Phase 6).**

| Milestone | Result |
|---|---|
| Studio baseline (Oct 15) | 10/10 core answers on both baseline companies, 0 wrong let through |
| Extractor build | 13.2.6, checkpointed and resumable, eight stages in two passes (A: 1–3, B: 4–8) |
| Review guardrails | Review reader refused invalid decisions three times (OceanSight once, Opus twice). Nothing bad reached memory |
| First company memory | Opus Q1 2026 r6 review accepted: 23 approved, 4 corrected, 0 rejected, 2 undecided. Memory created with 15 entries, coherence OK |
| First hand-off | Opus Q1 r6 hand-off built, status `ready_with_unresolved` (1 pending decision: add-backs) |
| Memory reuse proven | Opus Q1 r7 fresh run: 14 items reused, 1 pending carried, 0 reopened, 1 new decision, 3 new memory candidates. VERIFIED, 0 contradicted |
| Memory catching AI error | Memory flagged the AI's "value to XPV" cell as a copy; the extractor corrected itself to the source cell |

**Opus Q1 2026 chain (verified, r7):** TTM adjusted EBITDA $1,952,037.26 × 13.295142x = EV $25,952,612.37; + cash $422,159.65, debt $0 = equity $26,374,772.02; waterfall gives XPV $24,723,978.88, typed as $24,723,979 in Fund III.

**Known open items:**

| Item | Severity | Handling |
|---|---|---|
| Memory loaded at stage 6, not stage 1 (caused a stage 3 revision after stage 8) | Medium | Fix in first generation build |
| One proposal skipped as "unclear" without being flagged (proposals 13 → 12) | Low–medium | Fix in first generation build |
| Uploads improvised (base64 printing, memory retyped from context, deferred checkpoint uploads) | Highest risk | Fix in first generation build; urgent if any hash or size mismatch |
| Harness mechanics visible in traces (Polish #2) | UX | Carry into generation build |
| Add-backs approval ($2,875,964 TTM) | Analyst | Pending; needs investment-team or accounting sign-off (Q-22) |
| LP report ownership cell links to the Dec 2025 cap table | Analyst | r7 review decision (Q-23) |

## 2. What we reuse

| Existing piece | Used for |
|---|---|
| Extractor 13.2.6, all eight stages | Learning a company; the extraction side of each quarterly run |
| verify.py, reconcile.py | Evidence checks |
| review_xlsx 13.2.6 and the review reader | Decision workbook and its validation |
| memory.py | Writing and checking company memory |
| Generation hand-off file | Input contract for generation |
| Test bench 13.2.2 (frozen) and Gold keys | Grading against answer keys |
| write_approved_values.ts | All typing into workbooks |
| check_outputs.ts | Checking the typed workbook against last quarter |

## 3. Rules for every change

- **Universal agents.** No company names, cells or rules in agents, skills or instructions.
- **Answer keys only measure.**
- **AI proposes; code checks and types; a person approves.**
- **Confidence is decided by code, never by the AI.**
- **No fitting to one company.**
- **Regression check after every change.**
- **Exact matching by default.** Rounding only where declared.
- **Files are identified by fingerprint**, not by file name.
- **New:** memory is read before stage 1 whenever it exists.
- **New:** files are moved only by the approved upload method (System Spec §10); never printed as text or retyped.

## 4. Phases

| Phase | Status |
|---|---|
| 0 — Lock the baseline | Done |
| 1 — Remove the reviewer from the flow | Done |
| 2 — Test bench 13.2 | Done (13.2.2 frozen) |
| 3 — Prove it generalizes (third company, 3 runs each) | **Open** — third company not yet chosen (Q-16) |
| 4 — Fewer, better questions | Done for onboarding (deduplicated decisions; 4 decisions on Opus Q1) |
| 5 — Company memory and onboarding | **Done** — memory created (r6) and reused (r7) |
| Polish phase (P0/P1 items) | **Closed Oct 28.** Open remainder moved to Phase 6 entry items |
| 6 — Quarterly mode and workbook builder | **Next** |
| 7 — Test B: Q3 backtest | Not started |
| 8 — Handover | Not started; Run Guide drafted |

### Phase 6 — Quarterly mode and workbook builder (Oct 29–Nov 27; hardest part)

**Entry items (first generation build, one regression):**

1. Load memory before stage 1.
2. Every candidate becomes a proposal or an open question; nothing is dropped silently.
3. One approved upload method with size and hash checks.
4. Keep harness mechanics out of normal responses.

**Regression for the entry items:** one fresh Opus Q1 r8 extraction (Pass A + B) plus review. Pass if stage 3 is never reopened, proposals are 13 or the missing one is an open question, no base64 or retyped files appear in the trace, results stay VERIFIED with 0 contradicted, and the chain values match r7.

**Inputs:** the generation hand-off file, company memory, last quarter's approved valuation workbook, and the new quarter's monthly files.

**Order of work:**

- Start of run: release stage and standard questions; pending memory decisions shown first.
- Workbook version check against the saved fingerprint.
- Past-period columns refreshed, with revisions flagged.
- The AI proposes each change; code checks, sorts and applies it by stage, typing with write_approved_values.ts and adding a source note.
- Stored cell locations are validated semantically before writing; moved items are rediscovered, never blindly overwritten.
- Recalculate; run check_outputs.ts.
- Output: new workbook, change log, verdict in the file name.

**Test A — invented two-quarter package:** unchanged from Draft 3, plus one case: _a pending memory decision is shown to the analyst and blocks auto-apply of the items it affects._

**First real target:** Opus Q1 → Q2 2026. The Fund III June 30 summary shows a Q2 Opus value of $35,099,879; the Q2 LP report it came from has not been supplied yet.

**Fallback:** checked numbers plus a list of changes for the analyst.

**Done when:** Test A gives every expected result.

### Phase 7 — Test B (Nov 23–Dec 4) and Phase 8 — Handover (Dec 7–18)

Unchanged from Draft 3. The Run Guide is the start of the handover document.

## 5. Scorecard (every company, every run — record in the Log)

Unchanged, plus:

| Measure | Target |
|---|---|
| Memory items reused on a repeat run | Rising; confirmed items never re-asked |
| Pending decisions carried forward | All |
| Upload integrity (size and hash) | All match |

## 6. After December 18

Unchanged from Draft 3. Added to "saved for later": quality metrics for analyst-question reduction across memory-enabled runs; debug-only trace of checkpoint details.
