// recalc-and-read (Office Script for Excel on the web) - used by the valuation agent's RECALC step.
// 1) Fully recalculates the workbook (Excel on the web saves the result).
// 2) Returns one line of JSON: {"values": {cell: value}, "errors": ["Sheet!A1=#REF!", ...]}  (errors capped at 500)
// Parameter cells: a JSON list of "Sheet!A1" references, e.g. ["Sheet!A2", "Valuation Summary!F25"].
function main(workbook: ExcelScript.Workbook, cells: string = "[]"): string {
  let wanted: string[] = [];
  try {
    wanted = JSON.parse(cells) as string[];
  } catch (e) {
    return JSON.stringify({ error: "cells must be a JSON list such as [\"Sheet!A1\"]" });
  }
  workbook.getApplication().calculate(ExcelScript.CalculationType.full);

  const values: { [ref: string]: string | number | boolean } = {};
  for (const ref of wanted) {
    const cut = ref.lastIndexOf("!");
    const sheet = workbook.getWorksheet(ref.slice(0, cut).replace(/^'+|'+$/g, ""));
    values[ref] = sheet ? (sheet.getRange(ref.slice(cut + 1)).getValue() as string | number | boolean) : "#NO_SHEET";
  }

  const ERR = ["#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?", "#NUM!", "#NULL!", "#SPILL!", "#CALC!"];
  const errors: string[] = [];
  for (const ws of workbook.getWorksheets()) {
    const used = ws.getUsedRange(true);
    if (!used) {
      continue;
    }
    const v = used.getValues();
    const r0 = used.getRowIndex();
    const c0 = used.getColumnIndex();
    for (let r = 0; r < v.length && errors.length < 500; r++) {
      for (let c = 0; c < v[r].length && errors.length < 500; c++) {
        const x = v[r][c];
        if (typeof x === "string" && ERR.indexOf(x) >= 0) {
          errors.push(ws.getName() + "!" + columnName(c0 + c) + (r0 + r + 1) + "=" + x);
        }
      }
    }
  }
  return JSON.stringify({ values: values, errors: errors });
}

function columnName(index: number): string {
  let s = "";
  let n = index + 1;
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}
