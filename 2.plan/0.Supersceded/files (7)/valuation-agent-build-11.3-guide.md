# XPV valuation agent – build 11.3: setup, tests and running

Replaces the 11.2 guide. Design reference: `valuation-build-plan-v11.1.md` plus the 11.3 principle below.

## Glossary
| Term | Meaning |
|---|---|
| Limited partner (LP) report | XPV's quarterly investor report; the pipeline works back from each company's LP numbers |
| Enterprise value (EV) / trailing twelve months (TTM) / EBITDA | EV = selected multiple × metric; TTM = the 12 months ending at the valuation month; EBITDA = earnings before interest, tax, depreciation and amortization (adjusted = plus approved one-time items) |
| Requested valuation date | The quarter-end the analyst asks for. `gather` now passes it to onboarding as `--period-end` |
| Dependency role | What a cell is to the LP numbers: LP output, TTM metric, monthly history, period-end balance, valuation assumption, investment cash flow, pro forma adjustment. Each role has its own period rule |
| Set aside | A candidate cell of another period, or a Budget / Variance / prior-year column, not used for the identities (listed under `PERIODS:`) |
| Exception | A finding that needs its own explicit decision before approval; approval is refused until each has one |
| Evidence status | Per month: reconciled (a statement proves it) / carried from the approved baseline (labelled) / unsupported / adjustment (the analyst approves) |
| Verification status | Verified automatically (Excel recalculation of a copy matched) / analyst-attested (desktop Excel, recorded) / not verified |
| Answer key | Private, analyst-filled expected cells, window, method and months for one company and quarter; stays in the authorised environment |
| Sanitised diagnostics | `VERIFY:` lines: test ID, result, category, role, periods, counts, evidence status. No values, names, cells or paths |

## Principle (settled for 11.3)
**Prove period and meaning first, then math, then evidence.** Every LP number is (1) the requested quarter's cell in the
right role, (2) reproduced by Python from its formula, (3) backed month by month by statements or explicitly carried from
the approved baseline. Onboarding describes and validates the approved method; it never changes it. Nothing becomes a
convention by group approval.

## Real-run findings: what 11.3 does about each
Status: the synthetic suite reproduces each mechanism; **none is confirmed on the real workbook until the verify run (test T6).**

| Observed (real run, sanitised) | Hypothesis | How it is tested | Built in 11.3 |
|---|---|---|---|
| Metric windows Jan–Dec 2024 for a Q1 2026 request; identities still passed | Candidates came from an older period column: gather never passed the date, ties were broken by cell order (left column first), identities only test numbers | Synthetic: two periods side by side reproduce it on 11.2 exactly (T1.50). Real: verify, `role ttm_metric` / `lp_output` lines | Request-anchored periods; other periods and Budget / Variance columns set aside; seven role rules |
| Selected multiple mapped to a comparable's row | Label search + numeric coincidence (the median of an odd peer set equals one peer) | Synthetic: reproduced on 11.2 (T1.54, T1.55). Real: verify `role valuation_assumption` | EV traced through its own formula; comparables listed as such and never selectable |
| Statements: only the workbook registered; trace showed downloads, then failed recognition | Two code paths found: gather silently dropped a file whose classification raised an error, and ignored monthly summaries named for an entity as "another company's" | Synthetic: T1.62. Real: gather's new `EVIDENCE:` lines name every file's last stage and reason | Per-file stage log; entity from name and content; duplicates / revisions / conflicts handled; per-month evidence |
| Excel tool call timed out repeatedly; the agent retried | Recalculation or link / add-in refresh exceeded the ~60 s tool limit | Real: the staged Excel diagnostic (T5) separates access, calculation, link refresh and the two time limits | Office Script v5 (probe → recalc → read); categorised failures; attestation |
| 18 active link formulas; a much longer list of linked names in metadata | Most names are stale link records | Real: onboarding's L3 finding and the stale-records line | Active / inactive / stale links; only active links block |

## One-time setup in Copilot Studio (in order)
1. **Skill:** replace `valuation-pipeline` with `valuation-pipeline.zip` (build 11.3), uploaded as downloaded (do not unzip and re-zip).
2. **Instructions:** replace everything with `agent-instructions.txt` (11.3).
3. **Office Script:** in SharePoint, replace `recalc-and-read` with `recalc-and-read.ts` (v5). Same name and `cells` parameter, so the tool needs no change. It still accepts the v4 cell list. If the script editor underlines `getLinkedWorkbooks` or `refreshLinks`, delete the block between `// LINKS BLOCK` and `// END LINKS BLOCK` and save. I type-checked it against a stub and ran it on a mock workbook, but could not check it against the real Office Scripts library.
4. **Knowledge descriptions:** unchanged from 11.2.
5. **Publishing:** still blocked by the data-policy conflict (admin). Test in the Preview pane meanwhile.

## Tests in the agent (each in a new conversation, in this order)
| # | Say | Correct when | Send back |
|---|---|---|---|
| T1 | "Run the pipeline self-test." then "What version is the pipeline?" | `ALL SELFTESTS: PASS (76/76)`, `VERSION: valuation-pipeline 11.3.0` | the full output (synthetic only) |
| T2 | "Find the files for <company> for Q1 2026 – gather only." | `THEN:` ends with `--period-end 2026-03-31`; every statement-like file has a `HAVE:` or an `EVIDENCE:` line saying why it is not used | only counts: how many `HAVE: statement` and `EVIDENCE:` lines, and the reasons' wording with names removed |
| T3 | "Onboard <company> for Q1 2026." | `PERIODS: requested 2026-03`; LP FIELDS in the Q1 2026 column (spot-check 3 cells in Excel yourself); `EVIDENCE: statements` shows each file reconciled or a reason; `VERIFICATION:` line; `EXCEPTIONS:` each with options | nothing from the report; only the `PERIODS:` and `VERIFICATION:` first lines and the `EXCEPTIONS:` count, if they contain no names |
| T3b | (same) "approve as <name>" with no decisions | `APPROVAL REFUSED:` listing each exception; nothing saved | yes / no |
| T3c | (same) "approve as <name>; A-xxxx intentional lag – <reason>; …" | `APPROVED: … n exception decision(s) recorded` | yes / no |
| T4 | Run the Office Script by hand on an original (no `__copy` in its name) | `"guard": "refused"`, `"version": 5` | the script result (no data in it) |
| T5 | "Onboard <company> for Q1 2026 with the Excel diagnostic." | three RECALC stages run once each; the `VERIFICATION:` line names the stage and cause if it fails | the `VERIFICATION:` line only |
| T6 | Fill the answer key (below), upload it, say "Verify OB-01." | `VERIFY:` lines and a RESULT line | **the `VERIFY:` lines only** |

Never send back the onboarding report, cell references, sheet names, file names or values. The `VERIFY:` lines are built from a fixed vocabulary; anything else is printed as `withheld`.

## The answer key (WP8)
Template: `references/answer_key_template.json` (in the skill). An analyst copies it, fills in the company, the
quarter-end date, the four output cells of the approved workbook (enterprise value, adjusted EBITDA, the selected
multiple, value to XPV), the TTM window, method, number of entities and the statement months. Keep it in a private
SharePoint folder; upload it only into the agent conversation for T6. Proposed owner: the analyst who approved that
quarter (open question 1).

## Running day to day
| You want | Say | You provide |
|---|---|---|
| Set up a company | "Onboard <company> for <quarter>." | nothing, unless the agent asks for a file |
| Approve | "approve as <name>" + one decision per exception with a reason | — |
| Correct a cell | "EV is Valuation!C21" | — (the agent re-runs with `--cells`) |
| Say which entity a blocked statement is | "<file> is Entity B" | — (re-run with `--entities`) |
| Record a desktop Excel recalculation | "I recalculated it in Excel; EV, equity and value to XPV match" | what you refreshed and what did not refresh |
| Verify against the answer key | "Verify <test id>." | the answer key file |
| Add files / facts / ask where a number comes from / how others did it | as in 11.2 | — |

## Exception decisions (what each option means)
| Option | Means | Approval |
|---|---|---|
| `intentional_lag`, `fiscal_year_basis` | the period difference is the company's convention (recorded for that role and field only) | goes ahead |
| `accepted` | a reviewed workbook issue that does not make the LP number wrong | goes ahead |
| `restore_formula` | a typed number should be a formula again (applied by the refresh, after approval) | goes ahead |
| `carry_values` | values read from a linked workbook are carried as saved | goes ahead |
| `exclude_file` | a blocked statement is not used | goes ahead |
| `accept_python_checks_only` | Excel did not verify; Python's checks are accepted for now | goes ahead |
| `wrong_cells_selected`, `workbook_defect`, `provide_linked_workbook`, `rerun_with_entity`, `attest_first` | something must be fixed first | refused, with the next step |

`small_lag_needs_decision` (materiality defaults, currently `true`): set it to `false` by a named decision if 1–3 month
TTM lags should be information only.

## Troubleshooting
| You see | Do |
|---|---|
| `PERIODS: no requested valuation date` | onboarding was run without gather's command: run gather and its THEN line |
| `PERIODS:` exceptions (`wrong_period`) | the workbook's cells are for another quarter: check the request; if the cells are wrong, name the right ones; if it is the company's convention, decide `intentional_lag` / `fiscal_year_basis` |
| `EVIDENCE:` a file `blocked` | ambiguous entity or conflicting files: say which entity it is, or exclude it |
| `EVIDENCE: … carried from approved baseline` high | statements for those months were not given: allowed, and labelled; add them for full evidence |
| `VERIFICATION: not verified … tool time limit` | Excel Online could not recalculate in ~60 s: recalculate in desktop Excel and attest, or accept Python checks only |
| `VERIFICATION: … access` | Excel connection or file Id: Set up connection, then onboard again |
| `APPROVAL REFUSED` | give one decision per listed exception, or do the fix it names |
| anything else | as in the 11.2 guide |

## Not in 11.3
Quarterly generation (refresh), backtest build, close, other companies, publishing. **No production-readiness claim**
until T1 and a T6 verify run both pass.

## Open questions (structural only)
1. Approve the answer-key fields and who fills them.
2. Quarters as side-by-side columns or separate sheets? An LP Report sheet in every workbook? (11.3 handles both; the answer decides which layouts to add to the fixtures.)
3. Statements: one file per entity per month? Where does the entity name appear inside them? (11.3 reads rows 1–3 of the first sheet; a different place causes false `ambiguous entity` blocks.)
4. Is desktop recalculation attestation acceptable evidence for complex workbooks? (built as an explicit option; your call whether to allow it)
5. Data-policy block: remove `sharepoint_get_doc` first, then bisect (admin).
6. Keep `small_lag_needs_decision = true`?
