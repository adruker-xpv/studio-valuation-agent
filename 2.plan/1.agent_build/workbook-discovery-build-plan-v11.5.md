# Workbook discovery – build plan v11.5 (supersedes the 11.4 plan notes)

## 1. Glossary
| Term | Meaning |
|---|---|
| Discovery system | Reads one workbook (never changes it) and writes a map of what it contains, how it connects and what it means |
| Benchmark system | Grades a map against an independent answer key; never imports discovery code |
| Layer 0 / 1 / 2 | Physical facts / formula relationships derived from them / financial meaning |
| Gold workbook | A frozen, approved historical valuation workbook, hash-locked (SHA-256), used only for benchmarking |
| Answer key | Excel's own counts and precedents plus an analyst's blind answers for one Gold workbook |
| Invariant | A consistency check on a workbook (e.g. enterprise value (EV) = multiple × metric). Not ground truth |
| Gate | An open item that blocks a claim of complete understanding; never averaged into a score |
| Decision registry | (Milestone 2) the record of every mapping decision, bound to the inputs it was made from |

## 2. Purpose and scope
**Milestone 1 (unchanged):** for a frozen historical workbook, account for every physical structure in scope; reconstruct its
formula graph without silent truncation; independently validate the critical junctions, periods and a frozen sample of
relationships; and quantify everything ambiguous, unsupported or unscored.
**Not in milestone 1:** generating or updating workbooks, statement reconciliation as a goal, Excel recalculation, AI
interpretation, approvals. These belong to milestone 2 and start only when milestone 1's exit criteria are met.

## 3. Architecture
```
            GOLD WORKBOOK (hash-locked, read-only)
                  │                        │
   DISCOVERY      ▼                        ▼  INDEPENDENT EVIDENCE
   pre-flight → Layer 0 inventory          Excel itself (gold-facts.ts): counts, direct precedents
              → Layer 1 graph + flags      Analyst, blind: junctions, periods, regions, sample kinds
              → regions, hubs, sinks       Analyst, after discovery: classify unreached regions only
              → Layer 2 proposals                         │
              → invariants                                ▼
              → MAP (private files)              ANSWER KEY (frozen, hashed)
                  │                                       │
                  └──────────────► BENCHMARK ◄────────────┘
                                   scores, gates, regression → BENCHMARK lines (counts only)
```
**Contracts.** Files: `workbook_map.json` and `cells.jsonl.gz` (deterministic), `discovery_review.xlsx`, `run_log.json`
(non-deterministic, kept apart), `answer_key_*.json` and `blind_*.json` (schema-validated, self-hashed),
`benchmark_result.json`. Printed lines: `PREFLIGHT:`, `DISCOVERY:`, `BENCHMARK:`, `STOPPED:`, `... ERROR:`, `NEXT:`,
`ALL TESTS:` (documented in SKILL.md; test C.1). Exit codes: 0 / 1 internal / 2 usage / 3 user must act.
**Trust boundary.** Workbooks, maps, keys and reports stay in the authorised environment. Only BENCHMARK lines (counts and
categories from a fixed vocabulary, optionally without numbers) leave it.

## 4. Engineering standards (how every build is made)
| Standard | How it is enforced |
|---|---|
| Separation of discovery and benchmark | import test (B.1); keys built only from Excel facts and analyst answers |
| Read-only, deterministic discovery | tests D.13, D.12; one clock (`VALUATION_NOW`); sorted output; fixed gzip timestamp |
| No silent truncation | five flags on every formula (D.4); unreadable references are flags, not stops |
| Never claim absence without looking | NOT_EVALUATED when cells were not read (I.2) |
| Fail fast, fail clearly | pre-flight before parsing (P.1); `Stop` → one `STOPPED:` line; bugs → one error line + log (E.1) |
| Configuration as versioned data | rules and invariants in JSON, validated at start-up; hashes in the map; a changed hash is a method change |
| Contracts are tested | printed prefixes and exit codes (C.1); schemas (S.1) |
| Vendored code unchanged | byte-hash test (V.1); one adapter |
| Hygiene | every module compiles, has a build header, no placeholder code (C.2) |
| Releases are gated | `tools/release.py`: tests → package check → deterministic zip → manifest with every file's hash |
| Test-first fixes | every real-workbook failure is first reproduced in a synthetic fixture with a failing test |
| Versioning | build numbers 11.x; rule versions R/P/I; answer-key versions v1, v2…; schema versions; all recorded per result |

**Test families:** D discovery, B benchmark (including tests that the benchmark fails wrong maps), M mutations (layout
changes pass, real changes fail), P pre-flight and files, I invariants, E errors, S schemas, R rules, C contracts and
hygiene, V vendored code. Build 11.5: 37 tests.

**Definition of done for any build:** all tests pass in the agent-like layout (non-root, read-only skill folder,
`TMPDIR=/app/workspace`); release manifest produced; CHANGELOG and SKILL.md updated; any new printed prefix, rule or
invariant has its test; the Gold benchmark (once it exists) shows no new failures.

## 5. Roadmap with entry and exit criteria
| Build | Content | Exit criteria |
|---|---|---|
| 11.4 (done) | discovery + benchmark, milestone 1 | 26 tests |
| **11.5 (this)** | pre-flight, files by name, error taxonomy, rules as data, invariant registry, schemas, release gate, coverage fixes | 37 tests; release manifest; counting rules signed off |
| 11.6 | **Gold v1**: run the guide's steps; triage every failure by category (physical, relationships, periods, junctions, regions, gates); reproduce each in a fixture before fixing | physical import PASS; every failure explained; thresholds agreed with the valuation team |
| 11.7 | **Gold v2**: a structurally different workbook (pro forma, waterfall, external links or another method) | both Gold workbooks pass material graph with no open gates; no regression; `safe to design generation: YES` |
| 12.0 (design only) | milestone 2 design: generation, using the decision registry (§6), the invariant registry as draft checks, the linked-workbook policy, the parked 11.3 Excel diagnostic and statement evidence | design reviewed before any generation code |

## 6. Decision registry – specification for milestone 2 (not built in 11.5)
**Why not now.** Milestone 1 has no AI step and no mapping decisions to reuse; building the registry now would be
untested speculative code. Its interface is fixed here so milestone 2 builds to it.
**Purpose.** A mapping choice (a statement line to a workbook row, a field's cell, a period convention, a linked-workbook
policy) is made once, verified, approved by a named person, stored, and reused identically until the inputs it was based
on change. Nothing is re-guessed per run, so model or prompt variation cannot change an approved mapping.
**Record.**
```json
{"id": "D-<hash of company, type, subject>", "company_id": "...", "type": "line_map | field_cell | period_convention | link_policy | entity",
 "subject": "what was decided about", "value": "the decision",
 "basis": "ai_proposal | analyst | rule", "proposed_by": "<model and version, or person>",
 "verified": {"by_python": true, "check": "all overlap months equal after scale and sign"},
 "approved_by": "<name>", "approved_on": "YYYY-MM-DD", "said": "<the approver's words>",
 "inputs_fingerprint": {"workbook_structure": "<layout fingerprint>", "sources": ["<statement line identity hash>"]},
 "status": "active | superseded | invalidated", "supersedes": "D-..."}
```
**Rules.** (1) Only approved decisions are reused. (2) Reuse requires the current inputs' fingerprint to equal the stored one;
otherwise the decision becomes *invalidated*, is re-proposed, re-verified and re-approved; never silently kept. (3) AI
proposals are never stored without Python verification where verification is possible, and never without approval.
(4) Storage: the company file's hash-chained ledger (built in 11.x); hashing proves the record was not altered, approval and
verification prove it was right. (5) Every reuse is logged with the fingerprint it matched.
**Tests to write with it:** reuse on identical inputs; invalidation when a statement line is renamed or the layout
fingerprint changes; refusal to store an unverified AI proposal; tamper detection; an approved decision survives a model
change unchanged.

**Linked-workbook policy for milestone 2.** Discovery treats an external reference as an identified boundary and never
refuses. Generation refuses to produce a draft while an active link has no source, unless a recorded decision says
"carry the value" for that link.

**Invariants in milestone 2.** The registry built in 11.5 becomes the check on every generated draft (there is no answer
key for a new quarter). Because invariants pass consistent-but-wrong mappings (test I.3), they complement the decision
registry and analyst approval; they never replace them.

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Counting conventions differ between Excel and the reader (spills, print-area names, empty strings) | listed in the counting rules as "confirm on the first run"; a physical FAIL is triaged as a convention before it is treated as a bug |
| Reader limits: monthly blocks read 400 rows below a header; memory on very large workbooks | both visible (unresolved terminals; one error line); measured on Gold v1 before optimising |
| Office Scripts lacks `getDirectPrecedents` in XPV's tenant | the sample's relationship checks report as unscored, never as passes; fallback: precedents typed by the analyst |
| Rubber-stamped review | junctions, regions and the sample are answered blind; only unreached regions are classified after discovery |
| Overfitting to Gold v1 | mutation tests; Gold v2 chosen for structural difference; fixes go through synthetic fixtures first |
| Scope creep into generation | milestone-2 work is design-only until 11.7's exit criteria are met |

## 8. Operating model
Claude: code, synthetic tests, release zips, triage from BENCHMARK lines. Aria: runs the steps in a dedicated agent (or
an approved XPV machine), stores Gold files, keys and results in read-only SharePoint folders, sends back BENCHMARK lines.
Analyst: blind answers (~1.5–2 h per Gold workbook) and region classification. Valuation lead: signs off the counting rules
and the thresholds.
