# XPV Valuation Automation — Quarterly Process Flow (for Jerome to confirm)

*Draft, October 16, 2026. This is today's manual process for one company in one quarter, pieced together from AJ's notes.*

**Jerome, could you please:**

- Fix any step that is wrong, missing or in the wrong order.
- Fill in the times marked "?". A rough range is fine.

The last column shows what the automated build plans to do with each step.

---

## Legend

| Term | Meaning |
|---|---|
| Monthly summary | The analyst's summary of each month's company financials |
| Valuation workbook | The company's workbook that calculates its value |
| Fund valuation workbook | The workbook that turns company values into the fund's value |
| Adjusted earnings (Adjusted EBITDA) | Earnings after approved one-off adjustments; most companies are valued as a multiple of this |
| Pro-forma financials | The sheet that restates earnings as if an acquired business had been owned for 12 months |
| Comparables | Similar public companies used to set the multiple |
| Ownership table (cap table) | Who owns what share of the company |
| Build: **Does it** | The system does the step and the analyst approves it |
| Build: **Asks** | The system asks the analyst and never decides |
| Build: **Later** | Planned for after December 18 (Phases A, B and C) |
| Build: **No** | Stays manual |

---

## The flow

| # | Step | Who | Time today | Build |
|---|---|---|---|---|
| **Each month** | | | | |
| 1 | Company sends its monthly financials | Company CFO | — | No |
| 2 | Populate the monthly summary | AJ | ~5 min a month | No |
| **After quarter end** | | | | |
| 3 | Find the latest version of last quarter's workbook, including any revisions made after approval | AJ | ? | A person supplies it until "approved" folders exist. Code compares it with the approved fingerprint and lists any changes |
| 3a | Update past quarters if the company revised its numbers (as Opus's Q1 earnings changed in Q2) | AJ? | ? | Does it: refreshes past periods and flags changes |
| 4 | Move the new numbers from the monthly summaries into the workbook | AJ | ~5 min | Does it |
| 5 | Roll forward: relink cells to the new quarter and set the comparison period columns | AJ | 30–45 min (steps 5–8 together) | Does it |
| 6 | Update the pro-forma financials sheet (if there was an acquisition) | ? | ? | Does it if the sheet exists; asks if it's new |
| 7 | Carry forward earnings adjustments; add or remove any that changed | AJ | (in 5) | Does it for carried items; asks about changes |
| 8 | Update the ownership table | AJ | (in 5) | Does it if unchanged; asks about changes |
| 9 | Update debt and cash | AJ? | ? | Does it |
| 10 | Refresh the comparable multiples from PitchBook | Jerome | ? | Later (Phase B) |
| 11 | Review whether the comparable set is still relevant | Jerome | ? | Asks; Later (Phase B suggestions) |
| 12 | Choose the multiple | ? | ? | Asks (always) |
| 13 | Check and try out the workbook | AJ | ? | Does it |
| 14 | Write the summary explaining what changed, with footnotes | AJ | ? | Later (Phase C) |
| 15 | Update the fund valuation workbook from the new company value | ? | ? | Does it |
| 16 | Review by AJ and Sean (mostly catches hidden rows that should show, and footnote numbers out of order) | AJ, Sean | — | Code checks both |
| 17 | Apply fixes after review | AJ | ~30 min | Mostly removed by code checks |
| 18 | Deal leads meet the company CFO to review adjustments (where needed) | Deal leads | ? | No |
| 19 | Prepare the approval package, with forecasts for the rest of the year | AJ | ~1 h | Later (Phase C) |
| 20 | Approval meeting | Team | ~1 h | No |
| 21 | Apply post-meeting changes in both the valuation and fund workbooks, and recirculate values for final approval by email | AJ | ~30 min | Partly (code re-types changes and checks both files agree) |
| 22 | Update the investor fund workbooks (fund overview plus a breakdown per company) and the investor report | ? | ? | Later (Phase C) |

---

## Questions for Jerome

1. Is any step missing or in the wrong order? In particular, steps 3a, 6, 9, 14, 15 and 22.
2. How long does refreshing comparable multiples from PitchBook take per company per quarter? In what format do the numbers come out, and who has access?
3. How often does the comparable set itself change: about how many companies a year?
4. When there is an acquisition, how is the pro-forma financials sheet built? Where do the acquired business's numbers come from, and how long does it take?
5. How often does the ownership table change (people joining or leaving)? Is it more than once a year per company?
6. Is the multiple chosen before or after the new quarter's numbers are in? Could that explain why OceanSight's fund workbook has a typed-in multiple that differs from its valuation workbook?
7. When you set up a new company's workbook, what is always the same and what is always different? Should the Opus and OceanSight structure be the standard template?
8. Who builds the investor report, and how are the investor fund workbooks updated?
