# XPV Valuation Automation — System Spec

_Draft 2, October 28, 2026. Replaces Draft 1 (October 16). The rulebook for how the finished system behaves. When a rule changes, change it here first, then record the decision in the Log._

**Changes in Draft 2:** §3a review workbook rewritten to match review_xlsx 13.2.6; §7 memory updated to match memory.py; new §9 hand-off contract; new §10 run hygiene rules (memory first, no silent drops, approved upload method, clean responses); §8 outputs updated.

## 0. Legend

| Term | Meaning |
|---|---|
| Run | One company, one quarter, one run number (rN) |
| Extractor | The AI agent that reads the files and proposes what each number is and what changed |
| Checking code | Tested programs that confirm every AI claim, read reviews, write memory and do all typing |
| Company memory | One file per company of confirmed decisions (§7) |
| Pending decision | A review question the analyst left blank on purpose; it comes back next run |
| Hand-off | The file that passes a reviewed onboarding to workbook generation (§9) |
| Fingerprint | A digital code for a file; any change to the file changes it |
| Pass / to the analyst / stopped | The three results for each item (§5) |
| Release stage | Track changes, approve new or unsure, or auto (§6) |
| STOPPED (memory) | Two different answers for the same item; neither is saved |
| Source note | A comment on every typed number saying which file, sheet and cell it came from |

## 1. Ground rules

Unchanged from Draft 1: every approval by a person; AI never types into a workbook; universal agents; answer keys only measure; exact matching; data stays in XPV's Microsoft 365; two-company rule for new checks.

## 2. Inputs for a run

| Input | Where it comes from |
|---|---|
| Last quarter's approved valuation workbook | Company "approved" folder (supplied by a person until it exists) |
| The new quarter's monthly files | Uploaded by the operator |
| Company memory | `5.company_memory/<Company>.memory.json`, written only by code |
| Generation hand-off | `6.generation_handoff/<Company>/<YYYY>/<Qn_rN>/` (generation runs only) |
| Investor fund workbooks | Phase C only |

## 3. Start of every run: the analyst answers

Standard questions 0–11 and the acquisitions table: unchanged from Draft 1.

New: **pending decisions from memory are shown first**, before the standard questions.

## 3a. The review workbook (review_xlsx 13.2.6)

**Sheets:** Start here · Unresolved decisions · Proposed changes · Memory candidates · Legend (plus hidden `_bundle` and `_meta`, never edited).

**Reviewer name** (Start here, B6) is required.

**Allowed answers:**

| Sheet | Decision options | Notes |
|---|---|---|
| Unresolved decisions | **Correct** or **Reject** only (or blank) | No suggested answer exists, so **Approve is invalid** and the review is refused. Correct needs the answer in "Your correction" |
| Proposed changes | Approve · Correct · Reject (or blank) | "Always confirm" rows (the multiple) need a decision every quarter |
| Memory candidates | Approve · Correct · Reject (or blank) | Only Approve or Correct adds to memory |

**Correction types:** each row's "Correction may be" column lists the allowed type: Number (`8.75`), Cell (`'Sheet'!D9` or `W2:'Sheet'!D9`) or Text (one plain sentence). Explanations go in **Comment**, never in a number or cell field.

**Blank = not approved.** A blank unresolved decision is kept as pending. A blank never counts as approval.

**Consistency:** answers that conflict across sheets for the same concept STOP that concept from being saved.

**Refusal:** if any row is invalid, the whole review is refused and nothing is written. The analyst fixes the workbook and resubmits.

**Identity:** a review is read only against the exact proposal snapshot and bundle it was built from. A mismatch stops memory writeback.

## 4. Checks code always runs

Unchanged from Draft 1.

## 5. Sorting rules

Unchanged from Draft 1, plus: an item that depends on a **pending** decision is always **to the analyst**, never pass.

## 6. Release stages

Unchanged from Draft 1.

## 7. Company memory

**Update rules**

- Entries are only added; nothing is edited or deleted.
- The latest confirmed entry for an item wins and keeps what it replaced.
- Only Approve or Correct creates an entry. Unconfirmed items never make an item pass.
- Analyst answers to unresolved decisions and approved "Always confirm" values are saved as **assumptions for that period**.
- Deliberate blanks are saved as **pending** and asked again each run until answered or rejected.
- Conflicting answers for one concept are **STOPPED**, not saved.
- Memory is written only by memory.py, with a hash chain; a file that fails its chain check is rejected.

**Entry kinds:** fact (the workbooks show it) · assumption (a person's call). Categories: mapping, source precedence, method or judgment, period fact. Operational observations stay as run evidence unless the analyst makes them a rule.

**Every entry carries:** item ID, concept, value or rule, period, evidence cells, who confirmed it, date and the analyst's own words.

**Reuse on a repeat run:** before building a review, code reconciles new findings against memory by concept. The run reports four groups: **reused**, **pending carried forward**, **reopened by changed evidence**, **new**. Confirmed items consistent with current evidence are not asked again. Changed or contradictory evidence reopens them.

**Location portability:** memory stores the last confirmed cell and its meaning (label, role, period). Generation must validate both before writing; a location match alone is never enough.

## 8. Outputs of a run

**Onboarding:** extraction and verification files, review workbook, review decisions and approved changes, company memory, hand-off.

**Generation (Phase 6):**

- The new valuation workbook: a copy of last quarter's, with confirmed values typed by code, a source note on every typed number and formulas kept live.
- A change log: old value, new value, source, result and type ("this quarter only" or "saved to memory").
- A verdict in the file name: ready for sign-off, or needs attention.
- New memory candidates for the analyst to confirm.

## 9. Generation hand-off

Built by code after an accepted review. File: `6.generation_handoff/<Company>/<YYYY>/<Qn_rN>/<Company>_<YYYY>_<Qn>_rN_generation_handoff.json`.

**Carries:** confirmed memory items, inputs to refresh each quarter, formulas to keep as they are, and unresolved items.

| Status | Meaning |
|---|---|
| `ready` | Nothing pending |
| `ready_with_unresolved` | Generation can run; each pending item goes to the analyst and blocks auto-apply of what it affects |
| Not built | Review refused or memory STOPPED |

## 10. Run hygiene

- **Memory first.** If memory exists, it is loaded and attached before stage 1, never mid-run.
- **No silent drops.** Every candidate becomes a proposal or an open question. "Unclear" is a reason to ask, not to skip.
- **Approved upload method.** Files go to SharePoint by staged file path. After each upload, code checks size and hash against the local file. Printing files as text (base64) or retyping files from context is not allowed. Memory is always copied byte for byte.
- **Checkpoint after every stage.** Each stage's checkpoint is uploaded right after it is saved, not batched for later.
- **Clean responses.** Normal replies show only Status, Material result, Decisions you need, Next action and Resources. Paths, staging, retries and checkpoint revisions stay internal unless the user must act.
