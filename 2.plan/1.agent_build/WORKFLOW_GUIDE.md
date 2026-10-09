# XPV Onboarding workflow - build guide (build 13.0)

Platform facts are carried over from build 12.0 (8 October 2026, Microsoft Learn). Copilot Studio changes monthly: recheck the model list
and the workflow features before each new build. While the workflow is paused, run the agents by hand with `MANUAL_RUN_PROMPTS.md`.

## Legend
| Term | Meaning |
|---|---|
| Extractor | Agent 1, "XPV Onboarding Extractor": maps the valuation across the supplied workbooks; writes `extraction.json` in stages |
| Reviewer | Agent 2, "XPV Onboarding Reviewer": independent second reader, called twice (blind, then review) |
| Workflow | A Copilot Studio workflow (GitHub Copilot harness) that calls the agents with agent nodes and passes only files |
| Pass A / pass B | The extractor's two bounded calls: stages 1-3 (first usable extraction) / stage 4 to the end |
| RESUME | Continue from the last checkpoint; used for pass B and after any interruption |
| Checkpoint | A saved stage file (`checkpoints/NN_name.json`); `extraction.json` is rebuilt from them after every save |
| Reader | `xlsx_evidence.py`: read-only, streaming access to workbook evidence (safe on inflated used ranges) |
| verify | `verify.py`: tests each claim (formula links, matches, rounding, sums, the window, discrepancies, the fund link) |
| Reconcile | `reconcile.py`: compares the two agents by file fingerprint, checks the reviewer's claims, measures what it added, writes the analyst's review |
| Fingerprint | A workbook's SHA-256; every agent records it, and source ids follow file names |
| TTM / EV | Trailing twelve months / enterprise value |

## What changed from 12.0, and why
Test2 (five real workbooks) showed the model's reading was right while the run timed out before saving anything. 13.0 keeps the
AI-led interpretation and fixes the harness around it:
1. **A streaming reader.** The 12.0 reader walked every cell of a sheet's used range; one inflated range (formatting out to row 1,048,576)
   could keep a call silent for minutes - the likely trigger of the StreamInactivityTimeout. The new reader reads only populated cells,
   shows formulas and saved values together, exposes hidden and very-hidden sheets, shared / array / data-table formulas and links to
   other files, answers targeted questions, and stops with an explicit STOPPED line at a time budget.
2. **Checkpoints and an early artifact.** Work is saved in seven small stages; a provisional `extraction.json` exists from stage 3, and a
   fresh call rebuilds it exactly from the checkpoints. The extractor runs as two bounded passes; any interruption is a RESUME.
3. **Any number of workbooks.** Upstream files (monthly financials, XPV monthly summaries, pro forma files) are first-class sources with
   roles; links to files that were not supplied get their own ids.
4. **Evidence classes on every edge**, tested by verify. Numeric equality is never promoted to a link; a preserved discrepancy passes.
5. **Primary result vs evidence.** Stage files have size caps; inventories, cell dumps and reasoning live in `notes.md` and `evidence/`.
6. **A sharper reviewer.** Phase 1 works bottom-up (the extractor works top-down); phase 2 settles a deterministic list of contested
   items; reconcile reports whether the second reading added anything - agreement alone is not counted.
7. **No exhaustive coverage gate.** 12.0's rule that every formula using the chain must be explained is gone; materiality decides.

## The flow
```
 Trigger (company, quarter end, the workbook paths - any number, reviewer)
   -> Agent node 1: Extractor PASS A   "ONBOARDING EXTRACTION"  -> checkpoints 1-3, extraction.json (provisional)
   -> Agent node 2: Extractor PASS B   "ONBOARDING RESUME"      -> checkpoints 4-7, extraction.json (final)
   -> Condition: node 2's next_stage is not null -> Agent node 2b: Extractor "ONBOARDING RESUME" (once)
   -> Agent node 3: Reviewer PHASE 1 (workbooks only)           -> reviewer/checkpoints, reviewer/reviewer_blind.json
   -> Agent node 4: Reviewer PHASE 2                            -> review.json, out/ (reconcile)
   -> if findings or disagreements: Agent node 5: Extractor "ONBOARDING RESPONSE" -> out-final/
   -> Approval to the named reviewer -> record the decision; if approved, copy extraction.json to the approved folder
```
Each agent node is its own run; only files move between them. Node 3 needs only the workbooks, so it may run before or alongside nodes 1-2.

## 1. SharePoint (once)
- `Onboarding` for run folders; `Companies/<Company>/approved/` for approved extractions.
- A list `Onboarding decisions`: Company, Quarter end, Run folder, Workbook SHA-256s, Status, Extractor model, Reviewer model, Approver,
  Decision, Decided at, Comments.
- Keep `trial/keys`, `trial/reference` and the test-bench skill away from everything the two workflow agents can reach.

## 2. Skills
| Skill ZIP | Extractor | Reviewer | Test bench agent |
|---|---|---|---|
| `xpv-valuation-playbook.zip` | yes | yes | - |
| `xpv-onboarding-extractor.zip` | yes | - | - |
| `xpv-onboarding-reviewer.zip` | - | yes | - |
| `xpv-onboarding-testbench.zip` | **never** | **never** | yes |

## 3. Models (unchanged from 12.0 - recheck the list before each build) (as listed for Canada in the GitHub Copilot harness, September 2026)
| Model | Microsoft's tag | Canada | Use here |
|---|---|---|---|
| Claude Opus 5 | Deep | Generally available (cross-geo) | **Extractor** |
| GPT-6 Astra | General | Generally available (cross-geo) | **Reviewer** (OpenAI's newest flagship, released 3 Sep 2026) |
| Claude Fable 5.1 | General | Generally available (cross-geo) | Worth one test as Extractor if Opus 5 misses things |
| GPT-5.6 Reasoning | Deep | not offered | - (experimental, US early-access environments only) |

- **Pin the model** on each agent; never leave it on "Default". The default changes as new models arrive, and an agent
  falls back to the default if its selected model is unavailable. Record each agent's model in every run.
- Microsoft tags GPT-6 Astra "General" (its speed/cost category), while OpenAI positions it as its most capable model.
  Decide on evidence: run the trial (section 6) with the Reviewer on Astra and again on Opus 5, and compare scores and credits.
- All three models above are **cross-geo** for Canada: data may be processed outside Canada, and external (Anthropic) models
  need admin opt-in. Confirm this is acceptable for XPV's confidential workbooks with your admin before real runs.

## 4. The agents (GitHub Copilot harness)
For each of the Extractor and the Reviewer:
- **Instructions:** `agents/extractor-instructions.txt` / `agents/reviewer-instructions.txt`.
- **Model:** pinned, per section 3. **Memory: off. Knowledge: none.**
- **Tools:** SharePoint "Get file content" (to fetch workbooks and, when resuming, checkpoints) and "Create file" (to save into the run
  folder). Scope connections to read the source libraries and write only to `Onboarding`.
- A third, chat-only agent, **XPV Onboarding Test Bench**, gets the test-bench skill and its instructions.

## 5. Getting the real .xlsx files to the agents
The scripts need the original workbooks with their formulas. Prefer SharePoint paths in the message (the agent fetches them); attach
as a fallback (16 MiB per file, 20 files per conversation). Either way the `READ:` lines settle it: each shows the formula count and the
fingerprint, and `READ WARNING: ... no formulas` flags a values-only copy.

## 6. The workflow (Copilot Studio > Workflows)
**Trigger:** manual, with `company` (as the fund workbook names it), `quarter_end` (YYYY-MM-DD), `workbooks` (the SharePoint paths, one
per line), `reviewer_email`. Compose the run folder from them and utcNow. Turn **Request human assistance when unsure** off on every node.
Node messages are the prompts in `MANUAL_RUN_PROMPTS.md`, with the line `Use ONLY the attached workbooks` replaced by
`Workbooks (fetch each from SharePoint): <workbooks>`. Read each reply's last line (JSON) with structured output or a Parse JSON step.
**Approval:** "Start and wait for an approval" to `reviewer_email`. Title `Onboarding <company> <quarter_end>: <status>`; details: status,
key answers agreed, reviewer value, discrepancies, questions, both models, and the link to `onboarding_review.xlsx` (from `out-final/`
if node 5 ran, else `out/`). **Record:** always add an `Onboarding decisions` row; if approved, copy `extraction.json` to
`Companies/<company>/approved/extraction-<quarter_end>.json`. Nothing is deleted; a rerun is a new run folder.

## 7. Testing, in this order
1. **Test bench:** "Run the onboarding tests" -> `TESTS: PASS (84/84)`.
2. **Synthetic trials:** run the flow (or the manual prompts) on `trial/set-T1` (five workbooks) and on `trial/workbook-52` and
   `trial/workbook-94`, quarter end 2026-06-30, in a test folder without keys. Score each agent's file in the test bench
   ("Score <file> for trial set T1"; "... for trial workbook 52"). Bar: 9/9 and confidently wrong 0; T1 must also show the fund
   discrepancy recorded, not forced.
3. **Test2 regression:** rerun the five real Test2 workbooks with `TEST2_REGRESSION.md`; bring back only its sanitized form.
4. **Reviewer model comparison:** repeat 2 with the Reviewer on another model; compare scores, reviewer value and credits.
5. **First real Gold workbook (benchmark):** the analyst fills `analyst_answers_template.xlsx` before seeing any agent output; score both
   agents against it. Bar: zero confidently wrong.

## 8. Later, not now
- Turn approved onboardings into agent evaluation test sets so every model or skill change is regression-tested.
- For reading monthly statements, test Copilot Studio's workflow extract node against the agent reading them.
