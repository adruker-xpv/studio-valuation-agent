# Test2 as a regression case (build 13.0)

Test2 is the run where the build 12.0 extractor understood five real workbooks and still timed out before saving anything. It is now
the regression case for build 13.0: the same five workbooks, rerun inside the authorized environment, must produce saved, checkable
results. Only the sanitized diagnostics at the end leave that environment - no values, names, file paths, cell contents or reasoning.

## Legend
| Term | Meaning |
|---|---|
| Authorized environment | Copilot Studio and SharePoint, where the confidential workbooks are allowed |
| Pass A / pass B / RESUME | The extractor's stages 1-3 / stage 4 to the end / continuing after an interruption |
| Checkpoint | A saved stage file in the run folder's `checkpoints/` |
| verify | The deterministic claim checker; its status is VERIFIED, SUPPORTED, PROVISIONAL or REVIEW |
| Sanitized | Counts, statuses, durations and yes/no answers only |

## Keep the evidence of the failure
Leave `Onboarding/OceanSight-test2` exactly as it is (the 12.0 trace, the partial outputs and the timeout record). Run build 13.0 in a new
folder, for example `Onboarding/OceanSight-test3`, with the same five workbooks, using `MANUAL_RUN_PROMPTS.md`.

## Pass criteria
| # | Check | Pass |
|---|---|---|
| 1 | Every workbook's READ line appears, with the same fingerprints in every pass | yes |
| 2 | The inventory call finishes (no STOPPED left unresolved), including any INFLATED sheet | yes |
| 3 | Pass A saves stage 3 and ends with `"next_stage": 4` | yes, without a timeout |
| 4 | `extraction.json` exists in the run folder after pass A | yes |
| 5 | Pass B reaches stage 7 | in at most 2 sittings (pass B plus at most one RESUME) |
| 6 | No home-made workbook reader: no script in the transcript or `evidence/` opens the .xlsx as zip or XML itself | none |
| 7 | Primary result size: `extraction.json` | under 150 KB (stage caps make this automatic) |
| 8 | verify `--final` ran | status recorded in `checkpoints/07_validation.json` |
| 9 | Any value the fund reports differently from the company workbook is a recorded discrepancy, not forced to agree | yes, if one exists |
| 10 | Reviewer phase 1 is bottom-up and saved; `reviewer_blind.json` under 45 KB | yes |
| 11 | Reconcile's REVIEWER VALUE line is something other than "NO INDEPENDENT VALUE SHOWN" | report what it says |
| 12 | Privately, the analyst compares the 13.0 core chain with what the 12.0 trace had found | same chain, or a reason |

## Sanitized diagnostics to bring back (copy this form)
```
Build: 13.0.0    Extractor model:            Reviewer model:
Workbooks supplied: 5    Workbooks with formulas:     INFLATED sheets reported:    Linked files not supplied (X ids):
Pass A: minutes        timeouts:     stages saved:          verify after stage 3:
Pass B: minutes        timeouts:     RESUMEs needed:        stages saved:
Reader calls per stage (count from the transcript): 2:   3:   4:   5:   6:
Home-made workbook parsing seen: yes / no
verify --final: status            edges confirmed:     contradicted:     judgment (not checkable):
Discrepancies recorded:     unresolved:          Open questions:
extraction.json size (KB):        reviewer_blind.json size (KB):        review.json size (KB):
Reviewer phase 1: minutes   timeouts:   direction recorded:
Reconcile: status                  key answers agreed:   /9      REVIEWER VALUE:
   missed rivals:   weak provenance:   unsupported assumptions:   evidence-backed contradictions:   reviewer claims contradicted:
Core chain same as the 12.0 trace (analyst, privately): yes / no / partly
Tool errors (message type only, no contents):
```
Bring back only this form. If something needs a closer look, describe its shape ("a stage-4 save was refused for size") rather than its
contents.
