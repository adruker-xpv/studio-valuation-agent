# Workbook discovery and benchmark – build 11.5: what it is, how to set it up, how to run the Gold benchmark

## Glossary
| Term | Meaning |
|---|---|
| Discovery system | `discovery/discover.py`: reads one workbook (never changes it) and writes a map of what it contains and how it connects |
| Benchmark system | `benchmark/bench.py`: grades the map against an independent answer key. It never imports discovery code |
| Gold workbook | A frozen, approved historical valuation workbook, hash-locked (SHA-256), used only to test discovery |
| Answer key | The independent truth for one Gold workbook: Excel's own counts and precedents plus the analyst's blind answers |
| Blind | Answered by the analyst from the workbook itself, before any discovery output exists |
| Layer 0 / 1 / 2 | What the file contains / the formula relationships derived from it / what the important cells mean financially |
| Enterprise value (EV), trailing twelve months (TTM), limited partner (LP) | As in earlier builds |
| Gate | An open item (e.g. an unclassified region) that blocks a claim of complete understanding; never averaged |
| Invariant | A consistency check discovery runs on the workbook (e.g. EV = multiple × metric, the balance sheet balances). Not ground truth |
| Pre-flight | The check that a file can be read at all, before any parsing |
| PROVEN but wrong | Discovery claimed PROVEN and the key disagrees: the status rules themselves need fixing |

## What changed in 11.5
- Unreadable files (legacy `.xls`, password-protected, `.xlsb`, damaged) are refused up front with one `PREFLIGHT: REFUSED`
  line saying what to do. Files are passed by name; two different files with the same name stop the run.
- A bug now prints one `DISCOVERY ERROR:` / `BENCHMARK ERROR:` line and writes the details to a log file; nothing else changes.
- Discovery runs eight consistency checks (invariants) and reports them as `consistency, not truth`.
- Small formula-free areas are now read completely; a corrupt named range is flagged.
- Rules live in versioned data files; a changed rule shows up as `method changed yes` in the regression line.

## What build 11.5 does – and does not do
**Does:** for one frozen Gold workbook, accounts for everything that physically exists; builds the full formula graph with a
status on every formula (nothing stops silently); finds calculation regions the outputs do not reach; proposes the
outputs, junctions and periods with their evidence; classifies every input the outputs depend on; and measures all of
it against an answer key whose content never comes from the discovery code.
**Does not:** generate, update or value anything; reconcile statements; recalculate in Excel. The valuation pipeline
(build 11.3) is parked unchanged; its modules are reused read-only inside discovery.

## Who does what
| Who | Does | Time |
|---|---|---|
| Aria | set-up, runs the commands (in the agent or on an approved machine), sends back BENCHMARK lines | ~2 h first Gold, ~10 min per build after |
| Analyst (the one who approved that quarter) | blind answers, sample periods and kinds, region review | ~1.5–2 h once per Gold workbook |
| Valuation lead | signs off the counting rules; agrees thresholds after the first run | ~30 min, twice |
| Claude (me) | code, synthetic tests, interpreting the BENCHMARK lines you send | – |

## One-time set-up
1. **Sign off the counting rules** (`docs/stage0-counting-and-status-rules.md` in the skill): you and the valuation lead.
2. **A separate Copilot Studio agent** (or update the existing one: replace the skill with build 11.5's zip and the instructions with `agent-instructions-discovery.txt`) ("Workbook Discovery Benchmark"): add only the `workbook-discovery.zip` skill
   (upload as downloaded); paste `agent-instructions-discovery.txt` into Instructions; knowledge: *Valuation Workbooks*
   only; no other tools needed. Keeping it apart from the valuation agent stops either agent's rules interfering.
   (Alternative, cheaper per run: an XPV machine with Python 3.12 and openpyxl, if XPV IT approves; same commands.)
3. **Office Script:** in SharePoint, add `gold-facts.ts` as a new script (do not replace `recalc-and-read`). It only reads.
4. **Test:** in the new agent say "Run the discovery tests." → `ALL TESTS: PASS (37/37)`.

## The first Gold benchmark (Gold v1), step by step
Pick the **structurally simplest** approved historical workbook (failures then belong to the engine, not the layout).
Do the steps in this order; step 5 must finish before step 6.

| # | Who | Do | Correct when |
|---|---|---|---|
| 1 | Aria | Copy the workbook to a read-only SharePoint folder `Valuations/_gold/GOLD-01/`. Never open it in Excel for editing again (a re-save changes the file). Agent: "Hash the Gold workbook." | a `BENCHMARK: workbook SHA-256 …` line; note it |
| 2 | Aria | Agent: "Make the answer-key template for GOLD-01, quarter end 2026-03-31", then "Draw the sample." Download `gold_key_GOLD-01.xlsx` and `gold_facts_precedents_request.json` | template written; sample of up to 45 cells across physical strata |
| 3 | Aria | On a **copy** of the Gold file in Excel for the web: Automate → gold-facts → Run with `{"mode": "counts"}`; save the logged JSON as `excel_facts_counts.json`. Run again with the content of the request file; save as `excel_facts_precedents.json`. (A very large workbook: run counts per sheet with `{"mode": "counts", "sheets": ["<name>"]}` and send me the parts to merge.) | two JSON files; precedents for the sample cells |
| 4 | Analyst | Fill `gold_key_GOLD-01.xlsx` from the workbook alone (Excel, Trace Precedents allowed; no discovery output): sheet 1 the junction cells and values; sheet 2 the material areas and the known historical / reference / presentation areas; sheet 3 the period and kind of each sampled cell ("unsure" is fine) | every junction answered as Sheet!Cell |
| 5 | Aria | Upload the filled template. Agent: "Freeze the blind answers as <analyst's name>." Store `blind_GOLD-01.json` read-only next to the Gold file | `BENCHMARK: blind answers frozen …` |
| 6 | Aria | Agent: "Run discovery on <Gold file> for 2026-03-31." Download `discovery_review.xlsx` | a `PREFLIGHT: OK` line, then `DISCOVERY:` lines including `invariants` |
| 7 | Analyst | In `discovery_review.xlsx`, give each unreached region (often a family of history columns) a verdict: material, supporting, reference_only, historical, presentation, irrelevant or unsure | every row has a verdict |
| 8 | Aria | Upload `blind_GOLD-01.json`, both facts files and the filled review. Agent: "Build the answer key." Store `answer_key_GOLD-01_v1.json` read-only | `BENCHMARK: answer key GOLD-01 v1 built …` |
| 9 | Aria | Agent: "Score the benchmark." Download and keep `benchmark_result.json` (private) | `BENCHMARK:` lines ending in a `result` line |
| 10 | Aria | Send me **only the BENCHMARK lines**. They hold counts and categories, no names, cells or values (add "without numbers" for `--redact-counts` if XPV prefers) | – |

## Every build after that
I send a new skill zip with the synthetic tests passing. You: upload it, "Run the discovery tests", "Run discovery on
<Gold file> for 2026-03-31", then "Score the benchmark" with last time's `benchmark_result.json` uploaded (it becomes
`--previous`). Send me the BENCHMARK lines. No analyst work unless the report shows **unaccounted regions** (new
unreached regions): the analyst classifies them and we build key v2. A build is only an improvement if the regression line
shows no new failures.

## Reading the BENCHMARK lines
| Line | Asks | Good looks like |
|---|---|---|
| physical | did discovery capture what Excel says exists? | every item `X of X PASS` |
| formula understanding | of Excel's formulas: text captured, references extracted, fully interpreted, recomputed | first two equal to Excel's count; unsupported and dynamic visible, not zero by force |
| period understanding | on the sampled cells: correct, wrong, abstained, false certain, proven but wrong | wrong, false certain and proven but wrong all 0; abstaining is acceptable |
| material web | outputs and junctions found; sampled relationships exact; silent omissions; material regions reached | outputs all found; silent omissions 0; regions all reached |
| invariants consistency not truth | holds / violated / not applicable / not evaluated | violated 0; a violation is a gate to investigate |
| terminal accounting | material inputs classified / unresolved | unresolved falling over builds |
| human | Python-only, AI, analyst confirmations needed | confirmations falling without accuracy falling |
| gates open | everything still open | eventually none |
| unscored claims | what the key does not cover yet | small; growth means the key needs extending |
| regression | previous checks still passing, new failures, fixed, method changed | new failures 0 |
| result | physical import, material graph, safe to proceed to generation design | YES only after a second, structurally different Gold passes too |

## Gold v2
Choose a workbook with a feature v1 lacks (pro forma or acquisition, a waterfall / cap table, external workbooks, or a
different method). Repeat steps 1–9 as GOLD-02; score each with the other's result as `--other-gold`.

## Known limits of build 11.4 (visible, never silent)
- Monthly blocks are read up to 400 rows below their header (the 11.3 reader); rows below show up as unresolved terminals.
- Memory: see the run log (`run_log.json`, peak memory and timings per stage); a very large workbook may hit the sandbox limit (the run
  stops with an error rather than a partial map). If so, send me the DISCOVERY lines and the file size.
- Excel's `getDirectPrecedents` and `getLinkedWorkbooks` are assumed available in Office Scripts. If precedents mode
  returns "unavailable", those samples are reported as unscored, never as passes.
- Statement evidence, refresh, approval and the Excel recalculation step are parked (build 11.3), not part of this benchmark.

## Troubleshooting
| You see | Do |
|---|---|
| `PREFLIGHT: REFUSED …` | do what the line says (save as .xlsx, remove the password, fetch the file again) |
| `STOPPED: … different files are named …` | two versions with one name were found: tell the agent which one (its full path) |
| `DISCOVERY ERROR:` / `BENCHMARK ERROR:` | a bug: send me the line (the log file stays with you unless I ask for its first lines) |
| `STOPPED: … older than the blind answers` | discovery ran before the freeze: freeze first, then run discovery again |
| `STOPPED: … different workbook (hash differs)` | the Gold file was re-saved or the wrong file was fetched: use the locked copy |
| `STOPPED: … changed after it was built / frozen` | a key or blind file was edited: use the stored read-only file |
| `STOPPED: the template already has a sample` | a Gold sample is drawn once; start a new template for a new key version |
| physical FAIL | send me the BENCHMARK physical line; usually a counting convention to settle (counting rules §1) |
| silent omissions > 0 | the most important failure: send me the material web line |
