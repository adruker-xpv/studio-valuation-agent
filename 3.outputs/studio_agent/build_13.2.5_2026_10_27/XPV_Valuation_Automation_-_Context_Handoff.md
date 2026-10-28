# XPV Valuation Automation — Context Handoff

*October 2026. Paste or attach this at the start of a new chat. Working docs: Studio Build Plan, System Spec, Log (D-11: three working files only; Markdown).*

## Legend

| Term | Meaning |
|---|---|
| Extractor | Copilot Studio agent `valuation-extractor`: reads a company's workbooks, maps how its value is built, proposes next quarter's changes |
| Test bench | Copilot Studio agent `valuation-test-bench`, version 13.2.2, **frozen**. Grades runs against answer keys (Gold keys). Development only; never feeds production |
| Reviewer | Blind reviewer agent. On the shelf, outside the main flow (D-02) |
| Checking code | Python scripts in the extractor skill that re-open workbooks and confirm every AI claim; only code types or writes memory |
| Stages 1–8 | 1 inventory, 2 roles, 3 chain, 4 upstream, 5 downstream, 6 questions, 7 proposals (code builds `proposed_changes.json`), 8 validation (`verify.py --final`) |
| Review workbook | `Review.xlsx`: Approve / Correct / Reject per proposed change, unresolved decision and memory candidate. Blank = not decided, never approval |
| Company memory | One file per company: only person-confirmed **facts** (where numbers live, revisions) and **assumptions** (which file wins, rules, the multiple, answered decisions), each with period, source, who confirmed, what it replaced. Append-only; latest confirmed wins |
| Pending decision | A review question left blank. Kept apart from memory, listed at the start of every run, blocks every change it touches (all changes if its cells can't be found) until answered or rejected. Never answered from history |
| TTM | Trailing twelve months |
| Run id / contract name | `<Company>_<YYYY>_<Qn>[_rN]` / a generated file's SharePoint name, `<run id>_<artifact>` (code derives both; checkpoints keep plain names; source workbooks keep any name) |
| Run manifest | `run_manifest.json`, written by code: run id, period, folders, every source by original name + fingerprints + discovered role, every generated file's SHA-256 |
| Source lock | The workbooks given for a run differ from the ones it started with (contents changed, file added or missing): the run stops; fresh onboarding in a new run folder and a new Gold baseline |
| Contradiction gate | Before memory is written: a concept confirmed with two different values, or two items code cannot tell apart, stops; nothing of it is written or handed on; it returns as a pending decision |

## Ground rules (System Spec §1)

Every approval is made by a person. AI never types into a workbook. No company names, cells or values in agents/code. Answer keys only measure. Exact matching (rounding only where declared). Data stays in XPV Microsoft 365; only sanitized statuses and counts leave it. The multiple is always confirmed.

## Current builds

| Item | Version | Notes |
|---|---|---|
| Extractor skill `xpv-onboarding-extractor` | 13.2.4 | 13.2.4: a review is read and written to memory only against the exact proposals snapshot saved when it was built (`review/proposals_<fingerprint>.json`, fingerprint in the review's hidden _meta); missing snapshot = refused, never rebuilt; 19/19 round-trip tests. 13.2.3: 13.2.2 plus: contradiction gate (`concepts.py`), coherence check on memory, source-set fingerprint on memory entries, source lock, run manifest and contract names (`run_manifest.py`), run identity checks on reviews and fetched files; older runs and plain names still read. New suite 67/67; bench suite with 13.2.3 scripts swapped in: same pass/fail set as 13.2.2 (340/353, the 13 known stage-8 differences). The 127 older extractor tests still to rerun |
| Playbook skill `xpv-valuation-playbook` | 13.2.3 | One paragraph added: one confirmed state per concept; identity is semantic (as-of date, workbook role) |
| Agent instructions | 13.2.4 | Never rebuild proposals when reading a review; report only accepted/refused, memory result, pending, file locations. 13.2.3: Company + Period prompts; code names everything; post STOPPED lines unchanged; code fence removed |
| Copilot Studio "Create file" tool | Folder Path = dynamically filled by AI (was hard-wired to the Valuations root) | |
| Test bench | 13.2.2 frozen | Grades the new extraction format identically. Reopen only for a reproducible grading/safety error or a false verified item |

## Results so far (sanitized)

| Run | Result |
|---|---|
| Synthetic smoke test, stages 1–8 | All expected answers, VERIFIED, 0 contradicted, revision recorded with both values |
| OceanSight 2026 Q2, stages 1–8 + grading | 10/10 core, 0 wrong, 0 omitted, 0 false claims, VERIFIED, source integrity 5/5 |
| Opus 2026 Q1, stages 1–8 + grading | 10/10 core, 0 wrong, 0 omitted, 0 false claims, VERIFIED, source integrity 6/6 (Log rows say Q2 — correct to Q1) |
| First real review → memory (13.2) | Refused safely, nothing written; four review-workbook problems fixed in 13.2.1 |

Backlog (not blockers): answer-key matching details for unscored items; equivalent period anchors in grading; fewer duplicate decisions.

## SharePoint layout (locked)

Site: AIInterns-AriaDruker, library `Shared Documents/Valuations/`. Pattern `<Company>/<YYYY>/<Qn>/`; a repeat run uses `<Qn>_r2/`.

```text
0.SS/                                          staging/archive, untouched
1.company_background_data/<Company>/<YYYY>/<Qn>/   inputs as received
1.company_background_data/_shared/<YYYY>/<Qn>/     fund valuation summary (one per quarter)
2.extractor-outputs/<Company>/<YYYY>/<Qn>/         run folder: extraction.json, proposed_changes.json,
                                                   verification.json, notes.md, Review.xlsx,
                                                   review_decisions.json, approved_changes.json,
                                                   checkpoints/ (01_sources.json ... 08_validation.json, .rN revisions)
3.test_bench_outputs/<Company>/<YYYY>/<Qn>/        <Company>_<YYYY>_<Qn>_grading_report.json
4.human_review/<Company>/<YYYY>/<Qn>/              Review.completed.xlsx (the person's copy)
5.company_memory/                                  <Company>.memory.json (one per company)
```

Company keys in use: `OceanSight`, `Opus` (code checks the form and case, not a list). From 13.2.3 generated files are saved as `<run id>_<artifact>` (e.g. `OceanSight_2026_Q2_r2_extraction.json`); the person's copy is `4.human_review/<Company>/<YYYY>/<Qn>[_rN]/<run id>_Review.completed.xlsx`. Runs from 13.2.2 keep plain names and still resume.

## Prompts (13.2.3: Company + Period, plus Run folder for RESUME/REVIEW; attach every .xlsx — the SharePoint file tool breaks binary files)

```
ONBOARDING EXTRACTION            (pass A: stages 1-3; then ONBOARDING RESUME for stages 4-8)
Company: OceanSight
Period: 2026 Q2
```
```
ONBOARDING RESUME
Company: OceanSight
Period: 2026 Q2
Run folder: /Shared Documents/Valuations/2.extractor-outputs/OceanSight/2026/Q2_rN
[MEMORY: /Shared Documents/Valuations/5.company_memory/OceanSight.memory.json]
```
13.2.2 prompts, kept for older runs:

Fresh review workbook:
```
ONBOARDING REVIEW
Build a fresh review workbook
Run folder: /Shared Documents/Valuations/2.extractor-outputs/<Company>/<YYYY>/<Qn>
Workbooks: <every input file of that run, including the _shared fund summary> — attached
```
Read the filled review (attach the workbooks and Review.completed.xlsx) and write memory:
```
ONBOARDING REVIEW
Run folder: <same>
Workbooks: <same>
Filled review: /Shared Documents/Valuations/4.human_review/<Company>/<YYYY>/<Qn>/Review.completed.xlsx
MEMORY: /Shared Documents/Valuations/5.company_memory/<Company>.memory.json
```
Extraction / resume (new runs): `ONBOARDING EXTRACTION` / `ONBOARDING RESUME` with `Quarter end`, `Model`, `Run id`, `Run folder`, `Workbooks` (+ `MEMORY:` on resume once memory exists).

## Decisions to remember (Log D-13 to D-22)

Test bench frozen (D-13). Stage 7 proposals / stage 8 validation (D-14). Memory = person-confirmed facts and assumptions only (D-15). Memory location configurable until Q-15 with Jim (D-16). Revisions only when both values are in the files (D-17). Approve / Correct / Reject, blank never approval (D-18). Onboarding done, move to quarterly mode (D-19, D-20). Pending decisions persist and block (D-21). Review fixes in 13.2.1 (D-22).

## Decisions 13.2.4 (add to Log)
Review round trip pinned to an immutable proposals snapshot; review workbooks built before 13.2.4 are refused (build a fresh one). Found by the review guardrail: zero wrong facts written.

## Decisions 13.2.3 (add to Log)
Contradiction gate before memory; identity uncertain is never merged and goes to the analyst. Any change to a run's source set means a fresh onboarding; memory confirmed from replaced workbooks for the same period is not reused. Exact naming applies only to generated files; sources are discovered (no fixed names, counts or layouts). An incoherent memory file is moved aside, never edited, and rebuilt.

## Next

1. Install 13.2.3. Then the OceanSight end-to-end test on 13.2.3 (clean run folder, old OceanSight memory moved to `0.SS/`): extraction (pass A + RESUME), corrected Gold grading, fresh review, clean memory write, memory reuse run. Check the Opus memory with `memory.py check` before Opus enters quarterly mode.
2. Rerun one company with `MEMORY:` into `<Qn>_r2/` to check memory is used (matches not re-asked, pending decisions surfaced).
3. Optional: add a SharePoint "list folder" tool so the extractor can see which run folders exist instead of probing by fetching files.
4. Quarterly mode (13.3): last quarter's approved workbook + new monthly files + confirmed memory + approved changes + pending decisions → new workbook typed by code with source notes, formulas live, change log, verdict in file name. Backtest on Q3 against the analyst's finished Q3 workbook (D-08).

Open: Q3 input file locations; Q-14 (answer-key workbooks and the adjustments template); Q-15 (memory location, Jim).


## 13.2.5 update (onboarding frozen after this build)

| Item | Version | Notes |
|---|---|---|
| Extractor skill | 13.2.5 | Active-run reuse (`run_manifest.py context`), run allocation from a folder listing (`allocate`, names only), review package in `4.human_review/`, review input diagnostics, question merging (`question_groups`), same-period memory reuse, source-precedence consistency, material-chain sufficiency check, generation handoff (`handoff.py`). Unchanged: verify, xlsx_evidence, reconcile, guard, concepts |
| Test bench | 13.2.2 + naming wrapper 13.2.5 | `report_store.py`: `<run id>_grading_report_vN.json` in `3.test_bench_outputs/`; grading code untouched |
| Tests | 13.2.5 45/45, 13.2.4 19/19, 13.2.3 67/67, bench 353/353, wrapper 7/7 | 127 older extractor tests not yet rerun |
| Copilot Studio tools to add | | SharePoint listing tool on both agents; Create file on the test bench |

Generation handoff: `/Shared Documents/Valuations/6.generation_handoff/<Company>/<YYYY>/<Qn>[_rN]/<run id>_generation_handoff.json`, schema `xpv-generation-handoff/1`.

Open policy point: a multiple confirmed for the same period with the same value is reused rather than re-asked (always asked in a new quarter).
