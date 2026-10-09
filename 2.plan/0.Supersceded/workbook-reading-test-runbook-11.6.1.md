# Testing the program on real workbooks – step-by-step runbook (build 11.6.1)

## Words used here
| Word | Meaning |
|---|---|
| The program | The code that reads a valuation workbook and works out what is in it and what it means |
| The agent | Your Copilot Studio agent, which runs the program when you type the sentences below |
| Export copy | A copy of the workbook in which Excel itself writes down every cell, so the program can be checked against Excel |
| Answer form | A short Excel form where the analyst writes down the key numbers' locations and what areas of the workbook are |
| Fingerprint | A code calculated from a file's contents; if the file changes at all, the code changes |
| Result lines | The lines starting with `BENCHMARK:` – counts and pass/fail only, no numbers or names from the workbook |

## What you will have at the end
For each workbook tested: whether the program reads the file **exactly as Excel does** (every cell), and whether it
understands **what the key numbers are and which areas matter**, compared with an analyst. Each new build repeats the same
checks, so you can see whether it got better or worse.

## Before you start (once, about 20 minutes)
1. **The skill:** in Copilot Studio, open the agent you use for this test, go to its skills and replace `workbook-discovery`
   with the new `workbook-discovery.zip` (upload it exactly as downloaded – do not unzip it).
2. **The instructions:** replace the agent's instructions with everything in `agent-instructions-discovery.txt`.
3. **The Excel script:** open any workbook in Excel for the web → **Automate** tab → **New script** → delete everything in
   the editor → paste the whole of `excel-export.ts` → rename the script **excel-export** → **Save**. You only do this once;
   the script then appears under Automate in every workbook.

---

## Milestone 1 – the tool works in your environment (5 minutes)
**Type:** `Run the discovery tests.`
**You should see:** `ALL TESTS: PASS (40/40)`.
**If not:** send me the last 10 lines. Stop here until it passes.

## Milestone 2 – see what the results look like (2 minutes)
**Type:** `Run the demo.`
**You should see:** lines starting `DEMO:` – the demo makes up a workbook, shows the form check catching a typical mistake
(a label cell given instead of the number), and ends with result lines that all say `PASS`.
**Then:** download `comparison.xlsx` when the agent offers it and open it. That is exactly what your real reports will look
like: a **Summary** tab in plain sentences, then **Cell differences**, **Formula uses**, **Key numbers** and **Areas** tabs.

## Milestone 3 – a first look at a real workbook (10 minutes, no analyst)
Pick one approved valuation workbook – start with the simplest you have.
**Type:** `Run the program on <workbook file name> for quarter end 2026-03-31.` (use that workbook's own quarter end)
**You should see:** a line `PREFLIGHT: OK …` (the file can be read), then lines starting `DISCOVERY:`.
- If you see `PREFLIGHT: REFUSED …`, do what it says (for example "save it as .xlsx" or "remove the password").
**Then:** download `program_answers.xlsx` and open it. Its **1 Key numbers** tab shows which cells the program thinks hold
the enterprise value, equity value, XPV's value, the earnings figure and the multiple. Open the workbook and look: does it
seem right?
**Important:** do **not** show `program_answers.xlsx` to the analyst who will fill in the form for this workbook.
**Send me:** the `DISCOVERY:` lines.

## Milestone 4 – does the program read the file exactly like Excel? (20–40 minutes, no analyst)
1. **Make the export copy.** In SharePoint, next to the workbook: **…** → **Copy to** → the same folder. Rename the copy so its
   name **contains the word "export"**, e.g. `Delta Q1 2026 valuation - export.xlsx`. (The script refuses to run on any
   file without "export" in its name, so the original can never be touched.)
2. **Run the script on the copy.** Open the copy in Excel for the web → **Automate** → **excel-export** → **Run**. Wait.
   - If the output says **"Run again"**, press **Run** again. Repeat until it says **"Finished"**. (Big workbooks need several
     runs; each one carries on where the last stopped.)
3. **Quick check (1 minute):** the copy now has three new sheets at the end – **XLX Info**, **XLX Cells**, **XLX Uses**.
   On **XLX Cells**, column C should show formulas as text, like `=B4-B5`. If column C shows numbers instead of formulas,
   stop and tell me.
4. **Compare.** Upload the copy to the agent (or say where it is). **Type:**
   `Compare <workbook file name> with the Excel export <copy file name>.`
   (If the agent says there are no program results in this conversation, first repeat milestone 3's sentence – it takes a
   few minutes – then compare again.)
**You should see:** result lines including
`BENCHMARK: file contents vs Excel | cells match … of …` and `BENCHMARK: formula uses vs Excel | …`.
**Then:** download `comparison.xlsx`; the **Cell differences** tab lists every cell that differs, with Excel's version and the
program's side by side.
**Send me:** the `BENCHMARK:` lines.
**Stop or go:** if fewer than about 99% of cells match, send me the lines and wait – there is no point involving the analyst
until the program reads the file correctly.

## Milestone 5 – does the program understand the workbook? (analyst 20–30 minutes, you 15 minutes)
1. **Type:** `Make the answer form for <workbook file name>, quarter end 2026-03-31.` Download the form.
2. **Send the analyst** the form and the workbook – nothing else. The email text is at the end of this runbook.
3. **When the form comes back:** upload it. **Type:** `Check the answer form <form file name> against <workbook file name>.`
   - `FORM: OK` → go to step 4.
   - Otherwise it lists what to fix, in plain words – for example *"Valuation!A11 holds the text 'Enterprise value', not a
     number. The first number to its right is in B11 – is that the one?"* Ask the analyst (or fix obvious typos together),
     upload the corrected form, and check again.
4. **Type:** `Save the answers by <analyst's name>.` Download and keep the `analyst answers - … .json` file.
5. **Type:** `Compare <workbook file name> with the answers <answers file name> and the Excel export <copy file name>.`
**You should see:** additional result lines –
`BENCHMARK: key numbers vs analyst | correct … of 5 …`, `BENCHMARK: areas vs analyst | …` and
`BENCHMARK: confidently wrong | …` (this one must be **0**: it counts answers the program was sure about and got wrong).
**Then:** in `comparison.xlsx`, the **Key numbers** tab shows the analyst's cell and the program's cell side by side.
**Send me:** the `BENCHMARK:` lines. **Keep:** `result.json` (for the next build's comparison).

## Milestone 6 – does it work beyond one workbook? (about 1 hour per workbook, including the analyst)
Repeat milestones 3–5 for 2–4 more workbooks that are **built differently** (one with an acquisition or pro forma, one with
a cap table or waterfall, one that reads other workbooks, one using a different method). Keep **one** of them aside: run it
only when I say a build is finished, so we see how the program does on a workbook it was never tuned on.

## Every new build after that (about 10 minutes per workbook, no analyst)
Replace the skill zip, then: `Run the discovery tests.` → for each workbook: run the program (milestone 3's sentence), then
`Compare <workbook> with the answers <answers file> and the Excel export <copy> and the previous result <result.json>.`
**You should see:** `BENCHMARK: since last comparison | better … | worse …`. A build is only better if **worse is 0**.

---

## What goes where on the answer form
**Always give the cell that holds the NUMBER – never the cell with its name.**

| On the workbook you see | Write | Not |
|---|---|---|
| A4 says "Adjusted EBITDA", B4 says 2,754,000 | Sheet `Valuation`, Cell `B4` | `A4` |
| The sheet tab is called "Valuation Summary" | `Valuation Summary` (exactly as on the tab) | `Valuation`, `valuation sheet` |
| The earnings figure covers April 2025 to March 2026 | First month `2025-04`, Last month `2026-03` | `April 2025`, `Q1` |
| Column F of the valuation sheet is the March 2026 quarter | Areas: Sheet `Valuation Summary`, Cells `F5:F40`, What it is `Current quarter's valuation`, Month `2026-03` | – |
| Columns B to M of the monthly sheet are 2024 | Areas: Sheet `Monthly`, Cells `B5:M40`, What it is `Old history` | – |
| A whole sheet is a scratch area | Areas: Sheet `Workings`, Cells *(leave empty)*, What it is `Scratch or working area` | – |
| You are not sure | leave it empty, or choose `Not sure` | a guess |

## What the result lines mean
| Line | Good looks like |
|---|---|
| file contents vs Excel | cells match all (or all but a handful, each explained in the Cell differences tab) |
| formula uses vs Excel | missed silently 0 (a reference the program missed without warning is the worst case) |
| key numbers vs analyst | correct 5 of 5; "not decided" is acceptable, "wrong" is not |
| areas vs analyst | handled correctly all; cell months wrong 0 |
| confidently wrong | **0** – the program was sure and the analyst disagrees |
| still open in the program | things the program itself says it could not settle; they should shrink over builds |
| since last comparison | worse 0 |

## If something goes wrong
| You see | Do |
|---|---|
| `PREFLIGHT: REFUSED …` | do what the line says (save as .xlsx, remove the password, fetch the file again) |
| `STOPPED: … no program results for this workbook in this conversation` | run the program on the workbook (milestone 3's sentence), then compare again |
| `STOPPED: the Excel export has not finished` | open the export copy, run excel-export again until it says Finished |
| `STOPPED: … different sheets` | the export copy is of another workbook: make a fresh copy of the right one |
| `STOPPED: … different version of the workbook` | the workbook changed after the form was made: make a new form for the current file |
| `STOPPED: … edited after it was saved` | use the answers file exactly as `save-answers` wrote it |
| The script says "Stopped: run this only on a COPY…" | rename the copy so its name contains "export" |
| `DISCOVERY ERROR:` / `BENCHMARK ERROR:` | a bug: send me that line |

## What to send me
Only lines starting with `DISCOVERY:` or `BENCHMARK:`. Never the workbook, the forms, `program_answers.xlsx`,
`comparison.xlsx`, the CSV files or `result.json` – they contain the workbook's content.

## Email text for the analyst
> Hi <name> – could you fill in the attached answer form for <workbook>? It takes about 20–30 minutes and uses only the
> workbook itself.
> - **Tab "1 Key numbers":** for each item, the sheet and the cell that holds the NUMBER (for example B4 – not A4 where its
>   name is), the first and last month the earnings figure covers (like 2025-04 and 2026-03), and the valuation method.
> - **Tab "2 Areas":** one row per part of the workbook you know about – which column or range is the current quarter (and
>   its month), which parts are old history, scratch work or presentation pages. Leave "Cells" empty for a whole sheet.
> - If you are not sure about something, leave it empty – please don't guess.
> Thanks!
