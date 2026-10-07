# XPV valuation agent – build 11.2: setup, tests and running

This guide replaces earlier deployment notes. The design reference is `valuation-build-plan-v11.1.md (design reference)`.

## Glossary
| Term | Meaning |
|---|---|
| Limited partner (LP) report | XPV's quarterly investor report; the pipeline works back from each company's LP numbers |
| Enterprise value (EV) | Selected multiple × metric (or a weighted blend), before debt and cash |
| Trailing twelve months (TTM) | Sum of the last 12 monthly values ending at the valuation month |
| Mapping | Onboarding step that works out how the approved workbook turns statements into the LP numbers |
| Build map | The parts the LP numbers depend on (entities, adjustments, pro forma, valuation, cap table…), in build order, each input with its next-quarter source |
| Liveness checks (L1–L5) | Proof the workbook is live: formulas not typed numbers, no pasted calculations, no external links / manual calculation / errors, Excel recalculation of a copy matches (L4), Python's checks match Excel |
| Company file | `Valuations/<company>/company/<company>_company.zip`: the company's map, facts, evidence and approvals |
| Self-test | 51 automatic tests on synthetic files, run inside the agent |

## What build 11.1 does
- **Onboarding** from one sentence ("Onboard Company B for Q2 2026"): the agent finds the files in knowledge, picks the
  right ones, maps the workbook, checks it, has Excel recalculate a copy, and asks for one named approval.
- **Analyst information:** files (filed in SharePoint), stated facts (recorded word for word in the company file).
- **Questions:** status, where a number comes from, how other companies structure something.
- **Not yet (next build):** backtest build, quarterly generation (refresh), close.
- **New in 11.2:** workbooks Excel Online cannot recalculate in time (data-provider add-ins, links to other
  workbooks, very large files) skip the Excel step – onboarding finishes in one step with `L4 SKIPPED`, relying on
  Python's checks (L5). The agent runs the Office Script at most once and never retries.
- **Removed in 11.1:** the portfolio register (and its link). SharePoint and knowledge are the record of files; the
  census is only an occasional portfolio overview.

## One-time setup in Copilot Studio (in order)
1. **Skills:** replace `valuation-pipeline` with `valuation-pipeline.zip` (build 11.2), uploaded as downloaded – do not
   unzip and re-zip. Keep `valuation-generate` as it is.
2. **Instructions:** replace everything with `agent-instructions.txt` (the register link line is gone).
3. **Knowledge descriptions** (they decide which source the agent searches):
   - *Valuation Workbooks:* "Quarterly valuation workbooks for each portfolio company (approved and draft), named by quarter and company. Used to fetch a company's workbook for a quarter."
   - *Company Financial Statements:* "Monthly financial statements (income statement, balance sheet) for each portfolio company and its entities, one file per month. Used to fetch statements by company, entity and month."
   - *Monthly Summaries:* "XPV's monthly summary workbooks for each portfolio company, often linked from valuation workbooks. Used to fetch a company's monthly summary for a period."
   - *LP_reports:* "XPV's quarterly LP reports. Used only to fetch the report for a quarter; not for answering valuation questions."
4. **Office Script:** in SharePoint, replace the contents of `recalc-and-read` with `recalc-and-read.ts` (v4). Same name,
   same `cells` parameter, so the tool needs no change.
5. **Tools present:** SharePoint *Create file*, *Create new folder*, *List folder*; Excel Online *Run script from SharePoint
   library*. Web search off. `sharepoint_get_doc` is optional (pasted links only) – remove it if it causes the data
   policy conflict.
6. **Publish** (if a data policy blocks publishing, test in the Preview pane meanwhile).
7. **Optional clean-up:** `Valuations/_portfolio` (the old register) is no longer used.

## Tests (each in a new conversation, in this order)
| # | Say | Correct when | Send back if not |
|---|---|---|---|
| T1 | "Run the pipeline self-test." then "What version is the pipeline?" | `ALL SELFTESTS: PASS (51/51)` and `VERSION: valuation-pipeline 11.2.0` | the full output |
| T2 | "Find the files for Company B for Q2 2026 – gather only, don't onboard." | `GATHER:` names the approved Q2 workbook (not a draft) and the Q1 workbook; statements for each month, or `NEED:` lines with exact searches; a `THEN:` onboarding command. Note the line `GATHER: looked in …; files found in …` | the GATHER / HAVE / NEED lines |
| T3 | "Onboard Company B for Q2 2026." | `LP FIELDS`: EV, equity value and value to XPV `[verified]`; `LIVENESS` L1–L3 pass or real findings, L4 PASS under 90 s or `SKIPPED` (add-ins / linked workbooks / very large file); `LINE MAP` matched; `BUILD` lists every part you expect and `TRACE` reaches each entity; `REVIEW` short; `READINESS: ONBOARDED_PENDING_APPROVAL`. Spot-check three numbers in Excel | the report from ONBOARD to READINESS |
| T3b | (same conversation) "approve as <your name>" | `APPROVED:` and `READINESS: ONBOARDED`; the company file saved in SharePoint | the output |
| T4 | Run the Office Script by hand on an original workbook (no `__copy` in its name) | it returns `"guard": "refused"` | the script result |
| T5 | (after T3) "Company B bought Gamma; Gamma's TTM EBITDA is 2.1m." | `INTAKE: fact F-001 …` recorded word for word | the output |
| T6 | "How have other companies structured acquisitions?" | the agent searches Valuation Workbooks, then `REFERENCE:` lines (structure only, no numbers) | the output |

## Running day to day
| You want | Say | You provide |
|---|---|---|
| Set up a company | "Onboard <company> for <quarter>." | nothing, unless the agent asks for a file it could not find |
| Approve | "approve as <your name>" (+ corrections in plain words) | — |
| Add files | "Here are <company>'s <quarter> statements." | the files or links |
| Record a fact | "<company> bought Gamma; Gamma's TTM EBITDA is 2.1m." | — |
| What's on file | "What do we have for <company>?" | — |
| Where a number comes from | "Explain the enterprise value for <company>." | — |
| How others did it | "How have other companies structured <acquisitions / pro forma / waterfalls>?" | — |
| Portfolio overview (occasional) | "Run a census on <workbooks>." | — |

**The analyst's part:** name the company and quarter, supply any file the agent could not find, read the REVIEW items,
approve by name. One company per conversation; approve in the onboarding conversation.

## Troubleshooting
| You see | Do |
|---|---|
| gather finds no workbook | check the file is in the Valuation Workbooks source and indexed; its name should contain the company and quarter; or paste its SharePoint link |
| gather picked a draft | say "use the approved workbook" and paste its link, or confirm the draft is the only version |
| `NEED: statements for <month>` after two rounds | upload or link those statements |
| `L4 NOT RUN` / Run script failed | Excel connection: select Set up connection, Retry; onboarding can still be approved |
| Run script timed out or the agent keeps retrying | reset the conversation (new-conversation button at the top of the Preview pane, or close it) to stop; build 11.2 skips the Excel step for such workbooks and forbids retries |
| `L4 FAIL` | the saved values were stale: open the original in Excel, recalculate, save, onboard again |
| a period question (e.g. "calendar year 2024 for Q1 2026") | answer it: is this the company's convention, or should the window be rolled? |
| `no_saved_values` finding | the file was saved by a tool that does not calculate: open and save it in Excel |
| `integrity` STOP | use the company file saved in SharePoint; never edit the zip |
| `NOT ANALYSED (killed …)` | the file is very large: send me the READING line |
| any FAIL or PIPELINE ERROR | paste the full output here |

## What's next (build 12)
Backtest build, quarterly generation (refresh) and close. To design them against real data, run T2 and T3 on one
company that has a pro forma sheet and send back the GATHER, BUILD, TRACE, LEARNED and HAVE / NEED lines.
